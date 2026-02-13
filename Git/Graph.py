from addons.AddonBase import SecondarySideBar
from PySide6.QtWidgets import *
from PySide6.QtGui import QIcon, Qt, QColor, QFont, QPainter, QPen, QBrush
from PySide6.QtCore import QTimer, QDir, QRect, QPoint, Signal, QFileSystemWatcher
from Git.common import get_status_icon, get_status_color, run_git
import os
import re
from datetime import datetime

class CommitFileItem(QWidget):
	"""コミットの変更ファイルアイテム"""
	clicked = Signal(str, str)  # file_path, status
	
	def __init__(self, file_path, status, parent=None):
		super().__init__(parent)
		self.file_path = file_path
		self.status = status
		
		layout = QHBoxLayout()
		layout.setContentsMargins(8, 4, 8, 4)
		layout.setSpacing(8)
		
		# ステータスアイコン
		status_icon = QLabel(get_status_icon(status))
		status_icon.setFont(QFont("Segoe UI", 10))
		status_icon.setFixedWidth(20)
		layout.addWidget(status_icon)
		
		# ファイル名
		file_name = QLabel(os.path.basename(file_path))
		file_name.setFont(QFont("Segoe UI", 9))
		file_name.setStyleSheet(f"color: {get_status_color(status)};")
		layout.addWidget(file_name, 1)
		
		# パス表示
		if os.path.dirname(file_path):
			path_label = QLabel(os.path.dirname(file_path))
			path_label.setFont(QFont("Segoe UI", 8))
			path_label.setStyleSheet("color: #858585;")
			layout.addWidget(path_label)
		
		self.setLayout(layout)
		self.setStyleSheet("""
			QWidget:hover {
				background: #2A2D2E;
				border-left: 2px solid #007ACC;
			}
		""")
	
	def get_status_icon(self, status):
		"""ステータスアイコン"""
		icons = {
			'M': '◆', 'A': '+', 'D': '−', 'R': '→', 'U': '?', 'C': '©', 'T': '≠'
		}
		return icons.get(status, '•')
	
	def get_status_color(self, status):
		"""ステータスカラー"""
		colors = {
			'M': '#E5C07B', 'A': '#98C379', 'D': '#E06C75',
			'R': '#61AFEF', 'U': '#4EC9B0', 'C': '#C678DD', 'T': '#56B6C2'
		}
		return colors.get(status, '#ABB2BF')
	
	def mousePressEvent(self, event):
		"""クリックイベント"""
		if event.button() == Qt.LeftButton:
			self.clicked.emit(self.file_path, self.status)

class CommitItem:
	"""シンプルなコミット情報を保持するクラス"""
	def __init__(self, hash, parents, message, author, date, refs):
		self.hash = hash
		self.parents = parents
		self.message = message
		self.author = author
		self.date = date
		self.refs = refs
		self.branch = 0
		self.color_index = 0

