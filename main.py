import sys, os, json
from PySide6.QtWidgets import *
from PySide6.QtGui import QFont, QAction, QTextOption, QFontMetrics
from PySide6.QtCore import Qt, QDir, QFileInfo, QSettings
from terminal import Terminal
from syntaxhighlight import PygmentsSyntaxHighlight

embedded_python = "python\\python.exe"
STYLE = "themes/onedarkpro"
with open(f"{STYLE}.json", "r", encoding="utf-8") as f:
	STYLE = json.load(f)
if not "theme" in STYLE:
	STYLE["theme"] = "themes/monokai.css"
class Window(QMainWindow):
	def __init__(self):
		super().__init__()
		self.setStyleSheet(open(STYLE["theme"], "r", encoding="utf-8").read())
		self.setWindowTitle(f"PyCode2")
		self.resize(800, 600)
		
		self.FONT = QFont("Consolas", 11)

		self.main_widget = QWidget()
		self.setCentralWidget(self.main_widget)
		self.main_layout = QVBoxLayout(self.main_widget)
		self.main_layout.setContentsMargins(2, 2, 2, 2)

		vertical_splitter = QSplitter(Qt.Vertical)
		horizontal_splitter = QSplitter(Qt.Horizontal)

		# -----------------------------------------------------------
		# 🔹 ファイルツリー部
		# -----------------------------------------------------------
		self.model = QFileSystemModel()
		self.model.setRootPath(QDir.currentPath())
		self.tree = QTreeView()
		self.tree.setModel(self.model)
		self.tree.setRootIndex(self.model.index(QDir.currentPath()))
		for column in range(1, self.tree.model().columnCount()):
			self.tree.hideColumn(column)
		self.tree.setColumnWidth(0, 200)
		self.tree.setHeaderHidden(True)
		self.tree.clicked.connect(self.open_file_from_tree)
		# -----------------------------------------------------------
		# 🔸 テキストエディタ部
		# -----------------------------------------------------------
		self.tabs = QTabWidget()
		self.tabs.setTabsClosable(True)
		self.tabs.tabCloseRequested.connect(self.close_tab)

		self.tablist = []
		self.tabfilelist = []
		self.newtab(name="Untitled")
		# -----------------------------------------------------------
		# 🔻 下：コンソール・出力ビュー
		# -----------------------------------------------------------
		self.console = Terminal()
		# -----------------------------------------------------------
		# スプリッター
		# -----------------------------------------------------------
		vertical_splitter.addWidget(self.tabs)
		vertical_splitter.addWidget(self.console)
		vertical_splitter.setStretchFactor(0, 3)
		vertical_splitter.setStretchFactor(1, 1)

		horizontal_splitter.addWidget(self.tree)
		horizontal_splitter.addWidget(vertical_splitter)
		horizontal_splitter.setStretchFactor(0, 1)
		horizontal_splitter.setStretchFactor(1, 4)

		self.main_layout.addWidget(horizontal_splitter)

		self.create_menu_bar()
		self.create_status_bar()

	def create_menu_bar(self):
		menubar = self.menuBar()

		#--------------------------------------------------------
		# メニュー項目のフォントを設定
		file_menu = menubar.addMenu("ファイル(&F)")
		file_menu.setFont(self.FONT)

		new_action = QAction("新しいテキストファイル", self)
		new_action.setFont(self.FONT)
		new_action.setShortcut("Ctrl+N")
		new_action.triggered.connect(lambda: self.newtab(name="Untitled"))
		
		open_action = QAction("ファイルを開く...", self)
		open_action.setFont(self.FONT)
		open_action.setShortcut("Ctrl+O")
		open_action.triggered.connect(self.open_file)
		
		open_folder_action = QAction("フォルダーを開く...", self)
		open_folder_action.setShortcut("Ctrl+K")
		open_folder_action.triggered.connect(self.open_folder)

		save_action = QAction("保存", self)
		save_action.setShortcut("Ctrl+S")
		save_action.triggered.connect(self.save_file)
		
		save_as_action = QAction("名前を付けて保存", self)
		save_as_action.setShortcut("Ctrl+Shift+S")
		save_as_action.triggered.connect(self.save_file_as)
		
		file_menu.addAction(new_action)
		file_menu.addAction(open_action)
		file_menu.addAction(open_folder_action)
		file_menu.addSeparator()
		file_menu.addAction(save_action)
		file_menu.addAction(save_as_action)
		file_menu.addSeparator()
		
		close_action = QAction("タブを閉じる", self)
		close_action.triggered.connect(lambda: self.close_tab(self.tabs.currentIndex()))
		file_menu.addAction(close_action)

		close_all_action = QAction("すべてのタブを閉じる", self)
		close_all_action.triggered.connect(lambda: [self.close_tab(i) for i in reversed(range(self.tabs.count()))])
		file_menu.addAction(close_all_action)

		exit_action = QAction("終了", self)
		exit_action.triggered.connect(self.close)
		file_menu.addAction(exit_action)
		#--------------------------------------------------------
		edit_menu = menubar.addMenu("編集(&E)")
		edit_menu.setFont(self.FONT)

		undo_action = QAction("元に戻す", self)
		undo_action.setFont(self.FONT)
		undo_action.setShortcut("Ctrl+Z")
		undo_action.triggered.connect(lambda: self.tablist[self.tabs.currentIndex()].undo())

		redo_action = QAction("やり直す", self)
		redo_action.setFont(self.FONT)
		redo_action.setShortcut("Ctrl+Y")
		redo_action.triggered.connect(lambda: self.tablist[self.tabs.currentIndex()].redo())

		edit_menu.addAction(undo_action)
		edit_menu.addAction(redo_action)
		edit_menu.addSeparator()

		cut_action = QAction("切り取り", self)
		cut_action.setShortcut("Ctrl+X")
		cut_action.triggered.connect(lambda: self.tablist[self.tabs.currentIndex()].cut())

		copy_action = QAction("コピー", self)
		copy_action.setShortcut("Ctrl+C")
		copy_action.triggered.connect(lambda: self.tablist[self.tabs.currentIndex()].copy())

		paste_action = QAction("貼り付け", self)
		paste_action.setShortcut("Ctrl+V")
		paste_action.triggered.connect(lambda: self.tablist[self.tabs.currentIndex()].paste())

		edit_menu.addAction(cut_action)
		edit_menu.addAction(copy_action)
		edit_menu.addAction(paste_action)
		#--------------------------------------------------------
		run_menu = menubar.addMenu("実行(&R)")
		run_menu.setFont(self.FONT)

		run_action = QAction("デバッグなしで実行", self)
		run_action.setShortcut("F5")
		run_action.triggered.connect(self.run_code)
		run_menu.addAction(run_action)

	def create_status_bar(self):
		status_bar = self.statusBar()
		status_bar.setFont(self.FONT)

		self.permanent_message = QLabel()
		self.permanent_message.setFont(self.FONT)
		self.permanent_message.setText("Coming Soon")
		
		status_bar.addPermanentWidget(self.permanent_message)

		status_bar.messageChanged.connect(self.on_status_message_changed)

	def newtab(self, name=None, path=None):#新しいテキストファイル
		if path is not None:
			name = QFileInfo(path).fileName()
			self.tabfilelist.append(path)
		else:
			self.tabfilelist.append(None)
		self.tablist.append(QPlainTextEdit())
		self.tablist[-1].setFont(self.FONT)
		
		options = QTextOption()
		options.setTabStopDistance(QFontMetrics(self.tablist[-1].font()).horizontalAdvance(' ') * 4)
		PygmentsSyntaxHighlight(parent=self.tablist[-1].document(), filename=name, style=STYLE["highlight"])
		self.tablist[-1].document().setDefaultTextOption(options)
		
		self.tabs.addTab(self.tablist[-1], name)
		self.tabs.setCurrentIndex(len(self.tablist) - 1)

	def open_(self, file_path):
		try:
			with open(file_path, 'r', encoding='utf-8') as file:
				content = file.read()
				self.newtab(path=file_path)
				current_tab = self.tablist[-1]
				current_tab.setPlainText(content)
				current_tab.file_path = file_path
		except UnicodeDecodeError:
			QMessageBox.warning(self, "警告", "このファイルはテキストファイルではないか、対応していないエンコーディングです。")
		except Exception as e:
			QMessageBox.critical(self, "エラー", f"ファイルを開けませんでした: {str(e)}")

	def open_file(self):#ファイルを開く
		file_paths, _ = QFileDialog.getOpenFileNames(self, "ファイルを開く", "", "All Files (*.*)")
		for file_path in file_paths:
			if file_path in self.tabfilelist:
				tab_index = self.tabfilelist.index(file_path)
				self.tabs.setCurrentIndex(tab_index)
				continue
			self.open_(file_path)

	def open_folder(self):#フォルダーを開く
		folder_path = QFileDialog.getExistingDirectory(self, "フォルダーを開く", "")
		if folder_path:
			self.tree.setRootIndex(self.model.index(folder_path))
			self.console.end_terminal()
			os.chdir(folder_path)
			self.console.start_terminal()

	def save_file(self):#保存
		current_tab = self.tablist[self.tabs.currentIndex()]
		if not hasattr(current_tab, 'file_path'):
			self.save_file_as()
		else:
			try:
				with open(current_tab.file_path, 'w', encoding='utf-8') as file:
					file.write(current_tab.toPlainText())
			except Exception as e:
				QMessageBox.critical(self, "エラー", f"ファイルの保存に失敗しました: {str(e)}")

	def save_file_as(self):#名前を付けて保存
		current_tab = self.tablist[self.tabs.currentIndex()]
		file_path, _ = QFileDialog.getSaveFileName(self, "名前を付けて保存", "", "All Files (*.*)")
		if file_path:
			try:
				with open(file_path, 'w', encoding='utf-8') as file:
					file.write(current_tab.toPlainText())
				current_tab.file_path = file_path
				self.tabs.setTabText(self.tabs.currentIndex(), QFileInfo(file_path).fileName())
			except Exception as e:
				QMessageBox.critical(self, "エラー", f"ファイルの保存に失敗しました: {str(e)}")

	def close_tab(self, index):#タブを閉じる
		if self.maybe_save(index):
			self.tabs.removeTab(index)
			self.tablist.pop(index)
			self.tabfilelist.pop(index)

	def maybe_save(self, index):#変更の保存確認
		current_tab = self.tablist[index]
		if hasattr(current_tab, 'file_path'):
			with open(current_tab.file_path, 'r', encoding='utf-8') as file:
				content = file.read()
			if content == current_tab.toPlainText():
				return True
		if not current_tab.document().isModified():
			return True
		
		ret = QMessageBox.warning(self, f"PyCode2",
								f"ドキュメント'{QFileInfo(current_tab.file_path).fileName() if hasattr(current_tab, 'file_path') else 'Untitled'}'が変更されています。\n保存しますか？",
								QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)

		if ret == QMessageBox.Save:
			self.save_file()
		elif ret == QMessageBox.Cancel:
			return False
		return True

	def run_command(self, command):
		self.console.insertPlainText(command)
		self.console.run_command()

	def run_code(self):#実行
		current_tab = self.tablist[self.tabs.currentIndex()]
		if not hasattr(current_tab, 'file_path'):
			self.run_command("echo TEST COMMAND")
			return
		if os.path.splitext(current_tab.file_path)[-1] == ".py":
			self.run_command(f"{embedded_python} {current_tab.file_path}")

	def open_file_from_tree(self, index):#ファイルツリーから開く(クリック)
		file_path = self.model.filePath(index)
		if file_path in self.tabfilelist:
			tab_index = self.tabfilelist.index(file_path)
			self.tabs.setCurrentIndex(tab_index)
			return
		if QFileInfo(file_path).isFile():
			self.open_(file_path)

	def on_status_message_changed(self, message):#一時的なステータスメッセージが変更された時のハンドラ
		if not message:
			self.statusBar().showMessage("Ready")

	def closeEvent(self, event):#終了前処理など
		can_close = True
		for i in range(len(self.tablist)):
			if not self.maybe_save(i):
				can_close = False
				break
		if can_close:
			#終了前処理はここ
			event.accept()
		else:
			event.ignore()

if __name__=="__main__":
	app = QApplication(sys.argv)
	window = Window()
	window.showMaximized()
	sys.exit(app.exec()) 