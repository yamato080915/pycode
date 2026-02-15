from addons.AddonBase import SecondarySideBar
from PySide6.QtWidgets import *
from PySide6.QtGui import QIcon, Qt, QColor, QFont, QPainter, QPen, QBrush, QPainterPath
from PySide6.QtCore import QTimer, QDir, QRect, QPoint, Signal, QFileSystemWatcher
from Git.common import get_status_icon, get_status_color, run_git
import os

# ─── スタイル定数 ─────────────────────────────────────────
_MENU_STYLE = """
	QMenu {
		background: #252526; color: #CCCCCC;
		border: 1px solid #3E3E42; padding: 4px 0;
	}
	QMenu::item { padding: 6px 24px; }
	QMenu::item:selected { background: #094771; }
	QMenu::separator { height: 1px; background: #3E3E42; margin: 4px 8px; }
"""
_TOOLBAR_STYLE = "background: #2D2D30; padding: 5px;"
_SEARCH_STYLE = """
	QLineEdit {
		background: #252526; color: #CCCCCC;
		border: 1px solid #3E3E42; border-radius: 3px; padding: 4px 8px;
	}
	QLineEdit:focus { border-color: #007ACC; }
"""


class CommitItem:
	"""コミット情報を保持するデータクラス"""
	__slots__ = ('hash', 'parents', 'message', 'author', 'date', 'refs',
				 'branch', 'color_index', 'visible')

	def __init__(self, hash, parents, message, author, date, refs):
		self.hash = hash
		self.parents = parents
		self.message = message
		self.author = author
		self.date = date
		self.refs = refs
		self.branch = 0
		self.color_index = 0
		self.visible = True