class CompactGraphWidget(QWidget):
	"""コンパクトなGitグラフを描画するウィジェット"""
	commitSelected = Signal(CommitItem)
	fileClicked = Signal(str, str, CommitItem)  # file_path, status, commit
	
	def __init__(self, parent=None):
		super().__init__(parent)
		self.commits = []
		self.row_height = 32
		self.branch_width = 20
		self.node_size = 6
		self.current_branch_head = None  # 現在のブランチのHEAD
		self.detail_height = 0  # 詳細パネルの高さ
		self.selected_index = -1  # 選択されたコミットのインデックス
		self.selected_commit_files = []  # 選択されたコミットのファイル一覧
		self.file_rects = []  # ファイルのクリック可能領域 [(rect, file_path, status), ...]
		self.setMinimumHeight(50)
		
		# カラーパレット（パステル調）
		self.colors = [
			QColor("#66D9EF"),  # シアン
			QColor("#A6E22E"),  # グリーン
			QColor("#F92672"),  # マゼンタ
			QColor("#FD971F"),  # オレンジ
			QColor("#AE81FF"),  # パープル
			QColor("#E6DB74"),  # イエロー
		]
		
		self.branch_map = {}
		self.selected = None
		self.hover_commit = None
		
		# マウストラッキングを有効化
		self.setMouseTracking(True)
	
	def setCommits(self, commits, current_head=None):
		"""コミットを設定してレイアウト計算"""
		self.commits = commits
		self.current_branch_head = current_head
		self.calculateBranches()
		self.updateHeight()
		self.update()
	
	def updateHeight(self):
		"""ウィジェットの高さを更新"""
		total_height = len(self.commits) * self.row_height + 30
		if self.selected_index >= 0:
			total_height += self.detail_height
		self.setFixedHeight(total_height)
	
	def calculateBranches(self):
		"""ブランチレーンを計算（簡易版）"""
		self.branch_map.clear()
		used_branches = []
		next_branch = 0
		
		for i, commit in enumerate(self.commits):
			# ブランチ番号を決定
			if commit.hash in self.branch_map:
				branch = self.branch_map[commit.hash]
			else:
				# 空いているブランチを探す
				if used_branches:
					available_branches = [b for b in used_branches if b not in [self.branch_map.get(c.hash, -1) for c in self.commits[i:]]]
					if available_branches:
						branch = min(available_branches)
					else:
						branch = next_branch
						next_branch += 1
				else:
					branch = next_branch
					next_branch += 1
			
			commit.branch = branch
			commit.color_index = branch % len(self.colors)
			
			# 親コミットにブランチを割り当て
			for j, parent_hash in enumerate(commit.parents):
				if parent_hash not in self.branch_map:
					if j == 0:
						# 第1親は同じブランチ
						self.branch_map[parent_hash] = branch
					else:
						# マージ元は新しいブランチ
						new_branch = next_branch
						next_branch += 1
						self.branch_map[parent_hash] = new_branch
						used_branches.append(new_branch)
	
	def paintEvent(self, event):
		"""グラフ描画"""
		painter = QPainter(self)
		painter.setRenderHint(QPainter.Antialiasing)
		
		# 背景
		painter.fillRect(self.rect(), QColor("#252526"))
		
		# ホバー・選択中の行の背景を描画（接続線の前に）
		for i, commit in enumerate(self.commits):
			y = self.getCommitY(i)
			
			if commit == self.selected:
				# 選択中の行
				painter.fillRect(0, y, self.width(), self.row_height, QColor("#094771"))
			elif commit == self.hover_commit:
				# ホバー中の行
				painter.fillRect(0, y, self.width(), self.row_height, QColor("#2A2D2E"))
		
		# 詳細パネルの背景
		if self.selected_index >= 0 and self.detail_height > 0:
			detail_y = self.getCommitY(self.selected_index) + self.row_height
			painter.fillRect(0, detail_y, self.width(), self.detail_height, QColor("#1E1E1E"))
			painter.setPen(QColor("#3E3E42"))
			painter.drawRect(0, detail_y, self.width() - 1, self.detail_height - 1)
			
			# 詳細情報を描画
			self.drawDetail(painter, self.selected, detail_y)
		
		# 接続線を描画
		for i, commit in enumerate(self.commits):
			for parent_hash in commit.parents:
				parent = self.findCommit(parent_hash)
				if parent:
					self.drawLine(painter, commit, parent, i)
		
		# コミットノードとテキストを描画
		for i, commit in enumerate(self.commits):
			self.drawCommit(painter, commit, i)
	
	def getCommitY(self, index):
		"""コミットのY座標を取得（詳細パネルを考慮）"""
		if index <= self.selected_index or self.selected_index < 0:
			return index * self.row_height
		else:
			return index * self.row_height + self.detail_height
	
	def drawLine(self, painter, commit, parent, index):
		"""接続線を描画"""
		start_x = commit.branch * self.branch_width + 20
		start_y = self.getCommitY(index) + 15
		
		parent_idx = self.commits.index(parent) if parent in self.commits else -1
		if parent_idx >= 0:
			end_x = parent.branch * self.branch_width + 20
			end_y = self.getCommitY(parent_idx) + 15
			
			color = self.colors[commit.color_index]
			pen = QPen(color.darker(130), 1.5)
			painter.setPen(pen)
			
			if commit.branch == parent.branch:
				# 直線
				painter.drawLine(start_x, start_y, end_x, end_y)
			else:
				# ベジェ曲線
				from PySide6.QtGui import QPainterPath
				path = QPainterPath()
				path.moveTo(start_x, start_y)
				
				mid_y = (start_y + end_y) / 2
				path.cubicTo(start_x, mid_y, end_x, mid_y, end_x, end_y)
				painter.drawPath(path)
	
	def drawCommit(self, painter, commit, index):
		"""コミットノードとテキストを描画"""
		x = commit.branch * self.branch_width + 20
		y = self.getCommitY(index) + 15
		
		# ノード
		color = self.colors[commit.color_index]
		is_head = (self.current_branch_head and commit.hash == self.current_branch_head)
		
		if is_head:
			# 現在のブランチHEAD: 空洞の丸（○）
			painter.setPen(QPen(color, 2))
			painter.setBrush(QBrush(QColor("#252526")))  # 背景色で塗りつぶし
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
		
		# テキスト
		text_x = max([c.branch for c in self.commits]) * self.branch_width + 40
		
		# コミットハッシュ（最初に表示）
		painter.setPen(QColor("#858585"))
		font = QFont("Consolas", 8)
		painter.setFont(font)
		painter.drawText(text_x, y + 4, commit.hash[:7])
		
		# コミットメッセージ
		painter.setPen(QColor("#CCCCCC"))
		font = QFont("Yu Gothic UI", 9)
		painter.setFont(font)
		message = commit.message[:35] + "..." if len(commit.message) > 35 else commit.message
		painter.drawText(text_x + 60, y + 4, message)
		
		# ブランチ/タグ（あれば）
		if commit.refs:
			painter.setPen(QColor("#4EC9B0"))
			font.setBold(True)
			font.setPointSize(8)
			painter.setFont(font)
			ref_text = " ".join([f"◆{ref}" for ref in commit.refs[:2]])
			painter.drawText(text_x + 280, y + 4, ref_text)
			font.setBold(False)
	
	def drawDetail(self, painter, commit, y):
		"""詳細情報を描画"""
		if not commit:
			return
		
		# ファイルクリック領域をクリア
		self.file_rects.clear()
		
		painter.setPen(QColor("#CCCCCC"))
		font = QFont("Consolas", 8)
		painter.setFont(font)
		
		# コミット情報
		info_y = y + 15
		painter.drawText(20, info_y, f"COMMIT: {commit.hash}")
		info_y += 15
		painter.drawText(20, info_y, f"AUTHOR: {commit.author}")
		info_y += 15
		painter.drawText(20, info_y, f"DATE: {commit.date}")
		info_y += 15
		
		painter.setPen(QColor("#569CD6"))
		painter.drawText(20, info_y, "MESSAGE:")
		info_y += 15
		painter.setPen(QColor("#D4D4D4"))
		
		# メッセージを複数行に分割
		message_lines = [commit.message[i:i+80] for i in range(0, len(commit.message), 80)]
		for line in message_lines[:3]:  # 最大3行
			painter.drawText(40, info_y, line)
			info_y += 15
		
		# ファイルリスト
		if self.selected_commit_files:
			info_y += 10
			painter.setPen(QColor("#4EC9B0"))
			painter.drawText(20, info_y, f"📄 変更されたファイル ({len(self.selected_commit_files)}):")
			info_y += 15
			
			# すべてのファイルを表示
			for file_path, status in self.selected_commit_files:
				file_y = info_y
				
				# ホバー背景
				file_rect = QRect(30, file_y - 12, self.width() - 40, 15)
				if file_rect.contains(self.mapFromGlobal(self.cursor().pos())):
					painter.fillRect(file_rect, QColor("#2A2D2E"))
				
				# ファイル表示
				color = get_status_color(status)
				painter.setPen(QColor(color))
				icon = get_status_icon(status)
				painter.drawText(40, info_y, f"{icon} {file_path}")
				
				# クリック領域を記録
				self.file_rects.append((file_rect, file_path, status))
				info_y += 15
	
	def findCommit(self, hash):
		"""ハッシュでコミット検索"""
		for c in self.commits:
			if c.hash == hash:
				return c
		return None
	
	def mousePressEvent(self, event):
		"""クリック処理"""
		# ファイルクリックをチェック
		for rect, file_path, status in self.file_rects:
			if rect.contains(event.pos()):
				self.fileClicked.emit(file_path, status, self.selected)
				return
		
		# コミット行クリック
		for i, commit in enumerate(self.commits):
			y_start = self.getCommitY(i)
			y_end = y_start + self.row_height
			
			# 行全体でクリック可能
			if y_start <= event.pos().y() < y_end:
				# 同じコミットをクリックした場合は折りたたみ
				if self.selected == commit and self.detail_height > 0:
					self.selected = None
					self.selected_index = -1
					self.detail_height = 0
					self.selected_commit_files = []
				else:
					self.selected = commit
					self.selected_index = i
					self.detail_height = 90  # 詳細パネルの初期高さ（ファイル読み込み前）
					self.commitSelected.emit(commit)
				
				self.updateHeight()
				self.update()
				break
	
	def mouseMoveEvent(self, event):
		"""マウスホバー処理"""
		old_hover = self.hover_commit
		self.hover_commit = None
		
		# ファイル領域のホバーチェック
		is_over_file = False
		for rect, file_path, status in self.file_rects:
			if rect.contains(event.pos()):
				is_over_file = True
				break
		
		# カーソルを変更
		if is_over_file:
			self.setCursor(Qt.PointingHandCursor)
		else:
			self.setCursor(Qt.ArrowCursor)
		
		for i, commit in enumerate(self.commits):
			y_start = self.getCommitY(i)
			y_end = y_start + self.row_height
			
			# 行全体でホバー可能
			if y_start <= event.pos().y() < y_end:
				self.hover_commit = commit
				break
		
		if old_hover != self.hover_commit:
			self.update()
	
	def setCommitFiles(self, files):
		"""選択されたコミットのファイル一覧を設定"""
		self.selected_commit_files = files
		
		# ファイル数に応じて詳細パネルの高さを調整
		if self.selected_index >= 0:
			# 基本情報（COMMIT, AUTHOR, DATE）: 15px × 3 = 45px
			# MESSAGE ヘッダー + メッセージ（最大3行）: 15px + 15px × 3 = 60px
			# ファイルリストヘッダー: 10px（余白） + 15px = 25px
			# 下部余白: 15px
			base_height = 145
			# ファイル1つにつき15px
			file_height = len(files) * 15
			self.detail_height = base_height + file_height
			self.updateHeight()
		
		self.update()

