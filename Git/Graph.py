from addons.AddonBase import SecondarySideBar
from PySide6.QtWidgets import *
from PySide6.QtGui import QIcon, Qt, QColor, QFont, QPainter, QPen, QBrush, QPainterPath
from PySide6.QtCore import QTimer, QDir, QRect, QPoint, Signal, QFileSystemWatcher
from Git.common import get_status_icon, get_status_color, run_git
import os

# ─── スタイル定数 ─────────────────────────────────────────
_MENU_STYLE = """
	QMenu {
		background: #1E1E1E; color: #E0E0E0;
		border: 1px solid #454545; border-radius: 6px; padding: 6px 0;
	}
	QMenu::item { padding: 8px 28px; border-radius: 4px; margin: 2px 6px; }
	QMenu::item:selected { background: #0E639C; }
	QMenu::separator { height: 1px; background: #454545; margin: 6px 12px; }
"""
_TOOLBAR_STYLE = """
	background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
		stop:0 #323233, stop:1 #2D2D30);
	border-bottom: 1px solid #1E1E1E; padding: 6px;
"""
_SEARCH_STYLE = """
	QLineEdit {
		background: #1E1E1E; color: #E0E0E0;
		border: 1px solid #3E3E42; border-radius: 6px; padding: 6px 12px;
		font-size: 11px;
	}
	QLineEdit:focus { border-color: #0E639C; background: #252526; }
"""
_COMBO_STYLE = """
	QComboBox {
		background: #3C3C3C; color: #E0E0E0;
		border: 1px solid #4A4A4A; border-radius: 4px;
		padding: 4px 8px; min-height: 22px;
	}
	QComboBox:hover { border-color: #0E639C; background: #454545; }
	QComboBox::drop-down {
		border: none; width: 20px;
	}
	QComboBox::down-arrow { image: none; border: none; }
	QComboBox QAbstractItemView {
		background: #1E1E1E; color: #E0E0E0;
		border: 1px solid #454545; selection-background-color: #0E639C;
	}
"""
_BUTTON_STYLE = """
	QPushButton {
		background: #0E639C; color: white;
		border: none; border-radius: 4px;
		font-size: 12px; font-weight: bold;
	}
	QPushButton:hover { background: #1177BB; }
	QPushButton:pressed { background: #094771; }
"""


class CommitItem:
	"""コミット情報を保持するデータクラス"""
	__slots__ = ('hash', 'parents', 'message', 'author', 'date', 'refs',
				 'branch', 'color_index', 'visible', 'branch_name')

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
		self.branch_name = None  # ブランチ名を追跡