class CompactGraphWidget(QWidget):
	"""Gitグラフを描画するウィジェット"""
	commitSelected = Signal(CommitItem)
	fileClicked = Signal(str, str, CommitItem)

	# カラーパレット
	COLORS = [
		QColor("#66D9EF"), QColor("#A6E22E"), QColor("#F92672"),
		QColor("#FD971F"), QColor("#AE81FF"), QColor("#E6DB74"),
		QColor("#56B6C2"), QColor("#C678DD"),
	]

	def __init__(self, parent=None):
		super().__init__(parent)
		self.all_commits = []
		self.commits = []       # フィルタ後の表示用
		self.row_height = 32
		self.branch_width = 20
		self.node_size = 6
		self.current_branch_head = None

		self.detail_height = 0
		self.selected_index = -1
		self.selected_commit_files = []
		self.file_rects = []
		self.selected = None
		self.hover_commit = None

		self.branch_map = {}
		self.setMinimumHeight(50)
		self.setMouseTracking(True)

	# ─── データ設定 ───────────────────────────────────────
	def setCommits(self, commits, current_head=None):
		self.all_commits = commits
		self.commits = [c for c in commits if c.visible]
		self.current_branch_head = current_head
		self._resetSelection()
		self._calculateBranches()
		self._updateHeight()
		self.update()

	def filterByText(self, text):
		"""テキストでフィルタ"""
		text = text.lower()
		for c in self.all_commits:
			if not text:
				c.visible = True
			else:
				c.visible = (
					text in c.message.lower()
					or text in c.author.lower()
					or text in c.hash[:10].lower()
					or any(text in r.lower() for r in c.refs)
				)
		self.commits = [c for c in self.all_commits if c.visible]
		self._resetSelection()
		self._calculateBranches()
		self._updateHeight()
		self.update()

	def _resetSelection(self):
		self.selected = None
		self.selected_index = -1
		self.detail_height = 0
		self.selected_commit_files = []
		self.file_rects = []

	# ─── レイアウト計算 ───────────────────────────────────
	def _updateHeight(self):
		total = len(self.commits) * self.row_height + 30
		if self.selected_index >= 0:
			total += self.detail_height
		self.setFixedHeight(max(total, 50))

	def _calculateBranches(self):
		"""ブランチレーンを安定的に計算"""
		self.branch_map.clear()
		active_lanes = []  # 各レーンが接続中のハッシュ (None = 空き)
		next_branch = 0

		for commit in self.commits:
			# このコミットに割り当て済みのレーンを探す
			lane = -1
			for i, target in enumerate(active_lanes):
				if target == commit.hash:
					lane = i
					active_lanes[i] = None
					break

			if lane < 0:
				# 空きレーンを探すか新規作成
				for i, target in enumerate(active_lanes):
					if target is None:
						lane = i
						break
				if lane < 0:
					lane = len(active_lanes)
					active_lanes.append(None)

			commit.branch = lane
			commit.color_index = lane % len(self.COLORS)

			# 親コミットにレーンを予約
			for j, parent_hash in enumerate(commit.parents):
				already = False
				for i, target in enumerate(active_lanes):
					if target == parent_hash:
						already = True
						break
				if already:
					continue

				if j == 0:
					# 第1親は同じレーン
					active_lanes[lane] = parent_hash
				else:
					# マージ元は空きレーンか新規
					placed = False
					for i, target in enumerate(active_lanes):
						if target is None:
							active_lanes[i] = parent_hash
							placed = True
							break
					if not placed:
						active_lanes.append(parent_hash)

	# ─── 描画 ────────────────────────────────────────────
	def paintEvent(self, event):
		if not self.commits:
			return
		painter = QPainter(self)
		painter.setRenderHint(QPainter.Antialiasing)
		painter.fillRect(self.rect(), QColor("#252526"))

		# 背景 (選択 / ホバー)
		for i, commit in enumerate(self.commits):
			y = self._commitY(i)
			if commit == self.selected:
				painter.fillRect(0, y, self.width(), self.row_height, QColor("#094771"))
			elif commit == self.hover_commit:
				painter.fillRect(0, y, self.width(), self.row_height, QColor("#2A2D2E"))

		# 詳細パネル背景
		if self.selected_index >= 0 and self.detail_height > 0:
			dy = self._commitY(self.selected_index) + self.row_height
			painter.fillRect(0, dy, self.width(), self.detail_height, QColor("#1E1E1E"))
			painter.setPen(QColor("#3E3E42"))
			painter.drawRect(0, dy, self.width() - 1, self.detail_height - 1)
			self._drawDetail(painter, self.selected, dy)

		# 接続線
		commit_index = {c.hash: i for i, c in enumerate(self.commits)}
		for i, commit in enumerate(self.commits):
			for ph in commit.parents:
				if ph in commit_index:
					self._drawLine(painter, commit, self.commits[commit_index[ph]], i, commit_index[ph])

		# ノード + テキスト
		max_branch = max((c.branch for c in self.commits), default=0)
		text_x = max_branch * self.branch_width + 45
		for i, commit in enumerate(self.commits):
			self._drawCommit(painter, commit, i, text_x)

	def _commitY(self, index):
		if index <= self.selected_index or self.selected_index < 0:
			return index * self.row_height
		return index * self.row_height + self.detail_height

	def _drawLine(self, painter, commit, parent, ci, pi):
		sx = commit.branch * self.branch_width + 20
		sy = self._commitY(ci) + 15
		ex = parent.branch * self.branch_width + 20
		ey = self._commitY(pi) + 15

		color = self.COLORS[commit.color_index]
		painter.setPen(QPen(color.darker(130), 1.5))

		if commit.branch == parent.branch:
			painter.drawLine(sx, sy, ex, ey)
		else:
			path = QPainterPath()
			path.moveTo(sx, sy)
			my = (sy + ey) / 2
			path.cubicTo(sx, my, ex, my, ex, ey)
			painter.drawPath(path)

	def _drawCommit(self, painter, commit, index, text_x):
		x = commit.branch * self.branch_width + 20
		y = self._commitY(index) + 15
		color = self.COLORS[commit.color_index]
		is_head = self.current_branch_head and commit.hash == self.current_branch_head

		if is_head:
			painter.setPen(QPen(color, 2))
			painter.setBrush(QBrush(QColor("#252526")))
			painter.drawEllipse(QPoint(x, y), self.node_size + 2, self.node_size + 2)
		elif commit == self.selected:
			painter.setPen(QPen(QColor("#FFFFFF"), 2))
			painter.setBrush(QBrush(color))
			painter.drawEllipse(QPoint(x, y), self.node_size + 2, self.node_size + 2)
		elif commit == self.hover_commit:
			painter.setPen(QPen(color.lighter(150), 1.5))
			painter.setBrush(QBrush(color.lighter(120)))
			painter.drawEllipse(QPoint(x, y), self.node_size + 1, self.node_size + 1)
		else:
			painter.setPen(QPen(color.darker(120), 1))
			painter.setBrush(QBrush(color))
			painter.drawEllipse(QPoint(x, y), self.node_size, self.node_size)

		# ハッシュ
		painter.setPen(QColor("#858585"))
		painter.setFont(QFont("Consolas", 8))
		painter.drawText(text_x, y + 4, commit.hash[:7])

		# メッセージ
		painter.setPen(QColor("#CCCCCC"))
		painter.setFont(QFont("Yu Gothic UI", 9))
		avail = self.width() - text_x - 300
		max_chars = max(20, avail // 7)
		msg = commit.message[:max_chars] + "..." if len(commit.message) > max_chars else commit.message
		painter.drawText(text_x + 60, y + 4, msg)

		# refs
		if commit.refs:
			ref_x = text_x + 60 + len(msg) * 8 + 10
			for ref in commit.refs[:3]:
				# バッジ描画
				font = QFont("Yu Gothic UI", 8, QFont.Bold)
				painter.setFont(font)
				fm = painter.fontMetrics()
				tw = fm.horizontalAdvance(ref) + 12
				badge_rect = QRect(ref_x, y - 8, tw, 16)

				if ref.startswith('🏷'):
					bg = QColor("#3E3E42")
					fg = QColor("#E6DB74")
				else:
					bg = QColor("#1B3A4B")
					fg = QColor("#4EC9B0")

				painter.setPen(Qt.NoPen)
				painter.setBrush(QBrush(bg))
				painter.drawRoundedRect(badge_rect, 3, 3)
				painter.setPen(fg)
				painter.drawText(badge_rect, Qt.AlignCenter, ref)
				ref_x += tw + 4

		# 作者 + 日付 (右端)
		painter.setPen(QColor("#6A6A6A"))
		painter.setFont(QFont("Yu Gothic UI", 8))
		info = f"{commit.author}  {commit.date}"
		iw = painter.fontMetrics().horizontalAdvance(info) + 12
		painter.drawText(self.width() - iw, y + 4, info)

	def _drawDetail(self, painter, commit, y):
		if not commit:
			return
		self.file_rects.clear()
		font_mono = QFont("Consolas", 8)
		font_ui = QFont("Yu Gothic UI", 9)

		cy = y + 15
		painter.setFont(font_mono)
		painter.setPen(QColor("#569CD6"))
		painter.drawText(20, cy, f"COMMIT  {commit.hash}")
		cy += 18
		painter.setPen(QColor("#CCCCCC"))
		painter.drawText(20, cy, f"AUTHOR  {commit.author}")
		cy += 18
		painter.drawText(20, cy, f"DATE    {commit.date}")
		cy += 18

		painter.setPen(QColor("#D4D4D4"))
		painter.setFont(font_ui)
		lines = [commit.message[i:i+90] for i in range(0, len(commit.message), 90)]
		for line in lines[:3]:
			painter.drawText(20, cy, line)
			cy += 16

		if self.selected_commit_files:
			cy += 8
			painter.setPen(QColor("#4EC9B0"))
			painter.setFont(QFont("Yu Gothic UI", 9, QFont.Bold))
			painter.drawText(20, cy, f"変更ファイル ({len(self.selected_commit_files)})")
			cy += 18

			painter.setFont(font_mono)
			for fp, st in self.selected_commit_files:
				fr = QRect(30, cy - 12, self.width() - 40, 16)
				if fr.contains(self.mapFromGlobal(self.cursor().pos())):
					painter.fillRect(fr, QColor("#2A2D2E"))

				painter.setPen(QColor(get_status_color(st)))
				painter.drawText(40, cy, f"{get_status_icon(st)} {fp}")
				self.file_rects.append((fr, fp, st))
				cy += 16

	# ─── マウスイベント ───────────────────────────────────
	def mousePressEvent(self, event):
		for rect, fp, st in self.file_rects:
			if rect.contains(event.pos()):
				self.fileClicked.emit(fp, st, self.selected)
				return

		for i, commit in enumerate(self.commits):
			ys = self._commitY(i)
			if ys <= event.pos().y() < ys + self.row_height:
				if self.selected == commit and self.detail_height > 0:
					self._resetSelection()
				else:
					self.selected = commit
					self.selected_index = i
					self.detail_height = 90
					self.commitSelected.emit(commit)
				self._updateHeight()
				self.update()
				break

	def mouseMoveEvent(self, event):
		old = self.hover_commit
		self.hover_commit = None
		over_file = any(r.contains(event.pos()) for r, _, _ in self.file_rects)
		self.setCursor(Qt.PointingHandCursor if over_file else Qt.ArrowCursor)

		for i, commit in enumerate(self.commits):
			ys = self._commitY(i)
			if ys <= event.pos().y() < ys + self.row_height:
				self.hover_commit = commit
				break
		if old != self.hover_commit:
			self.update()

	def contextMenuEvent(self, event):
		for i, commit in enumerate(self.commits):
			ys = self._commitY(i)
			if ys <= event.pos().y() < ys + self.row_height:
				self._showCommitMenu(commit, event.globalPos())
				return

	def _showCommitMenu(self, commit, pos):
		menu = QMenu(self)
		menu.setStyleSheet(_MENU_STYLE)
		menu.addAction(f"ハッシュをコピー ({commit.hash[:7]})",
					   lambda: QApplication.clipboard().setText(commit.hash))
		menu.addAction("メッセージをコピー",
					   lambda: QApplication.clipboard().setText(commit.message))
		menu.addSeparator()
		menu.addAction("このコミットにチェックアウト",
					   lambda: self._checkoutCommit(commit))
		menu.addAction("このコミットからブランチ作成",
					   lambda: self._branchFromCommit(commit))
		menu.addSeparator()
		menu.addAction("Revert (打ち消し)",
					   lambda: self._revertCommit(commit))
		menu.exec_(pos)

	def _checkoutCommit(self, commit):
		reply = QMessageBox.question(
			self, 'チェックアウト', f'{commit.hash[:7]} にチェックアウトしますか？\n(detached HEAD になります)',
			QMessageBox.Yes | QMessageBox.No
		)
		if reply == QMessageBox.Yes:
			run_git(['checkout', commit.hash])

	def _branchFromCommit(self, commit):
		name, ok = QInputDialog.getText(self, '新ブランチ', f'{commit.hash[:7]} からブランチを作成:')
		if ok and name:
			run_git(['checkout', '-b', name, commit.hash])

	def _revertCommit(self, commit):
		reply = QMessageBox.warning(
			self, 'Revert', f'{commit.hash[:7]} を打ち消しますか？',
			QMessageBox.Yes | QMessageBox.No, QMessageBox.No
		)
		if reply == QMessageBox.Yes:
			run_git(['revert', '--no-edit', commit.hash])

	def setCommitFiles(self, files):
		self.selected_commit_files = files
		if self.selected_index >= 0:
			base = 145
			fh = len(files) * 16
			self.detail_height = base + fh
			self._updateHeight()
		self.update()


class Main(SecondarySideBar):
	"""Git履歴グラフパネル"""
	def __init__(self, window=None):
		super().__init__()
		self.name = "GitGraph"
		self.description = "Compact Git History Graph"
		self.version = "2.0.0"
		self.win = window

		self.icon_color(f"{window.DIR}/assets/gitgraph.svg")
		self.icon = QIcon(f"{window.DIR}/assets/gitgraph.svg")

		self._loaded = False

		layout = QVBoxLayout()
		layout.setContentsMargins(0, 0, 0, 0)
		layout.setSpacing(0)

		# ═══ ツールバー ═══
		toolbar = QWidget()
		toolbar.setStyleSheet(_TOOLBAR_STYLE)
		tb_layout = QHBoxLayout()
		tb_layout.setContentsMargins(8, 4, 8, 4)

		title = QLabel("Git履歴")
		title.setStyleSheet("color: #CCCCCC; font-weight: bold; font-size: 11px;")
		tb_layout.addWidget(title)
		tb_layout.addStretch()

		self.limit_combo = QComboBox()
		self.limit_combo.addItems(["20", "50", "100", "200", "500", "全て"])
		self.limit_combo.setCurrentText("50")
		self.limit_combo.setFixedWidth(70)
		self.limit_combo.currentTextChanged.connect(self.loadGraph)
		tb_layout.addWidget(self.limit_combo)

		self.branch_combo = QComboBox()
		self.branch_combo.addItem("全て")
		self.branch_combo.setFixedWidth(120)
		self.branch_combo.currentTextChanged.connect(self.loadGraph)
		tb_layout.addWidget(self.branch_combo)

		refresh_btn = QPushButton("⟳")
		refresh_btn.setFixedSize(28, 28)
		refresh_btn.setToolTip("更新")
		refresh_btn.clicked.connect(self.loadGraph)
		tb_layout.addWidget(refresh_btn)

		toolbar.setLayout(tb_layout)
		layout.addWidget(toolbar)

		# ═══ 検索バー ═══
		self.search_input = QLineEdit()
		self.search_input.setPlaceholderText("🔍 コミット/作者/ハッシュで検索...")
		self.search_input.setStyleSheet(_SEARCH_STYLE)
		self.search_input.setFixedHeight(28)
		self.search_input.textChanged.connect(self._onSearchChanged)
		layout.addWidget(self.search_input)

		# ═══ グラフエリア ═══
		scroll = QScrollArea()
		scroll.setWidgetResizable(True)
		scroll.setStyleSheet("QScrollArea { border: none; background: #252526; }")

		self.graph = CompactGraphWidget()
		self.graph.commitSelected.connect(self.showDetails)
		self.graph.fileClicked.connect(self.onCommitFileClicked)
		scroll.setWidget(self.graph)
		layout.addWidget(scroll, 1)

		# ═══ ステータスバー ═══
		self.status = QLabel("準備完了")
		self.status.setStyleSheet("background: #007ACC; color: white; padding: 4px 8px; font-size: 9px;")
		layout.addWidget(self.status)

		self.setLayout(layout)

		# ブランチ変更監視
		self.file_watcher = QFileSystemWatcher()
		self.current_branch = None
		self._setupWatcher()

		# 検索デバウンス
		self._search_timer = QTimer()
		self._search_timer.setSingleShot(True)
		self._search_timer.setInterval(300)
		self._search_timer.timeout.connect(self._applySearchFilter)

	# ─── 監視 ────────────────────────────────────────────
	def _setupWatcher(self):
		try:
			head = os.path.join(QDir.currentPath(), '.git', 'HEAD')
			if os.path.exists(head):
				self.file_watcher.addPath(head)
				self.file_watcher.fileChanged.connect(self._onBranchChanged)
				self.current_branch = self._getCurrentBranch()
		except Exception:
			pass

	def _getCurrentBranch(self):
		return run_git(['branch', '--show-current']) or None

	def _onBranchChanged(self, path):
		new = self._getCurrentBranch()
		if new != self.current_branch:
			self.current_branch = new
			if self._loaded:
				self.status.setText(f"🔄 ブランチ変更: {new}")
				self.loadGraph()
				# 監視再設定
				head = os.path.join(QDir.currentPath(), '.git', 'HEAD')
				if head not in self.file_watcher.files():
					self.file_watcher.addPath(head)

	# ─── ライフサイクル ───────────────────────────────────
	def showEvent(self, event):
		if not self._loaded:
			self.loadGraph()
			self._loaded = True
		return super().showEvent(event)

	def runGit(self, args):
		return run_git(args)

	# ─── 検索 ────────────────────────────────────────────
	def _onSearchChanged(self, text):
		self._search_timer.start()

	def _applySearchFilter(self):
		text = self.search_input.text().strip()
		self.graph.filterByText(text)
		visible = len(self.graph.commits)
		total = len(self.graph.all_commits)
		if text:
			self.status.setText(f"🔍 {visible}/{total} コミット (フィルタ中)")
		else:
			self.status.setText(f"✓ {total} コミット")

	# ─── グラフ読み込み ───────────────────────────────────
	def loadGraph(self):
		self.status.setText("📡 読み込み中...")
		current_head = self.runGit(['rev-parse', 'HEAD'])
		self._updateBranches()

		limit_text = self.limit_combo.currentText()
		limit = 999999 if limit_text == "全て" else int(limit_text)

		branch_text = self.branch_combo.currentText()
		branch = None if branch_text.startswith("全") else branch_text

		args = ['log', '--format=%H|%P|%s|%an|%ad|%D', '--date=short', '--date-order']
		if branch:
			args.append(branch)
		else:
			args.append('--all')
		args.append(f'--max-count={limit}')

		output = self.runGit(args)
		if not output:
			self.status.setText("❌ Gitリポジトリが見つかりません")
			self.graph.setCommits([])
			return

		commits = []
		for line in output.split('\n'):
			if not line:
				continue
			parts = line.split('|', 5)
			if len(parts) < 5:
				continue
			refs = []
			if len(parts) > 5 and parts[5]:
				for r in parts[5].split(','):
					r = r.strip()
					if 'HEAD ->' in r:
						refs.append(r.split('HEAD -> ')[1])
					elif 'tag:' in r:
						refs.append('🏷' + r.split('tag: ')[1])
					elif r and not r.startswith('origin/'):
						refs.append(r)

			commits.append(CommitItem(
				parts[0], parts[1].split() if parts[1] else [],
				parts[2], parts[3], parts[4], refs
			))

		self.graph.setCommits(commits, current_head)

		# 検索フィルタ再適用
		text = self.search_input.text().strip()
		if text:
			self.graph.filterByText(text)
			self.status.setText(f"🔍 {len(self.graph.commits)}/{len(commits)} コミット")
		else:
			self.status.setText(f"✓ {len(commits)} コミット")

	def _updateBranches(self):
		output = self.runGit(['branch', '-a'])
		if not output:
			return
		self.branch_combo.blockSignals(True)
		current = self.branch_combo.currentText()
		self.branch_combo.clear()
		self.branch_combo.addItem("全て")

		local_branches = []
		remote_branches = []
		for line in output.split('\n'):
			branch = line.strip().lstrip('* ').strip()
			if not branch or 'HEAD' in branch:
				continue
			if branch.startswith('remotes/'):
				remote_branches.append(branch.replace('remotes/', ''))
			else:
				local_branches.append(branch)

		for b in local_branches:
			self.branch_combo.addItem(b)
		if remote_branches:
			self.branch_combo.insertSeparator(self.branch_combo.count())
			for b in remote_branches:
				self.branch_combo.addItem(b)

		idx = self.branch_combo.findText(current)
		if idx >= 0:
			self.branch_combo.setCurrentIndex(idx)
		self.branch_combo.blockSignals(False)

	# ─── 詳細 ────────────────────────────────────────────
	def showDetails(self, commit):
		self.status.setText(f"✓ {commit.hash[:7]} — {commit.author}")
		self._loadCommitFiles(commit)

	def _loadCommitFiles(self, commit):
		if commit.parents:
			output = self.runGit(['diff', '--name-status', f'{commit.parents[0]}..{commit.hash}'])
		else:
			output = self.runGit(['diff-tree', '--no-commit-id', '--name-status', '-r', commit.hash])

		files = []
		if output:
			for line in output.split('\n'):
				if line.strip():
					parts = line.split('\t', 1)
					if len(parts) >= 2:
						files.append((parts[1].strip(), parts[0].strip()))
		self.graph.setCommitFiles(files)

	def onCommitFileClicked(self, file_path, status, commit):
		if not commit:
			return
		if status.startswith('D'):
			old = self.runGit(['show', f'{commit.parents[0]}:{file_path}']) if commit.parents else ""
			old = old or ""
			new = ""
		elif status.startswith('A'):
			old = ""
			new = self.runGit(['show', f'{commit.hash}:{file_path}']) or ""
		else:
			old = self.runGit(['show', f'{commit.parents[0]}:{file_path}']) if commit.parents else ""
			old = old or ""
			new = self.runGit(['show', f'{commit.hash}:{file_path}']) or ""

		if self.win:
			self.win.newdiffviewer(old, new, title=f"Diff: {file_path} ({commit.hash[:7]})")