class Main(SecondarySideBar):
	"""SecondarySideBar用のGitGraphクラス"""
	def __init__(self, window=None):
		super().__init__()
		self.name = "GitGraph"
		self.description = "Compact Git History Graph"
		self.version = "1.0.0"
		self.win = window

		self.icon_color(f"{window.DIR}/assets/gitgraph.svg")
		self.icon = QIcon(f"{window.DIR}/assets/gitgraph.svg")
		
		self._loaded = False
		
		layout = QVBoxLayout()
		layout.setContentsMargins(0, 0, 0, 0)
		layout.setSpacing(0)
		
		# ツールバー
		toolbar = QWidget()
		toolbar.setStyleSheet("background: #2D2D30; padding: 5px;")
		toolbar_layout = QHBoxLayout()
		toolbar_layout.setContentsMargins(8, 4, 8, 4)
		
		title = QLabel("Git履歴")
		title.setStyleSheet("color: #CCCCCC; font-weight: bold; font-size: 11px;")
		toolbar_layout.addWidget(title)
		
		toolbar_layout.addStretch()
		
		# コミット数制限
		self.limit_combo = QComboBox()
		self.limit_combo.addItems(["20", "50", "100", "200", "全て"])
		self.limit_combo.setCurrentText("50")
		self.limit_combo.setFixedWidth(80)
		self.limit_combo.currentTextChanged.connect(self.loadGraph)
		toolbar_layout.addWidget(self.limit_combo)
		
		# ブランチフィルター
		self.branch_combo = QComboBox()
		self.branch_combo.addItem("全て")
		self.branch_combo.setFixedWidth(120)
		self.branch_combo.currentTextChanged.connect(self.loadGraph)
		toolbar_layout.addWidget(self.branch_combo)
		
		# 更新ボタン
		refresh_btn = QPushButton("⟳")
		refresh_btn.setFixedSize(28, 28)
		refresh_btn.setToolTip("更新")
		refresh_btn.clicked.connect(self.loadGraph)
		toolbar_layout.addWidget(refresh_btn)
		
		toolbar.setLayout(toolbar_layout)
		layout.addWidget(toolbar)
		
		# グラフエリア
		scroll = QScrollArea()
		scroll.setWidgetResizable(True)
		scroll.setStyleSheet("QScrollArea { border: none; background: #252526; }")
		
		self.graph = CompactGraphWidget()
		self.graph.commitSelected.connect(self.showDetails)
		self.graph.fileClicked.connect(self.onCommitFileClicked)
		scroll.setWidget(self.graph)
		
		layout.addWidget(scroll, 1)
		
		# ステータスバー
		self.status = QLabel("準備完了")
		self.status.setStyleSheet("background: #007ACC; color: white; padding: 4px 8px; font-size: 9px;")
		layout.addWidget(self.status)
		
		self.setLayout(layout)
		
		# ブランチ移動の監視を設定
		self.file_watcher = QFileSystemWatcher()
		self.current_branch = None
		self.setupBranchWatcher()
	
	def setupBranchWatcher(self):
		"""ブランチ移動の監視をセットアップ"""
		try:
			git_dir = os.path.join(QDir.currentPath(), '.git')
			
			# .git/HEAD ファイルを監視
			head_file = os.path.join(git_dir, 'HEAD')
			if os.path.exists(head_file):
				self.file_watcher.addPath(head_file)
				self.file_watcher.fileChanged.connect(self.onBranchChanged)
				
				# 現在のブランチを保存
				self.current_branch = self.getCurrentBranch()
		except Exception as e:
			print(f"Branch watcher setup failed: {e}")
	
	def getCurrentBranch(self):
		"""現在のブランチ名を取得"""
		output = self.runGit(['branch', '--show-current'])
		return output if output else None
	
	def onBranchChanged(self, path):
		"""ブランチが変更された時の処理"""
		new_branch = self.getCurrentBranch()
		if new_branch != self.current_branch:
			self.current_branch = new_branch
			if self._loaded:
				self.status.setText(f"🔄 ブランチ変更検知: {new_branch}")
				self.loadGraph()
				
				# HEADファイルの監視を再設定（一部のシステムで必要）
				git_dir = os.path.join(QDir.currentPath(), '.git')
				head_file = os.path.join(git_dir, 'HEAD')
				if head_file not in self.file_watcher.files():
					self.file_watcher.addPath(head_file)
	
	def showEvent(self, event):
		"""表示時に読み込み"""
		if not self._loaded:
			self.loadGraph()
			self._loaded = True
		return super().showEvent(event)
	
	def runGit(self, args):
		"""Gitコマンド実行"""
		return run_git(args)
	
	def loadGraph(self):
		"""グラフを読み込み"""
		self.status.setText("📡 読み込み中...")
		
		# 現在のブランチのHEADを取得
		current_head = self.runGit(['rev-parse', 'HEAD'])
		
		# ブランチリスト更新
		self.updateBranches()
		
		# コミット取得
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
		
		# パース
		commits = []
		for line in output.split('\n'):
			if not line:
				continue
			
			parts = line.split('|', 5)
			if len(parts) >= 5:
				hash = parts[0]
				parents = parts[1].split() if parts[1] else []
				message = parts[2]
				author = parts[3]
				date = parts[4]
				refs_raw = parts[5] if len(parts) > 5 else ""
				
				# リファレンス抽出
				refs = []
				if refs_raw:
					for ref in refs_raw.split(','):
						ref = ref.strip()
						if 'HEAD ->' in ref:
							refs.append(ref.split('HEAD -> ')[1])
						elif 'tag:' in ref:
							refs.append('🏷️' + ref.split('tag: ')[1])
						elif not ref.startswith('origin/'):
							refs.append(ref)
				
				commit = CommitItem(hash, parents, message, author, date, refs)
				commits.append(commit)
		
		self.graph.setCommits(commits, current_head)
		self.status.setText(f"✓ {len(commits)} コミット")
	
	def updateBranches(self):
		"""ブランチリスト更新"""
		output = self.runGit(['branch'])
		if output:
			self.branch_combo.blockSignals(True)
			current = self.branch_combo.currentText()
			self.branch_combo.clear()
			self.branch_combo.addItem("全て")
			
			for line in output.split('\n'):
				branch = line.strip().lstrip('* ').strip()
				if branch:
					self.branch_combo.addItem(branch)
			
			idx = self.branch_combo.findText(current)
			if idx >= 0:
				self.branch_combo.setCurrentIndex(idx)
			self.branch_combo.blockSignals(False)
	
	def showDetails(self, commit):
		"""詳細表示"""
		self.status.setText(f"✓ {commit.hash[:7]} selected")
		
		# 変更ファイルを取得して表示
		self.loadCommitFiles(commit)
	
	def loadCommitFiles(self, commit):
		"""コミットの変更ファイルを取得して表示"""
		# 変更ファイルを取得
		if commit.parents:
			# 通常のコミット: 親との差分
			output = self.runGit(['diff', '--name-status', f'{commit.parents[0]}..{commit.hash}'])
		else:
			# 初回コミット
			output = self.runGit(['diff-tree', '--no-commit-id', '--name-status', '-r', commit.hash])
		
		if not output:
			self.graph.setCommitFiles([])
			return
		
		# ファイルをパース
		files = []
		for line in output.split('\n'):
			if line.strip():
				parts = line.split('\t', 1)
				if len(parts) >= 2:
					status = parts[0].strip()
					file_path = parts[1].strip()
					files.append((file_path, status))
		
		# グラフウィジェットにファイル情報を渡す
		self.graph.setCommitFiles(files)
	
	def onCommitFileClicked(self, file_path, status, commit):
		"""コミットファイルがクリックされた時"""
		# commitがNoneの場合は何もしない
		if not commit:
			return
		
		# 差分を表示
		if status.startswith('D'):
			# 削除されたファイル: 親コミットのファイル内容のみ
			if commit.parents:
				old_content = self.runGit(['show', f'{commit.parents[0]}:{file_path}']) or ""
			else:
				old_content = ""
			new_content = ""
			self.status.setText(f"🗑 削除: {os.path.basename(file_path)}")
		elif status.startswith('A'):
			# 追加されたファイル: 新しいファイル内容のみ
			old_content = ""
			new_content = self.runGit(['show', f'{commit.hash}:{file_path}']) or ""
			self.status.setText(f"➕ 追加: {os.path.basename(file_path)}")
		else:
			# 変更されたファイル: 両方の内容を取得
			if commit.parents:
				old_content = self.runGit(['show', f'{commit.parents[0]}:{file_path}']) or ""
			else:
				old_content = ""
			new_content = self.runGit(['show', f'{commit.hash}:{file_path}']) or ""
			self.status.setText(f"📝 変更: {os.path.basename(file_path)}")
		
		# DiffViewerで表示
		if self.win:
			self.win.newdiffviewer(old_content, new_content, title=f"Diff: {file_path} ({commit.hash[:7]})")