class CompactGraphWidget(QWidget):
	"""Gitグラフを描画するウィジェット"""
	commitSelected = Signal(CommitItem)
	fileClicked = Signal(str, str, CommitItem)

	# カラーパレット (より洗練された配色)
	COLORS = [
		QColor("#61AFEF"), QColor("#98C379"), QColor("#E06C75"),
		QColor("#D19A66"), QColor("#C678DD"), QColor("#E5C07B"),
		QColor("#56B6C2"), QColor("#BE5046"), QColor("#61AFEF").lighter(130),
	]

	# 主要ブランチの固定色
	BRANCH_COLORS = {
		'main': QColor("#98C379"),       # 緑
		'master': QColor("#98C379"),     # 緑
		'dev': QColor("#61AFEF"),        # 青
		'develop': QColor("#61AFEF"),    # 青
		'feature': QColor("#C678DD"),    # 紫
		'hotfix': QColor("#E06C75"),     # 赤
		'bugfix': QColor("#E06C75"),     # 赤
		'release': QColor("#E5C07B"),    # 黄
	}

	def __init__(self, parent=None):
		super().__init__(parent)
		self.all_commits = []
		self.commits = []       # フィルタ後の表示用
		self.row_height = 36    # 少し余裕を持たせる
		self.branch_width = 22
		self.node_size = 7      # より見やすく
		self.current_branch_head = None

		self.detail_height = 0
		self.selected_index = -1
		self.selected_commit_files = []
		self.file_rects = []
		self.selected = None
		self.hover_commit = None
		self.hover_file_index = -1

		self.branch_map = {}
		self.branch_color_map = {}  # ブランチ名→色のマッピング
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
		"""ブランチレーンを安定的に計算し、ブランチ名に基づいて色を割り当て"""
		self.branch_map.clear()
		self.branch_color_map.clear()
		active_lanes = []  # 各レーンが接続中のハッシュ (None = 空き)
		lane_branch_names = []  # 各レーンのブランチ名
		color_counter = 0

		# 最初にrefsからブランチ名を抽出してマッピング
		hash_to_branch = {}
		for commit in self.commits:
			for ref in commit.refs:
				if not ref.startswith('🏷'):  # タグ以外
					branch_name = ref.split('/')[-1] if '/' in ref else ref
					hash_to_branch[commit.hash] = branch_name
					break

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
					lane_branch_names.append(None)

			commit.branch = lane

			# ブランチ名を決定
			if commit.hash in hash_to_branch:
				branch_name = hash_to_branch[commit.hash]
				lane_branch_names[lane] = branch_name
				commit.branch_name = branch_name
			elif lane < len(lane_branch_names) and lane_branch_names[lane]:
				commit.branch_name = lane_branch_names[lane]
			else:
				commit.branch_name = None

			# ブランチ名に基づいて色を割り当て
			commit.color_index = self._getBranchColorIndex(commit.branch_name, lane, color_counter)
			if commit.branch_name and commit.branch_name not in self.branch_color_map:
				self.branch_color_map[commit.branch_name] = commit.color_index
				color_counter += 1

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
					# 第1親は同じレーン（ブランチ名も継承）
					active_lanes[lane] = parent_hash
					if commit.branch_name:
						hash_to_branch[parent_hash] = commit.branch_name
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
						lane_branch_names.append(None)

	def _getBranchColorIndex(self, branch_name, lane, counter):
		"""ブランチ名に基づいて色インデックスを取得"""
		if not branch_name:
			return lane % len(self.COLORS)

		# 既に割り当て済みならそれを使用
		if branch_name in self.branch_color_map:
			return self.branch_color_map[branch_name]

		# 主要ブランチは固定色
		for key, color in self.BRANCH_COLORS.items():
			if branch_name == key or branch_name.startswith(key + '/') or branch_name.startswith(key + '-'):
				# 固定色のインデックスを探す
				for i, c in enumerate(self.COLORS):
					if c == color:
						return i
				# 見つからなければ追加
				return self.COLORS.index(color) if color in self.COLORS else counter % len(self.COLORS)

		# その他のブランチは順番に割り当て
		return counter % len(self.COLORS)

	def getBranchColor(self, commit):
		"""コミットのブランチ色を取得"""
		if commit.branch_name:
			for key, color in self.BRANCH_COLORS.items():
				if commit.branch_name == key or commit.branch_name.startswith(key + '/') or commit.branch_name.startswith(key + '-'):
					return color
		return self.COLORS[commit.color_index]

	# ─── 描画 ────────────────────────────────────────────
	def paintEvent(self, event):
		if not self.commits:
			return
		painter = QPainter(self)
		painter.setRenderHint(QPainter.Antialiasing)
		painter.fillRect(self.rect(), QColor("#1E1E1E"))

		# 背景 (選択 / ホバー)
		for i, commit in enumerate(self.commits):
			y = self._commitY(i)
			if commit == self.selected:
				painter.fillRect(0, y, self.width(), self.row_height, QColor("#0E639C"))
			elif commit == self.hover_commit:
				painter.fillRect(0, y, self.width(), self.row_height, QColor("#2A2D2E"))

		# 詳細パネル背景
		if self.selected_index >= 0 and self.detail_height > 0:
			dy = self._commitY(self.selected_index) + self.row_height
			# グラデーション背景
			painter.fillRect(0, dy, self.width(), self.detail_height, QColor("#181818"))
			painter.setPen(QPen(QColor("#0E639C"), 2))
			painter.drawLine(0, dy, self.width(), dy)
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
		sx = commit.branch * self.branch_width + 24
		sy = self._commitY(ci) + 18
		ex = parent.branch * self.branch_width + 24
		ey = self._commitY(pi) + 18

		color = self.getBranchColor(commit)
		painter.setPen(QPen(color.darker(110), 2.0, Qt.SolidLine, Qt.RoundCap))

		if commit.branch == parent.branch:
			painter.drawLine(sx, sy, ex, ey)
		else:
			path = QPainterPath()
			path.moveTo(sx, sy)
			# より滑らかなカーブ
			ctrl_y1 = sy + (ey - sy) * 0.4
			ctrl_y2 = sy + (ey - sy) * 0.6
			path.cubicTo(sx, ctrl_y1, ex, ctrl_y2, ex, ey)
			painter.drawPath(path)

	def _drawCommit(self, painter, commit, index, text_x):
		x = commit.branch * self.branch_width + 24
		y = self._commitY(index) + 18
		color = self.getBranchColor(commit)
		is_head = self.current_branch_head and commit.hash == self.current_branch_head
		is_merge = len(commit.parents) > 1

		if is_head:
			# HEAD: 二重リング
			painter.setPen(QPen(color, 2.5))
			painter.setBrush(QBrush(QColor("#1E1E1E")))
			painter.drawEllipse(QPoint(x, y), self.node_size + 3, self.node_size + 3)
			painter.setBrush(QBrush(color))
			painter.drawEllipse(QPoint(x, y), self.node_size - 1, self.node_size - 1)
		elif is_merge:
			# マージコミット: ダイアモンド形状
			painter.setPen(QPen(color.lighter(120), 2))
			painter.setBrush(QBrush(color.darker(110)))
			path = QPainterPath()
			s = self.node_size + 2
			path.moveTo(x, y - s)
			path.lineTo(x + s, y)
			path.lineTo(x, y + s)
			path.lineTo(x - s, y)
			path.closeSubpath()
			painter.drawPath(path)
		elif commit == self.selected:
			# 選択状態: 明るいリング
			painter.setPen(QPen(QColor("#FFFFFF"), 2.5))
			painter.setBrush(QBrush(color))
			painter.drawEllipse(QPoint(x, y), self.node_size + 2, self.node_size + 2)
		elif commit == self.hover_commit:
			# ホバー状態: グロー効果
			painter.setPen(QPen(color.lighter(160), 2))
			painter.setBrush(QBrush(color.lighter(130)))
			painter.drawEllipse(QPoint(x, y), self.node_size + 1, self.node_size + 1)
		else:
			# 通常ノード
			painter.setPen(QPen(color.darker(110), 1.5))
			painter.setBrush(QBrush(color))
			painter.drawEllipse(QPoint(x, y), self.node_size, self.node_size)

		# ハッシュ
		painter.setPen(QColor("#808080"))
		painter.setFont(QFont("Consolas", 9))
		painter.drawText(text_x, y + 5, commit.hash[:7])

		# メッセージ (レスポンシブ幅)
		painter.setPen(QColor("#E0E0E0") if commit == self.selected else QColor("#D4D4D4"))
		painter.setFont(QFont("Yu Gothic UI", 9))
		msg_start = text_x + 65
		avail = self.width() - msg_start - 200
		max_chars = max(15, avail // 8)
		msg = commit.message[:max_chars] + "…" if len(commit.message) > max_chars else commit.message
		painter.drawText(msg_start, y + 5, msg)

		# refs (バッジ表示)
		if commit.refs:
			ref_x = msg_start + min(len(msg), max_chars) * 8 + 16
			for ref in commit.refs[:3]:
				font = QFont("Yu Gothic UI", 8, QFont.Bold)
				painter.setFont(font)
				fm = painter.fontMetrics()
				tw = fm.horizontalAdvance(ref) + 14
				badge_rect = QRect(ref_x, y - 9, tw, 18)

				if ref.startswith('🏷'):
					bg = QColor("#4A4A2A")
					fg = QColor("#E5C07B")
					border = QColor("#6B6B3C")
				else:
					bg = QColor("#1B3A4B")
					fg = QColor("#61AFEF")
					border = QColor("#2D5A6B")

				painter.setPen(QPen(border, 1))
				painter.setBrush(QBrush(bg))
				painter.drawRoundedRect(badge_rect, 4, 4)
				painter.setPen(fg)
				painter.drawText(badge_rect, Qt.AlignCenter, ref)
				ref_x += tw + 5

		# 作者 + 日付 (右端)
		painter.setPen(QColor("#707070"))
		painter.setFont(QFont("Yu Gothic UI", 8))
		info = f"{commit.author}  •  {commit.date}"
		iw = painter.fontMetrics().horizontalAdvance(info) + 16
		painter.drawText(self.width() - iw, y + 5, info)

	def _drawDetail(self, painter, commit, y):
		if not commit:
			return
		self.file_rects.clear()
		font_mono = QFont("Consolas", 9)
		font_ui = QFont("Yu Gothic UI", 9)
		font_ui_bold = QFont("Yu Gothic UI", 9, QFont.Bold)

		cy = y + 20
		# コミット情報セクション
		painter.setFont(font_mono)
		painter.setPen(QColor("#61AFEF"))
		painter.drawText(24, cy, "󰜘")  # commit icon alternative
		painter.setPen(QColor("#808080"))
		painter.drawText(44, cy, "COMMIT")
		painter.setPen(QColor("#E0E0E0"))
		painter.drawText(110, cy, commit.hash)
		cy += 22

		painter.setPen(QColor("#808080"))
		painter.drawText(44, cy, "AUTHOR")
		painter.setPen(QColor("#C678DD"))
		painter.drawText(110, cy, commit.author)
		cy += 22

		painter.setPen(QColor("#808080"))
		painter.drawText(44, cy, "DATE")
		painter.setPen(QColor("#98C379"))
		painter.drawText(110, cy, commit.date)
		cy += 24

		# メッセージ
		painter.setPen(QColor("#E0E0E0"))
		painter.setFont(font_ui)
		lines = [commit.message[i:i+100] for i in range(0, len(commit.message), 100)]
		for line in lines[:3]:
			painter.drawText(24, cy, line)
			cy += 18

		# 変更ファイルセクション
		if self.selected_commit_files:
			cy += 12
			painter.setPen(QColor("#61AFEF"))
			painter.setFont(font_ui_bold)
			painter.drawText(24, cy, f"📁 変更ファイル ({len(self.selected_commit_files)})")
			cy += 22

			painter.setFont(font_mono)
			for idx, (fp, st) in enumerate(self.selected_commit_files):
				fr = QRect(24, cy - 13, self.width() - 48, 20)

				# ホバー状態の描画
				is_hover = idx == self.hover_file_index
				if is_hover:
					painter.fillRect(fr, QColor("#2A2D2E"))
					painter.setPen(QColor("#0E639C"))
					painter.drawRect(fr.adjusted(0, 0, -1, -1))

				status_color = get_status_color(st)
				painter.setPen(QColor(status_color))
				painter.drawText(40, cy, f"{get_status_icon(st)} {fp}")
				self.file_rects.append((fr, fp, st))
				cy += 20

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
		old_file = self.hover_file_index
		self.hover_commit = None
		self.hover_file_index = -1
		over_file = False

		for idx, (r, _, _) in enumerate(self.file_rects):
			if r.contains(event.pos()):
				self.hover_file_index = idx
				over_file = True
				break

		self.setCursor(Qt.PointingHandCursor if over_file else Qt.ArrowCursor)

		for i, commit in enumerate(self.commits):
			ys = self._commitY(i)
			if ys <= event.pos().y() < ys + self.row_height:
				self.hover_commit = commit
				break
		if old != self.hover_commit or old_file != self.hover_file_index:
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
			base = 160  # より余裕を持たせた基本高さ
			fh = len(files) * 20
			self.detail_height = base + fh
			self._updateHeight()
		self.update()


class Main(SecondarySideBar):
	"""Git履歴グラフパネル"""
	def __init__(self, window=None):
		super().__init__()
		self.name = "GitGraph"
		self.description = "Compact Git History Graph"
		self.version = "2.1.0"
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
		tb_layout.setContentsMargins(10, 6, 10, 6)
		tb_layout.setSpacing(8)

		title = QLabel("󰜘 Git履歴")
		title.setStyleSheet("color: #E0E0E0; font-weight: bold; font-size: 12px;")
		tb_layout.addWidget(title)
		tb_layout.addStretch()

		self.limit_combo = QComboBox()
		self.limit_combo.setStyleSheet(_COMBO_STYLE)
		self.limit_combo.addItems(["20", "50", "100", "200", "500", "全て"])
		self.limit_combo.setCurrentText("50")
		self.limit_combo.setFixedWidth(75)
		self.limit_combo.currentTextChanged.connect(self.loadGraph)
		tb_layout.addWidget(self.limit_combo)

		self.branch_combo = QComboBox()
		self.branch_combo.setStyleSheet(_COMBO_STYLE)
		self.branch_combo.addItem("全ブランチ")
		self.branch_combo.setFixedWidth(140)
		self.branch_combo.currentTextChanged.connect(self.loadGraph)
		tb_layout.addWidget(self.branch_combo)

		refresh_btn = QPushButton("⟳")
		refresh_btn.setStyleSheet(_BUTTON_STYLE)
		refresh_btn.setFixedSize(32, 28)
		refresh_btn.setToolTip("更新")
		refresh_btn.clicked.connect(self.loadGraph)
		tb_layout.addWidget(refresh_btn)

		toolbar.setLayout(tb_layout)
		layout.addWidget(toolbar)

		# ═══ 検索バー ═══
		search_container = QWidget()
		search_container.setStyleSheet("background: #252526; padding: 0;")
		search_layout = QHBoxLayout()
		search_layout.setContentsMargins(10, 6, 10, 6)

		self.search_input = QLineEdit()
		self.search_input.setPlaceholderText("🔍 コミット / 作者 / ハッシュで検索...")
		self.search_input.setStyleSheet(_SEARCH_STYLE)
		self.search_input.setFixedHeight(32)
		self.search_input.textChanged.connect(self._onSearchChanged)
		search_layout.addWidget(self.search_input)

		search_container.setLayout(search_layout)
		layout.addWidget(search_container)

		# ═══ グラフエリア ═══
		scroll = QScrollArea()
		scroll.setWidgetResizable(True)
		scroll.setStyleSheet("""
			QScrollArea { border: none; background: #1E1E1E; }
			QScrollBar:vertical {
				background: #1E1E1E; width: 10px; margin: 0;
			}
			QScrollBar::handle:vertical {
				background: #3E3E42; min-height: 30px; border-radius: 5px;
			}
			QScrollBar::handle:vertical:hover { background: #4E4E52; }
			QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
		""")

		self.graph = CompactGraphWidget()
		self.graph.commitSelected.connect(self.showDetails)
		self.graph.fileClicked.connect(self.onCommitFileClicked)
		scroll.setWidget(self.graph)
		layout.addWidget(scroll, 1)

		# ═══ ステータスバー ═══
		self.status = QLabel("準備完了")
		self.status.setStyleSheet("""
			background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
				stop:0 #0E639C, stop:1 #0A4E7A);
			color: white; padding: 5px 10px; font-size: 10px; font-weight: bold;
		""")
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
		self.branch_combo.addItem("全ブランチ")

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

