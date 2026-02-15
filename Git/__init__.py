from addons.AddonBase import ActivityBar, SideBar
from PySide6.QtWidgets import *
from PySide6.QtGui import QIcon, Qt, QColor, QFont, QPainter, QShortcut, QKeySequence
from PySide6.QtCore import QTimer, QDir, Signal, QSize
from Git.common import (
	get_status_icon, get_status_color, get_status_label,
	run_git, GitRunner, parse_ahead_behind,
)
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
_ICON_BTN = """
	QPushButton {
		background: transparent; border: none;
		color: #CCCCCC; font-size: %dpx;
	}
	QPushButton:hover { background: #2A2D2E; border-radius: 3px; }
"""
_SMALL_BTN = """
	QPushButton {
		background: transparent; border: 1px solid #3E3E42;
		border-radius: 3px; color: #CCCCCC; font-weight: bold;
	}
	QPushButton:hover { background: #2D2D30; border-color: #007ACC; }
"""
_SMALL_BTN_DANGER = """
	QPushButton {
		background: transparent; border: 1px solid #3E3E42;
		border-radius: 3px; color: #CCCCCC; font-weight: bold;
	}
	QPushButton:hover { background: #2D2D30; border-color: #E06C75; }
"""


class FileChangeItem(QWidget):
	"""ファイル変更アイテム（ステージ/アンステージ/破棄ボタン付き）"""
	clicked = Signal(str, str)
	stageToggled = Signal(str, str)
	discardRequested = Signal(str)

	def __init__(self, file_path, status, stage_type, parent=None):
		super().__init__(parent)
		self.file_path = file_path
		self.status = status
		self.stage_type = stage_type
		self.setContextMenuPolicy(Qt.CustomContextMenu)
		self.customContextMenuRequested.connect(self._context_menu)

		layout = QHBoxLayout()
		layout.setContentsMargins(8, 4, 8, 4)
		layout.setSpacing(6)

		# ステータスアイコン
		icon_lbl = QLabel(get_status_icon(status))
		icon_lbl.setFont(QFont("Segoe UI", 10))
		icon_lbl.setFixedWidth(20)
		icon_lbl.setToolTip(get_status_label(status))
		layout.addWidget(icon_lbl)

		# ファイル名
		name_lbl = QLabel(os.path.basename(file_path))
		name_lbl.setFont(QFont("Segoe UI", 9))
		name_lbl.setStyleSheet(f"color: {get_status_color(status)};")
		name_lbl.setToolTip(file_path)
		layout.addWidget(name_lbl, 1)

		# ディレクトリ表示
		dirname = os.path.dirname(file_path)
		if dirname:
			dir_lbl = QLabel(dirname)
			dir_lbl.setFont(QFont("Segoe UI", 8))
			dir_lbl.setStyleSheet("color: #858585;")
			layout.addWidget(dir_lbl)

		# アクションボタン（ホバーで表示）
		self._btns = QWidget()
		btn_layout = QHBoxLayout()
		btn_layout.setContentsMargins(0, 0, 0, 0)
		btn_layout.setSpacing(2)

		if stage_type == 'staged':
			unstage = QPushButton("−")
			unstage.setFixedSize(20, 20)
			unstage.setToolTip("アンステージ")
			unstage.setStyleSheet(_SMALL_BTN_DANGER)
			unstage.clicked.connect(lambda: self.stageToggled.emit(file_path, 'unstage'))
			btn_layout.addWidget(unstage)
		else:
			# 破棄ボタン
			if stage_type == 'unstaged':
				discard = QPushButton("↺")
				discard.setFixedSize(20, 20)
				discard.setToolTip("変更を破棄")
				discard.setStyleSheet(_SMALL_BTN_DANGER)
				discard.clicked.connect(lambda: self.discardRequested.emit(file_path))
				btn_layout.addWidget(discard)
			# ステージボタン
			stage = QPushButton("+")
			stage.setFixedSize(20, 20)
			stage.setToolTip("ステージに追加")
			stage.setStyleSheet(_SMALL_BTN)
			stage.clicked.connect(lambda: self.stageToggled.emit(file_path, 'stage'))
			btn_layout.addWidget(stage)

		self._btns.setLayout(btn_layout)
		self._btns.hide()
		layout.addWidget(self._btns)

		self.setLayout(layout)

	def enterEvent(self, event):
		self._btns.show()
		self.setStyleSheet("background: #2A2D2E;")

	def leaveEvent(self, event):
		self._btns.hide()
		self.setStyleSheet("")

	def mousePressEvent(self, event):
		if event.button() == Qt.LeftButton:
			self.clicked.emit(self.file_path, self.stage_type)

	def _context_menu(self, pos):
		menu = QMenu(self)
		menu.setStyleSheet(_MENU_STYLE)
		if self.stage_type == 'staged':
			menu.addAction("アンステージ", lambda: self.stageToggled.emit(self.file_path, 'unstage'))
		else:
			menu.addAction("ステージ", lambda: self.stageToggled.emit(self.file_path, 'stage'))
			if self.stage_type == 'unstaged':
				menu.addAction("変更を破棄", lambda: self.discardRequested.emit(self.file_path))
		menu.addSeparator()
		menu.addAction("パスをコピー", lambda: QApplication.clipboard().setText(self.file_path))
		menu.exec_(self.mapToGlobal(pos))


