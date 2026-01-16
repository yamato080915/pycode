from addons.AddonBase import ActivityBar, SideBar
from PySide6.QtWidgets import *
from PySide6.QtGui import QIcon, Qt, QColor, QFont, QPainter
from PySide6.QtCore import QTimer, QDir, Signal, QSize
import subprocess
import os
from datetime import datetime

class FileChangeItem(QWidget):
	"""VSCode風のファイル変更アイテム"""
	clicked = Signal(str, str)  # file_path, stage_type
	stageToggled = Signal(str, str)  # file_path, action (stage/unstage)
	
	def __init__(self, file_path, status, stage_type, parent=None):
		super().__init__(parent)
		self.file_path = file_path
		self.status = status
		self.stage_type = stage_type
		
		layout = QHBoxLayout()
		layout.setContentsMargins(8, 4, 8, 4)
		layout.setSpacing(8)
		
		# ステータスアイコン
		status_icon = QLabel(self.get_status_icon(status))
		status_icon.setFont(QFont("Segoe UI", 10))
		status_icon.setFixedWidth(20)
		layout.addWidget(status_icon)
		
		# ファイル名
		file_name = QLabel(os.path.basename(file_path))
		file_name.setFont(QFont("Segoe UI", 9))
		file_name.setStyleSheet(f"color: {self.get_status_color(status)};")
		layout.addWidget(file_name, 1)
		
		# ステージボタン
		if stage_type != 'staged':
			stage_btn = QPushButton("+")
			stage_btn.setFixedSize(20, 20)
			stage_btn.setToolTip("ステージに追加")
			stage_btn.setStyleSheet("""
				QPushButton {
					background: transparent;
					border: 1px solid #3E3E42;
					border-radius: 3px;
					color: #CCCCCC;
					font-weight: bold;
				}
				QPushButton:hover {
					background: #2D2D30;
					border-color: #007ACC;
				}
			""")
			stage_btn.clicked.connect(lambda: self.stageToggled.emit(file_path, 'stage'))
			layout.addWidget(stage_btn)
		else:
			unstage_btn = QPushButton("−")
			unstage_btn.setFixedSize(20, 20)
			unstage_btn.setToolTip("ステージから削除")
			unstage_btn.setStyleSheet("""
				QPushButton {
					background: transparent;
					border: 1px solid #3E3E42;
					border-radius: 3px;
					color: #CCCCCC;
					font-weight: bold;
				}
				QPushButton:hover {
					background: #2D2D30;
					border-color: #E06C75;
				}
			""")
			unstage_btn.clicked.connect(lambda: self.stageToggled.emit(file_path, 'unstage'))
			layout.addWidget(unstage_btn)
		
		self.setLayout(layout)
		self.setStyleSheet("""
			QWidget:hover {
				background: #2A2D2E;
			}
		""")
	
	def get_status_icon(self, status):
		"""ステータスアイコン"""
		icons = {
			'M': '◆', 'A': '+', 'D': '−', 'R': '→', 'U': '?', 'C': '©'
		}
		return icons.get(status, '•')
	
	def get_status_color(self, status):
		"""ステータスカラー"""
		colors = {
			'M': '#E5C07B', 'A': '#98C379', 'D': '#E06C75',
			'R': '#61AFEF', 'U': '#4EC9B0', 'C': '#C678DD'
		}
		return colors.get(status, '#ABB2BF')
	
	def mousePressEvent(self, event):
		"""クリックイベント"""
		if event.button() == Qt.LeftButton:
			self.clicked.emit(self.file_path, self.stage_type)

class Button(ActivityBar):
	def __init__(self, window=None):
		super().__init__()
		self.win = window
	
	def button(self):
		self.btn = super().button()
		self.btn.setObjectName("git_btn")
		self.icon_color(f"{self.win.DIR}/assets/git.svg")
		self.btn.setIcon(QIcon(f"{self.win.DIR}/assets/git.svg"))
		return self.btn

class Main(SideBar):
	def __init__(self, window=None, index=2):
		super().__init__()
		self.name = "Git"
		self.description = "Git Source Control"
		self.version = "1.0.0"
		
		self.win = window
		self.index = index
		self._connected = False
		
		layout = QVBoxLayout()
		layout.setContentsMargins(0, 0, 0, 0)
		layout.setSpacing(0)
		
		# === ヘッダー ===
		header = QWidget()
		header.setStyleSheet("background: #252526; border-bottom: 1px solid #3E3E42;")
		header_layout = QVBoxLayout()
		header_layout.setContentsMargins(12, 8, 12, 8)
		header_layout.setSpacing(8)
		
		# タイトルと更新ボタン
		title_layout = QHBoxLayout()
		title = QLabel("ソース管理")
		title.setFont(QFont("Segoe UI", 11, QFont.Bold))
		title.setStyleSheet("color: #CCCCCC;")
		title_layout.addWidget(title)
		
		title_layout.addStretch()
		
		refresh_btn = QPushButton("⟳")
		refresh_btn.setFixedSize(24, 24)
		refresh_btn.setToolTip("更新")
		refresh_btn.setStyleSheet("""
			QPushButton {
				background: transparent;
				border: none;
				color: #CCCCCC;
				font-size: 14px;
			}
			QPushButton:hover {
				background: #2A2D2E;
				border-radius: 3px;
			}
		""")
		refresh_btn.clicked.connect(self.refresh)
		title_layout.addWidget(refresh_btn)
		
		header_layout.addLayout(title_layout)
		
		# ブランチ情報
		self.branch_widget = QWidget()
		branch_layout = QHBoxLayout()
		branch_layout.setContentsMargins(0, 0, 0, 0)
		branch_layout.setSpacing(8)
		
		branch_icon = QLabel("⎇")
		branch_icon.setStyleSheet("color: #C678DD; font-size: 14px;")
		branch_layout.addWidget(branch_icon)
		
		self.branch_label = QLabel("main")
		self.branch_label.setFont(QFont("Segoe UI", 9))
		self.branch_label.setStyleSheet("color: #C678DD;")
		branch_layout.addWidget(self.branch_label)
		
		branch_layout.addStretch()
		
		# ブランチ切替ボタン
		switch_btn = QPushButton("切替")
		switch_btn.setFixedHeight(22)
		switch_btn.setStyleSheet("""
			QPushButton {
				background: transparent;
				border: 1px solid #3E3E42;
				border-radius: 3px;
				color: #CCCCCC;
				padding: 2px 8px;
				font-size: 8px;
			}
			QPushButton:hover {
				background: #2A2D2E;
				border-color: #007ACC;
			}
		""")
		switch_btn.clicked.connect(self.show_branch_menu)
		branch_layout.addWidget(switch_btn)
		
		self.branch_widget.setLayout(branch_layout)
		header_layout.addWidget(self.branch_widget)
		
		header.setLayout(header_layout)
		layout.addWidget(header)
		
		# === コミットメッセージ入力 ===
		commit_section = QWidget()
		commit_section.setStyleSheet("background: #1E1E1E; border-bottom: 1px solid #3E3E42;")
		commit_layout = QVBoxLayout()
		commit_layout.setContentsMargins(12, 8, 12, 8)
		commit_layout.setSpacing(6)
		
		self.commit_input = QTextEdit()
		self.commit_input.setPlaceholderText("メッセージ (Ctrl+Enter でコミット)")
		self.commit_input.setMaximumHeight(60)
		self.commit_input.setFont(QFont("Segoe UI", 9))
		self.commit_input.setStyleSheet("""
			QTextEdit {
				background: #252526;
				color: #CCCCCC;
				border: 1px solid #3E3E42;
				border-radius: 3px;
				padding: 6px;
			}
			QTextEdit:focus {
				border-color: #007ACC;
			}
		""")
		commit_layout.addWidget(self.commit_input)
		
		# コミット＆アクションボタン
		action_layout = QHBoxLayout()
		action_layout.setSpacing(6)
		
		self.commit_btn = QPushButton("✓ コミット")
		self.commit_btn.setFixedHeight(28)
		self.commit_btn.setStyleSheet("""
			QPushButton {
				background: #007ACC;
				color: white;
				border: none;
				border-radius: 3px;
				padding: 4px 12px;
				font-weight: bold;
			}
			QPushButton:hover {
				background: #0098FF;
			}
			QPushButton:pressed {
				background: #005A9E;
			}
			QPushButton:disabled {
				background: #3E3E42;
				color: #6E6E6E;
			}
		""")
		self.commit_btn.clicked.connect(self.commit)
		action_layout.addWidget(self.commit_btn, 2)
		
		more_btn = QPushButton("⋯")
		more_btn.setFixedSize(28, 28)
		more_btn.setToolTip("その他の操作")
		more_btn.setStyleSheet("""
			QPushButton {
				background: transparent;
				border: 1px solid #3E3E42;
				border-radius: 3px;
				color: #CCCCCC;
			}
			QPushButton:hover {
				background: #2A2D2E;
				border-color: #007ACC;
			}
		""")
		more_btn.clicked.connect(self.show_more_menu)
		action_layout.addWidget(more_btn)
		
		commit_layout.addLayout(action_layout)
		
		commit_section.setLayout(commit_layout)
		layout.addWidget(commit_section)
		
		# === 変更リスト ===
		scroll = QScrollArea()
		scroll.setWidgetResizable(True)
		scroll.setStyleSheet("""
			QScrollArea {
				border: none;
				background: #1E1E1E;
			}
			QScrollBar:vertical {
				background: #1E1E1E;
				width: 10px;
			}
			QScrollBar::handle:vertical {
				background: #424242;
				border-radius: 5px;
			}
			QScrollBar::handle:vertical:hover {
				background: #4E4E4E;
			}
		""")
		
		scroll_content = QWidget()
		self.changes_layout = QVBoxLayout()
		self.changes_layout.setContentsMargins(0, 0, 0, 0)
		self.changes_layout.setSpacing(0)
		scroll_content.setLayout(self.changes_layout)
		scroll.setWidget(scroll_content)
		
		layout.addWidget(scroll, 1)
		
		# === ステータスバー ===
		self.status_bar = QLabel("準備完了")
		self.status_bar.setFont(QFont("Segoe UI", 8))
		self.status_bar.setStyleSheet("""
			QLabel {
				background: #007ACC;
				color: white;
				padding: 4px 12px;
			}
		""")
		layout.addWidget(self.status_bar)
		
		self.setLayout(layout)
		
		# データ
		self.staged_files = []
		self.unstaged_files = []
		self.untracked_files = []
		self.branches = []
		self.current_branch = ""
		
		# 自動更新タイマー
		self.timer = QTimer()
		self.timer.timeout.connect(self.refresh)
	
	def showEvent(self, event):
		"""表示時"""
		if not self._connected:
			self.refresh()
			self.timer.start(3000)  # 3秒ごと
			self._connected = True
		return super().showEvent(event)
	
	def hideEvent(self, event):
		"""非表示時"""
		self.timer.stop()
		return super().hideEvent(event)
	
	def runGit(self, args, show_error=True):
		"""Gitコマンド実行"""
		try:
			cwd = QDir.currentPath()
			if os.name == 'nt':
				si = subprocess.STARTUPINFO()
				si.dwFlags = subprocess.STARTF_USESHOWWINDOW
				result = subprocess.run(
					['git'] + args,
					capture_output=True,
					text=True,
					encoding='utf-8',
					errors='replace',
					cwd=cwd,
					startupinfo=si
				)
			else:
				result = subprocess.run(
					['git'] + args,
					capture_output=True,
					text=True,
					encoding='utf-8',
					errors='replace',
					cwd=cwd
				)
			
			if result.returncode != 0:
				if show_error:
					self.status_bar.setText(f"⚠ {result.stderr.strip()[:50]}")
				return None
			return result.stdout.strip()
		except:
			if show_error:
				self.status_bar.setText("⚠ Gitが見つかりません")
			return None
	
	def refresh(self):
		"""状態更新"""
		# ブランチ取得
		branch = self.runGit(['branch', '--show-current'], False)
		if not branch:
			self.status_bar.setText("⚠ Gitリポジトリではありません")
			return
		
		self.current_branch = branch
		self.branch_label.setText(branch)
		
		# ブランチリスト取得
		branches_output = self.runGit(['branch'], False)
		if branches_output:
			self.branches = [b.strip().lstrip('* ') for b in branches_output.split('\n') if b.strip()]
		
		# ステージ済み
		self.staged_files = []
		staged_output = self.runGit(['diff', '--name-status', '--cached'], False)
		if staged_output:
			for line in staged_output.split('\n'):
				if line:
					parts = line.split('\t', 1)
					if len(parts) >= 2:
						self.staged_files.append((parts[1], parts[0]))
		
		# 未ステージ
		self.unstaged_files = []
		unstaged_output = self.runGit(['diff', '--name-status'], False)
		if unstaged_output:
			for line in unstaged_output.split('\n'):
				if line:
					parts = line.split('\t', 1)
					if len(parts) >= 2:
						self.unstaged_files.append((parts[1], parts[0]))
		
		# 未追跡
		self.untracked_files = []
		untracked_output = self.runGit(['ls-files', '--others', '--exclude-standard'], False)
		if untracked_output:
			self.untracked_files = [(f, 'U') for f in untracked_output.split('\n') if f]
		
		# UI更新
		self.update_changes_list()
		
		total = len(self.staged_files) + len(self.unstaged_files) + len(self.untracked_files)
		self.status_bar.setText(f"✓ {total} 件の変更")
	
	def update_changes_list(self):
		"""変更リスト更新"""
		# クリア
		while self.changes_layout.count():
			item = self.changes_layout.takeAt(0)
			if item.widget():
				item.widget().deleteLater()
		
		# ステージ済み変更
		if self.staged_files:
			header = QLabel(f"ステージ済みの変更 ({len(self.staged_files)})")
			header.setFont(QFont("Segoe UI", 9, QFont.Bold))
			header.setStyleSheet("color: #CCCCCC; padding: 8px 12px; background: #252526;")
			self.changes_layout.addWidget(header)
			
			for file_path, status in self.staged_files:
				item = FileChangeItem(file_path, status, 'staged')
				item.clicked.connect(self.on_file_clicked)
				item.stageToggled.connect(self.on_stage_toggle)
				self.changes_layout.addWidget(item)
		
		# 変更
		changes = self.unstaged_files + self.untracked_files
		if changes:
			header = QLabel(f"変更 ({len(changes)})")
			header.setFont(QFont("Segoe UI", 9, QFont.Bold))
			header.setStyleSheet("color: #CCCCCC; padding: 8px 12px; background: #252526;")
			self.changes_layout.addWidget(header)
			
			for file_path, status in changes:
				stage_type = 'untracked' if status == 'U' else 'unstaged'
				item = FileChangeItem(file_path, status, stage_type)
				item.clicked.connect(self.on_file_clicked)
				item.stageToggled.connect(self.on_stage_toggle)
				self.changes_layout.addWidget(item)
		
		# スペーサー
		self.changes_layout.addStretch()
		
		# コミットボタンの有効/無効
		self.commit_btn.setEnabled(len(self.staged_files) > 0)
	
	def on_file_clicked(self, file_path, stage_type):
		"""ファイルクリック"""
		full_path = QDir.current().filePath(file_path)
		
		if stage_type == 'staged' or stage_type == 'unstaged':
			# 差分表示
			original = self.runGit(['show', f'HEAD:{file_path}'], False) or ""
			
			try:
				with open(full_path, 'r', encoding='utf-8') as f:
					current = f.read()
			except:
				current = ""
			
			self.win.newdiffviewer(original, current, title=f"Diff: {os.path.basename(file_path)}")
		else:
			# ファイルを開く
			if os.path.exists(full_path):
				if full_path not in self.win.tabfilelist:
					self.win.open_(full_path)
				else:
					idx = self.win.tabfilelist.index(full_path)
					self.win.tabs.setCurrentIndex(idx)
	
	def on_stage_toggle(self, file_path, action):
		"""ステージ切替"""
		if action == 'stage':
			self.runGit(['add', file_path])
			self.status_bar.setText(f"+ {os.path.basename(file_path)}")
		else:
			self.runGit(['reset', 'HEAD', file_path])
			self.status_bar.setText(f"− {os.path.basename(file_path)}")
		
		self.refresh()
	
	def commit(self):
		"""コミット"""
		msg = self.commit_input.toPlainText().strip()
		if not msg:
			self.status_bar.setText("⚠ メッセージを入力してください")
			return
		
		if not self.staged_files:
			self.status_bar.setText("⚠ ステージされた変更がありません")
			return
		
		result = self.runGit(['commit', '-m', msg])
		if result:
			self.commit_input.clear()
			self.status_bar.setText(f"✓ コミット完了")
			self.refresh()
	
	def show_branch_menu(self):
		"""ブランチメニュー"""
		menu = QMenu(self)
		menu.setStyleSheet("""
			QMenu {
				background: #252526;
				color: #CCCCCC;
				border: 1px solid #3E3E42;
			}
			QMenu::item:selected {
				background: #2A2D2E;
			}
		""")
		
		for branch in self.branches:
			action = menu.addAction(f"{'✓ ' if branch == self.current_branch else '  '}{branch}")
			action.triggered.connect(lambda checked, b=branch: self.switch_branch(b))
		
		menu.addSeparator()
		new_action = menu.addAction("+ 新しいブランチ...")
		new_action.triggered.connect(self.create_branch)
		
		menu.exec_(self.branch_widget.mapToGlobal(self.branch_widget.rect().bottomLeft()))
	
	def switch_branch(self, branch):
		"""ブランチ切替"""
		if branch == self.current_branch:
			return
		
		reply = QMessageBox.question(
			self, 'ブランチ切替',
			f'"{branch}" に切り替えますか？',
			QMessageBox.Yes | QMessageBox.No
		)
		
		if reply == QMessageBox.Yes:
			result = self.runGit(['checkout', branch])
			if result is not None:
				self.status_bar.setText(f"⎇ {branch} に切替")
				self.refresh()
	
	def create_branch(self):
		"""ブランチ作成"""
		name, ok = QInputDialog.getText(self, '新しいブランチ', 'ブランチ名:')
		if ok and name:
			result = self.runGit(['checkout', '-b', name])
			if result is not None:
				self.status_bar.setText(f"+ {name} を作成")
				self.refresh()
	
	def show_more_menu(self):
		"""その他メニュー"""
		menu = QMenu(self)
		menu.setStyleSheet("""
			QMenu {
				background: #252526;
				color: #CCCCCC;
				border: 1px solid #3E3E42;
			}
			QMenu::item:selected {
				background: #2A2D2E;
			}
		""")
		
		pull_action = menu.addAction("↓ Pull")
		pull_action.triggered.connect(self.git_pull)
		
		push_action = menu.addAction("↑ Push")
		push_action.triggered.connect(self.git_push)
		
		fetch_action = menu.addAction("⟳ Fetch")
		fetch_action.triggered.connect(self.git_fetch)
		
		menu.addSeparator()
		
		stage_all_action = menu.addAction("+ すべてステージ")
		stage_all_action.triggered.connect(self.stage_all)
		
		unstage_all_action = menu.addAction("− すべてアンステージ")
		unstage_all_action.triggered.connect(self.unstage_all)
		
		menu.exec_(self.commit_btn.mapToGlobal(self.commit_btn.rect().bottomRight()))
	
	def git_pull(self):
		"""Pull"""
		self.status_bar.setText("↓ Pull中...")
		result = self.runGit(['pull'])
		if result:
			self.status_bar.setText("✓ Pull完了")
			self.refresh()
	
	def git_push(self):
		"""Push"""
		self.status_bar.setText("↑ Push中...")
		result = self.runGit(['push'])
		if result:
			self.status_bar.setText("✓ Push完了")
	
	def git_fetch(self):
		"""Fetch"""
		self.status_bar.setText("⟳ Fetch中...")
		result = self.runGit(['fetch'])
		if result:
			self.status_bar.setText("✓ Fetch完了")
			self.refresh()
	
	def stage_all(self):
		"""すべてステージ"""
		self.runGit(['add', '-A'])
		self.status_bar.setText("+ すべてステージ")
		self.refresh()
	
	def unstage_all(self):
		"""すべてアンステージ"""
		self.runGit(['reset', 'HEAD'])
		self.status_bar.setText("− すべてアンステージ")
		self.refresh()