# ─── セクションヘッダー ──────────────────────────────────
class _SectionHeader(QWidget):
	"""折りたたみ可能なセクションヘッダー"""
	toggleAll = Signal(str)  # 'stage_all' or 'unstage_all'

	def __init__(self, title, count, section_type, parent=None):
		super().__init__(parent)
		self.section_type = section_type
		self._collapsed = False

		layout = QHBoxLayout()
		layout.setContentsMargins(8, 6, 8, 6)
		layout.setSpacing(6)

		self._arrow = QLabel("▼")
		self._arrow.setFixedWidth(14)
		self._arrow.setStyleSheet("color: #858585; font-size: 9px;")
		layout.addWidget(self._arrow)

		lbl = QLabel(f"{title} ({count})")
		lbl.setFont(QFont("Segoe UI", 9, QFont.Bold))
		lbl.setStyleSheet("color: #CCCCCC;")
		layout.addWidget(lbl, 1)

		# 一括ボタン
		action = "unstage_all" if section_type == "staged" else "stage_all"
		btn_text = "−" if section_type == "staged" else "+"
		tip = "すべてアンステージ" if section_type == "staged" else "すべてステージ"
		btn = QPushButton(btn_text)
		btn.setFixedSize(20, 20)
		btn.setToolTip(tip)
		btn.setStyleSheet(_SMALL_BTN)
		btn.clicked.connect(lambda: self.toggleAll.emit(action))
		layout.addWidget(btn)

		self.setLayout(layout)
		self.setStyleSheet("background: #252526;")
		self.items_widget = None

	def mousePressEvent(self, event):
		if event.button() == Qt.LeftButton:
			self._collapsed = not self._collapsed
			self._arrow.setText("▶" if self._collapsed else "▼")
			if self.items_widget:
				self.items_widget.setVisible(not self._collapsed)


class Button(ActivityBar):
	def __init__(self, window=None):
		super().__init__()
		self.win = window

	def button(self):
		return super().button(name="git_btn", icon_path=f"{self.win.DIR}/assets/git.svg")


class Main(SideBar):
	def __init__(self, window=None, index=2):
		super().__init__()
		self.name = "Git"
		self.description = "Git Source Control"
		self.version = "2.0.0"

		self.win = window
		self.index = index
		self._connected = False
		self._amend = False
		self._last_hash = ""  # 変更検知用

		# 非同期ランナー
		self._runner = GitRunner(self)
		self._runner.taskFinished.connect(self._on_task_finished)
		self._runner.taskError.connect(self._on_task_error)

		layout = QVBoxLayout()
		layout.setContentsMargins(0, 0, 0, 0)
		layout.setSpacing(0)

		# ═══ ヘッダー ═══
		header = QWidget()
		header.setStyleSheet("background: #252526; border-bottom: 1px solid #3E3E42;")
		header_layout = QVBoxLayout()
		header_layout.setContentsMargins(12, 8, 12, 8)
		header_layout.setSpacing(6)

		# タイトル行
		title_row = QHBoxLayout()
		title = QLabel("ソース管理")
		title.setFont(QFont("Segoe UI", 11, QFont.Bold))
		title.setStyleSheet("color: #CCCCCC;")
		title_row.addWidget(title)
		title_row.addStretch()

		for icon, tip, slot in [("⟳", "更新", self.refresh)]:
			btn = QPushButton(icon)
			btn.setFixedSize(24, 24)
			btn.setToolTip(tip)
			btn.setStyleSheet(_ICON_BTN % 14)
			btn.clicked.connect(slot)
			title_row.addWidget(btn)
		header_layout.addLayout(title_row)

		# ブランチ + sync 状態
		branch_row = QHBoxLayout()
		branch_row.setSpacing(6)
		branch_icon = QLabel("⎇")
		branch_icon.setStyleSheet("color: #C678DD; font-size: 14px;")
		branch_row.addWidget(branch_icon)

		self.branch_label = QLabel("—")
		self.branch_label.setFont(QFont("Segoe UI", 9))
		self.branch_label.setStyleSheet("color: #C678DD;")
		branch_row.addWidget(self.branch_label)

		self.sync_label = QLabel("")
		self.sync_label.setFont(QFont("Segoe UI", 8))
		self.sync_label.setStyleSheet("color: #858585;")
		branch_row.addWidget(self.sync_label)
		branch_row.addStretch()

		self.branch_widget = QWidget()
		switch_btn = QPushButton("切替")
		switch_btn.setFixedHeight(22)
		switch_btn.setStyleSheet("""
			QPushButton {
				background: transparent; border: 1px solid #3E3E42;
				border-radius: 3px; color: #CCCCCC; padding: 2px 8px; font-size: 8px;
			}
			QPushButton:hover { background: #2A2D2E; border-color: #007ACC; }
		""")
		switch_btn.clicked.connect(self.show_branch_menu)
		branch_row.addWidget(switch_btn)

		self.branch_widget.setLayout(branch_row)
		header_layout.addWidget(self.branch_widget)
		header.setLayout(header_layout)
		layout.addWidget(header)

		# ═══ コミットセクション ═══
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
				background: #252526; color: #CCCCCC;
				border: 1px solid #3E3E42; border-radius: 3px; padding: 6px;
			}
			QTextEdit:focus { border-color: #007ACC; }
		""")
		commit_layout.addWidget(self.commit_input)

		# Amend チェックボックス
		self.amend_cb = QCheckBox("Amend (直前のコミットを修正)")
		self.amend_cb.setFont(QFont("Segoe UI", 8))
		self.amend_cb.setStyleSheet("color: #858585;")
		self.amend_cb.toggled.connect(self._on_amend_toggled)
		commit_layout.addWidget(self.amend_cb)

		# ボタン行
		btn_row = QHBoxLayout()
		btn_row.setSpacing(6)

		self.commit_btn = QPushButton("✓ コミット")
		self.commit_btn.setFixedHeight(28)
		self.commit_btn.setStyleSheet("""
			QPushButton {
				background: #007ACC; color: white; border: none;
				border-radius: 3px; padding: 4px 12px; font-weight: bold;
			}
			QPushButton:hover { background: #0098FF; }
			QPushButton:pressed { background: #005A9E; }
			QPushButton:disabled { background: #3E3E42; color: #6E6E6E; }
		""")
		self.commit_btn.clicked.connect(self.commit)
		btn_row.addWidget(self.commit_btn, 2)

		more_btn = QPushButton("⋯")
		more_btn.setFixedSize(28, 28)
		more_btn.setToolTip("その他の操作")
		more_btn.setStyleSheet("""
			QPushButton {
				background: transparent; border: 1px solid #3E3E42;
				border-radius: 3px; color: #CCCCCC;
			}
			QPushButton:hover { background: #2A2D2E; border-color: #007ACC; }
		""")
		more_btn.clicked.connect(self.show_more_menu)
		btn_row.addWidget(more_btn)

		commit_layout.addLayout(btn_row)
		commit_section.setLayout(commit_layout)
		layout.addWidget(commit_section)

		# ═══ 変更リスト ═══
		scroll = QScrollArea()
		scroll.setWidgetResizable(True)
		scroll.setStyleSheet("""
			QScrollArea { border: none; background: #1E1E1E; }
			QScrollBar:vertical { background: #1E1E1E; width: 10px; }
			QScrollBar::handle:vertical { background: #424242; border-radius: 5px; }
			QScrollBar::handle:vertical:hover { background: #4E4E4E; }
		""")
		scroll_content = QWidget()
		self.changes_layout = QVBoxLayout()
		self.changes_layout.setContentsMargins(0, 0, 0, 0)
		self.changes_layout.setSpacing(0)
		scroll_content.setLayout(self.changes_layout)
		scroll.setWidget(scroll_content)
		layout.addWidget(scroll, 1)

		# ═══ ステータスバー ═══
		self.status_bar = QLabel("準備完了")
		self.status_bar.setFont(QFont("Segoe UI", 8))
		self.status_bar.setStyleSheet("background: #007ACC; color: white; padding: 4px 12px;")
		layout.addWidget(self.status_bar)

		self.setLayout(layout)

		# Ctrl+Enter ショートカット
		shortcut = QShortcut(QKeySequence("Ctrl+Return"), self.commit_input)
		shortcut.activated.connect(self.commit)

		# データ
		self.staged_files = []
		self.unstaged_files = []
		self.untracked_files = []
		self.branches = []
		self.current_branch = ""

		# 自動更新タイマー
		self.timer = QTimer()
		self.timer.timeout.connect(self._smart_refresh)

	# ─── ライフサイクル ───────────────────────────────────
	def showEvent(self, event):
		if not self._connected:
			self.refresh()
			self.timer.start(3000)
			self._connected = True
		return super().showEvent(event)

	def hideEvent(self, event):
		self.timer.stop()
		return super().hideEvent(event)

	# ─── Git操作ヘルパー ──────────────────────────────────
	def runGit(self, args, show_error=True):
		callback = (lambda msg: self.status_bar.setText(msg)) if show_error else None
		return run_git(args, show_error=show_error, error_callback=callback)

	def _runAsync(self, task, args):
		self._runner.run(task, args)

	def _on_task_finished(self, task, result):
		handlers = {
			'pull':  lambda r: (self.status_bar.setText("✓ Pull完了"), self.refresh()),
			'push':  lambda r: self.status_bar.setText("✓ Push完了"),
			'fetch': lambda r: (self.status_bar.setText("✓ Fetch完了"), self.refresh()),
		}
		if task in handlers:
			handlers[task](result)

	def _on_task_error(self, task, msg):
		self.status_bar.setText(f"⚠ {task}: {msg[:60]}")

	# ─── リフレッシュ ─────────────────────────────────────
	def _smart_refresh(self):
		"""変更があった場合のみUIを更新"""
		h = self.runGit(['rev-parse', 'HEAD'], False) or ""
		status = self.runGit(['status', '--porcelain'], False) or ""
		current_hash = h + "|" + status
		if current_hash != self._last_hash:
			self._last_hash = current_hash
			self.refresh()

	def refresh(self):
		"""状態を取得してUIを更新"""
		branch = self.runGit(['branch', '--show-current'], False)
		if not branch:
			self.status_bar.setText("⚠ Gitリポジトリではありません")
			return

		self.current_branch = branch
		self.branch_label.setText(branch)

		# Ahead / Behind
		ab_output = self.runGit(
			['rev-list', '--left-right', '--count', f'{branch}...origin/{branch}'], False
		)
		if ab_output:
			parts = ab_output.split('\t')
			ahead = int(parts[0]) if len(parts) > 0 and parts[0].isdigit() else 0
			behind = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
			sync_parts = []
			if ahead:
				sync_parts.append(f"↑{ahead}")
			if behind:
				sync_parts.append(f"↓{behind}")
			self.sync_label.setText("  ".join(sync_parts))
		else:
			self.sync_label.setText("")

		# ブランチ一覧
		branches_output = self.runGit(['branch'], False)
		if branches_output:
			self.branches = [b.strip().lstrip('* ') for b in branches_output.split('\n') if b.strip()]

		# ステージ済み
		self.staged_files = []
		staged = self.runGit(['diff', '--name-status', '--cached'], False)
		if staged:
			for line in staged.split('\n'):
				if line:
					parts = line.split('\t', 1)
					if len(parts) >= 2:
						self.staged_files.append((parts[1], parts[0]))

		# 未ステージ
		self.unstaged_files = []
		unstaged = self.runGit(['diff', '--name-status'], False)
		if unstaged:
			for line in unstaged.split('\n'):
				if line:
					parts = line.split('\t', 1)
					if len(parts) >= 2:
						self.unstaged_files.append((parts[1], parts[0]))

		# 未追跡
		self.untracked_files = []
		untracked = self.runGit(['ls-files', '--others', '--exclude-standard'], False)
		if untracked:
			self.untracked_files = [(f, 'U') for f in untracked.split('\n') if f]

		self._rebuild_list()
		total = len(self.staged_files) + len(self.unstaged_files) + len(self.untracked_files)
		self.status_bar.setText(f"✓ {total} 件の変更")

	# ─── 変更リスト構築 ───────────────────────────────────
	def _rebuild_list(self):
		"""変更リストを再構築"""
		while self.changes_layout.count():
			item = self.changes_layout.takeAt(0)
			if item.widget():
				item.widget().deleteLater()

		# ステージ済み
		if self.staged_files:
			hdr = _SectionHeader("ステージ済みの変更", len(self.staged_files), "staged")
			hdr.toggleAll.connect(self._on_toggle_all)
			self.changes_layout.addWidget(hdr)
			container = QWidget()
			cl = QVBoxLayout()
			cl.setContentsMargins(0, 0, 0, 0)
			cl.setSpacing(0)
			for fp, st in self.staged_files:
				item = FileChangeItem(fp, st, 'staged')
				item.clicked.connect(self.on_file_clicked)
				item.stageToggled.connect(self.on_stage_toggle)
				cl.addWidget(item)
			container.setLayout(cl)
			hdr.items_widget = container
			self.changes_layout.addWidget(container)

		# 変更 + 未追跡
		changes = self.unstaged_files + self.untracked_files
		if changes:
			hdr = _SectionHeader("変更", len(changes), "unstaged")
			hdr.toggleAll.connect(self._on_toggle_all)
			self.changes_layout.addWidget(hdr)
			container = QWidget()
			cl = QVBoxLayout()
			cl.setContentsMargins(0, 0, 0, 0)
			cl.setSpacing(0)
			for fp, st in changes:
				stype = 'untracked' if st == 'U' else 'unstaged'
				item = FileChangeItem(fp, st, stype)
				item.clicked.connect(self.on_file_clicked)
				item.stageToggled.connect(self.on_stage_toggle)
				item.discardRequested.connect(self._discard_file)
				cl.addWidget(item)
			container.setLayout(cl)
			hdr.items_widget = container
			self.changes_layout.addWidget(container)

		self.changes_layout.addStretch()
		self.commit_btn.setEnabled(len(self.staged_files) > 0)

	# ─── ファイル操作 ─────────────────────────────────────
	def on_file_clicked(self, file_path, stage_type):
		full = QDir.current().filePath(file_path)
		if stage_type in ('staged', 'unstaged'):
			original = self.runGit(['show', f'HEAD:{file_path}'], False) or ""
			try:
				with open(full, 'r', encoding='utf-8') as f:
					current = f.read()
			except Exception:
				current = ""
			self.win.newdiffviewer(original, current, title=f"Diff: {os.path.basename(file_path)}")
		else:
			if os.path.exists(full):
				if full not in self.win.tabfilelist:
					self.win.open_(full)
				else:
					self.win.tabs.setCurrentIndex(self.win.tabfilelist.index(full))

	def on_stage_toggle(self, file_path, action):
		if action == 'stage':
			self.runGit(['add', file_path])
			self.status_bar.setText(f"+ {os.path.basename(file_path)}")
		else:
			self.runGit(['reset', 'HEAD', file_path])
			self.status_bar.setText(f"− {os.path.basename(file_path)}")
		self.refresh()

	def _on_toggle_all(self, action):
		if action == 'stage_all':
			self.stage_all()
		else:
			self.unstage_all()

	def _discard_file(self, file_path):
		reply = QMessageBox.warning(
			self, '変更を破棄',
			f'"{os.path.basename(file_path)}" の変更を破棄しますか？\nこの操作は元に戻せません。',
			QMessageBox.Yes | QMessageBox.No, QMessageBox.No
		)
		if reply == QMessageBox.Yes:
			self.runGit(['checkout', '--', file_path])
			self.status_bar.setText(f"↺ {os.path.basename(file_path)} を破棄")
			self.refresh()

	# ─── コミット ─────────────────────────────────────────
	def _on_amend_toggled(self, checked):
		self._amend = checked
		if checked:
			last_msg = self.runGit(['log', '-1', '--format=%B'], False)
			if last_msg and not self.commit_input.toPlainText().strip():
				self.commit_input.setPlainText(last_msg)
			self.commit_btn.setText("✓ Amend")
		else:
			self.commit_btn.setText("✓ コミット")

	def commit(self):
		msg = self.commit_input.toPlainText().strip()
		if not msg:
			self.status_bar.setText("⚠ メッセージを入力してください")
			return
		if not self.staged_files and not self._amend:
			self.status_bar.setText("⚠ ステージされた変更がありません")
			return

		args = ['commit']
		if self._amend:
			args.append('--amend')
		args += ['-m', msg]

		result = self.runGit(args)
		if result is not None:
			self.commit_input.clear()
			self.amend_cb.setChecked(False)
			self.status_bar.setText("✓ コミット完了")
			self.refresh()

	# ─── ブランチ操作 ─────────────────────────────────────
	def show_branch_menu(self):
		menu = QMenu(self)
		menu.setStyleSheet(_MENU_STYLE)
		for branch in self.branches:
			prefix = "✓ " if branch == self.current_branch else "  "
			action = menu.addAction(f"{prefix}{branch}")
			action.triggered.connect(lambda c, b=branch: self.switch_branch(b))
		menu.addSeparator()
		menu.addAction("+ 新しいブランチ...", self.create_branch)
		menu.exec_(self.branch_widget.mapToGlobal(self.branch_widget.rect().bottomLeft()))

	def switch_branch(self, branch):
		if branch == self.current_branch:
			return
		reply = QMessageBox.question(
			self, 'ブランチ切替', f'"{branch}" に切り替えますか？',
			QMessageBox.Yes | QMessageBox.No
		)
		if reply == QMessageBox.Yes:
			result = self.runGit(['checkout', branch])
			if result is not None:
				self.status_bar.setText(f"⎇ {branch} に切替")
				self.refresh()

	def create_branch(self):
		name, ok = QInputDialog.getText(self, '新しいブランチ', 'ブランチ名:')
		if ok and name:
			result = self.runGit(['checkout', '-b', name])
			if result is not None:
				self.status_bar.setText(f"+ {name} を作成")
				self.refresh()

	# ─── その他メニュー ───────────────────────────────────
	def show_more_menu(self):
		menu = QMenu(self)
		menu.setStyleSheet(_MENU_STYLE)

		menu.addAction("↓ Pull", self.git_pull)
		menu.addAction("↑ Push", self.git_push)
		menu.addAction("⟳ Fetch", self.git_fetch)
		menu.addSeparator()
		menu.addAction("+ すべてステージ", self.stage_all)
		menu.addAction("− すべてアンステージ", self.unstage_all)
		menu.addAction("↺ すべて破棄", self.discard_all)
		menu.addSeparator()

		# スタッシュ
		stash_menu = menu.addMenu("📦 Stash")
		stash_menu.setStyleSheet(_MENU_STYLE)
		stash_menu.addAction("Stash (保存)", self.stash_save)
		stash_menu.addAction("Stash Pop (復元)", self.stash_pop)
		stash_menu.addAction("Stash List (一覧)", self.stash_list)

		menu.exec_(self.commit_btn.mapToGlobal(self.commit_btn.rect().bottomRight()))

	# ─── リモート操作 (非同期) ────────────────────────────
	def git_pull(self):
		self.status_bar.setText("↓ Pull中...")
		self._runAsync('pull', ['pull'])

	def git_push(self):
		self.status_bar.setText("↑ Push中...")
		self._runAsync('push', ['push'])

	def git_fetch(self):
		self.status_bar.setText("⟳ Fetch中...")
		self._runAsync('fetch', ['fetch'])

	# ─── ステージ一括 ────────────────────────────────────
	def stage_all(self):
		self.runGit(['add', '-A'])
		self.status_bar.setText("+ すべてステージ")
		self.refresh()

	def unstage_all(self):
		self.runGit(['reset', 'HEAD'])
		self.status_bar.setText("− すべてアンステージ")
		self.refresh()

	def discard_all(self):
		reply = QMessageBox.warning(
			self, 'すべて破棄',
			'すべての変更を破棄しますか？\nこの操作は元に戻せません。',
			QMessageBox.Yes | QMessageBox.No, QMessageBox.No
		)
		if reply == QMessageBox.Yes:
			self.runGit(['checkout', '--', '.'])
			# 未追跡ファイルも削除
			self.runGit(['clean', '-fd'])
			self.status_bar.setText("↺ すべて破棄")
			self.refresh()

	# ─── スタッシュ ──────────────────────────────────────
	def stash_save(self):
		msg, ok = QInputDialog.getText(self, 'Stash', 'メッセージ (省略可):')
		if ok:
			args = ['stash', 'push']
			if msg:
				args += ['-m', msg]
			result = self.runGit(args)
			if result is not None:
				self.status_bar.setText("📦 Stash保存")
				self.refresh()

	def stash_pop(self):
		result = self.runGit(['stash', 'pop'])
		if result is not None:
			self.status_bar.setText("📦 Stash復元")
			self.refresh()
		else:
			self.status_bar.setText("⚠ Stashが空です")

	def stash_list(self):
		output = self.runGit(['stash', 'list'], False)
		if not output:
			QMessageBox.information(self, 'Stash一覧', 'Stashは空です。')
			return
		menu = QMenu(self)
		menu.setStyleSheet(_MENU_STYLE)
		for line in output.split('\n'):
			if line.strip():
				entry = line.split(':')[0]  # stash@{0}
				action = menu.addAction(line.strip())
				action.triggered.connect(lambda c, e=entry: self._stash_apply(e))
		menu.addSeparator()
		menu.addAction("🗑 すべて削除", self._stash_clear)
		menu.exec_(self.mapToGlobal(self.rect().center()))

	def _stash_apply(self, entry):
		result = self.runGit(['stash', 'apply', entry])
		if result is not None:
			self.status_bar.setText(f"📦 {entry} を適用")
			self.refresh()

	def _stash_clear(self):
		reply = QMessageBox.warning(
			self, 'Stash削除', 'すべてのStashを削除しますか？',
			QMessageBox.Yes | QMessageBox.No, QMessageBox.No
		)
		if reply == QMessageBox.Yes:
			self.runGit(['stash', 'clear'])
			self.status_bar.setText("🗑 Stash全削除")
