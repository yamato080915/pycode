import sys, os, json, threading, time, subprocess
from pathlib import Path
from PySide6.QtWidgets import *
from PySide6.QtGui import QFont, QTextOption, QFontMetrics, QIcon
from PySide6.QtCore import Qt, QFileInfo, QDir, QSettings
from Highlight import Highlighter
from Editor import Editor
from DiffViewer import DiffViewer
from ActivityBar import ActivityBar
from SideBar import SideBar
from MenuBar import MenuBar
from TerminalGroup import TerminalGroup
from SecondarySideBar import SecondarySideBar
import platform
from AddonManager import AddonManager
from Color import css_color, icon_color
from pygments.lexers import guess_lexer

OS = platform.system()
DIR = os.getcwd()

if OS == "Windows":
	si = subprocess.STARTUPINFO()
	si.dwFlags = subprocess.STARTF_USESHOWWINDOW
	import ctypes
	ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('pycode2')
	embedded_python = f"{DIR}/python/python.exe"
else:
	embedded_python = f"python3"

def getpyversion():
	if OS == "Windows":
		PYV = subprocess.run([embedded_python, '-V'], capture_output=True, text=True, startupinfo=si)
	else:
		PYV = subprocess.run([embedded_python, '-V'], capture_output=True, text=True)
	return PYV.stdout.strip()
PYV = getpyversion()
STYLE = "onedarkpro"

def change_theme(theme_name):
	with open(f"{DIR}/themes/{theme_name}.json", "r", encoding="utf-8") as f:
		style = json.load(f)
	if not "style" in style:
		style["style"] = "themes/onedarkpro.css"
	style["style"] = f"{DIR}/{style["style"]}"
	color = css_color(style)
	for i in iter(p.name for p in Path(f"{DIR}/assets").iterdir() if p.is_file() and p.suffix.lower() == ".svg"):
		icon_color(f"{DIR}/assets/{i}", color)
	return style

STYLE = change_theme(STYLE)

class Window(QMainWindow):
	def __init__(self):
		super().__init__()
		self.STYLE = STYLE
		self.DIR = DIR
		
		self.settings = QSettings("PyCode", "PyCode2")
		
		self.setStyleSheet(open(STYLE["style"], "r", encoding="utf-8").read())
		self.setWindowTitle(f"PyCode2")
		
		if self.settings.contains("geometry"):
			self.restoreGeometry(self.settings.value("geometry"))
		else:
			self.resize(1600, 900)
		
		icon_path = f"{DIR}/assets/pycode.png"
		if os.path.exists(icon_path):
			self.setWindowIcon(QIcon(icon_path))
		
		self.FONT = QFont("Consolas", 11)

		self.addon_manager = AddonManager(self)

		self.main_widget = QWidget()
		self.setCentralWidget(self.main_widget)
		self.main_layout = QVBoxLayout(self.main_widget)
		self.main_layout.setContentsMargins(2, 2, 2, 2)

		vertical_splitter = QSplitter(Qt.Vertical)
		horizontal_splitter = QSplitter(Qt.Horizontal)

		# -----------------------------------------------------------
		# アクティビティバー
		# -----------------------------------------------------------
		self.activity_bar = ActivityBar(self, self.addon_manager.addons["ActivityBar"])
		self.sidebar = SideBar(self, self.addon_manager.addons["SideBar"])
		# -----------------------------------------------------------
		# テキストエディタ部
		# -----------------------------------------------------------
		self.tabs = QTabWidget()
		self.tabs.setTabsClosable(True)
		self.tabs.tabCloseRequested.connect(self.close_tab)

		self.tablist = []
		self.tabfilelist = []
		# -----------------------------------------------------------
		# 下：コンソール・出力ビュー
		# -----------------------------------------------------------
		self.ConsoleGroup = TerminalGroup(self)
		# -----------------------------------------------------------
		# 右：セカンダリサイドバー
		# -----------------------------------------------------------
		self.sec_sidebar = SecondarySideBar(self, self.addon_manager.addons["SecondarySideBar"])
		# -----------------------------------------------------------
		# スプリッター
		# -----------------------------------------------------------
		vertical_splitter.addWidget(self.tabs)
		vertical_splitter.addWidget(self.ConsoleGroup)
		vertical_splitter.setStretchFactor(0, 1)
		vertical_splitter.setStretchFactor(1, 0)
		vertical_splitter.setSizes([self.height() - 240, 240])
		
		horizontal_splitter.addWidget(self.activity_bar)
		horizontal_splitter.addWidget(self.sidebar)
		horizontal_splitter.addWidget(vertical_splitter)
		horizontal_splitter.addWidget(self.sec_sidebar)
		horizontal_splitter.setStretchFactor(0, 0)
		horizontal_splitter.setStretchFactor(1, 0)
		horizontal_splitter.setStretchFactor(2, 1)
		horizontal_splitter.setStretchFactor(3, 0)

		self.main_layout.addWidget(horizontal_splitter)
		
		self.vertical_splitter = vertical_splitter
		self.horizontal_splitter = horizontal_splitter

		self.load_settings()

		MenuBar(self)
		self.create_status_bar()
		
		self.newtab(name="Untitled")

	def create_status_bar(self):
		self.status_bar = self.statusBar()
		self.status_bar.setObjectName("status_bar")
		self.status_bar.setFont(self.FONT)

		self.permanent_message = QLabel()
		self.permanent_message.setFont(self.FONT)
		self.permanent_message.setContentsMargins(0,0,10,0)
		
		self.status_bar.addPermanentWidget(self.permanent_message)

		self.status_bar.messageChanged.connect(self.on_status_message_changed)
		threading.Thread(target=self.update_status, daemon=True).start()

	def update_status(self):
		self.running = False
		while True:
			try:
				disp_text = ""
				current_tab = self.tablist[self.tabs.currentIndex()]
				if not hasattr(current_tab, 'textCursor'):
					continue
				cursor = current_tab.textCursor()
				line = cursor.blockNumber() + 1
				column = cursor.columnNumber() + 1
				disp_text += f"Ln {line}, Col {column}"
				if cursor.hasSelection():
					selection_start = cursor.selectionStart()
					selection_end = cursor.selectionEnd()
					selection_length = selection_end - selection_start
					disp_text += f"(Sel {selection_length})"

				if hasattr(current_tab, 'file_path'):
					lang = str(current_tab.highlighter.lexer).lstrip("<pygments.lexers.").rstrip("Lexer>")
					disp_text += " | " + (f"{PYV}" if lang == "Python" else lang)
				
				self.permanent_message.setText(disp_text)
				
				flag = False
				if any((pid, name) for pid, name in self.ConsoleGroup.terminals[0].running):
					flag = True
				if flag and not self.running:
					bg_color = STYLE["theme"]["status_bar"]["running"]["background"]
					fg_color = STYLE["theme"]["status_bar"]["running"]["foreground"]
					self.status_bar.setStyleSheet(f"#status_bar {{ background-color: {bg_color};}}")
					self.permanent_message.setStyleSheet(f"color: {fg_color};")
				elif not flag and self.running:
					bg_color = STYLE["theme"]["status_bar"]["normal"]["background"]
					fg_color = STYLE["theme"]["status_bar"]["normal"]["foreground"]
					self.status_bar.setStyleSheet(f"#status_bar {{ background-color: {bg_color};}}")
					self.permanent_message.setStyleSheet(f"color: {fg_color};")
				self.running = flag
			except IndexError:
				pass
			except RuntimeError:
				pass
			except Exception as e:
				print("Status Bar Update Error:", e)
			finally:
				time.sleep(0.03)

	def newtab(self, name=None, path=None):#新しいテキストファイル
		if len(self.tabfilelist) == 1 and self.tabfilelist[0] == None and self.maybe_save(0):
			self.tabs.removeTab(0)
			self.tablist.pop(0)
			self.tabfilelist.pop(0)
		
		if path is not None:
			name = QFileInfo(path).fileName()
			self.tabfilelist.append(path)
		else:
			self.tabfilelist.append(None)
		self.tablist.append(Editor())
		self.tablist[-1].setFont(self.FONT)
		
		options = QTextOption()
		options.setTabStopDistance(QFontMetrics(self.tablist[-1].font()).horizontalAdvance(' ') * 4)
		options.setWrapMode(QTextOption.WrapMode.WordWrap if self.word_wrap else QTextOption.WrapMode.NoWrap)
		self.tablist[-1].document().setDefaultTextOption(options)
		self.tablist[-1].highlighter = Highlighter(window=self,parent=self.tablist[-1].document(), filename=name, style=STYLE["highlight"])
		
		self.tabs.addTab(self.tablist[-1], name)
		self.tabs.setCurrentIndex(len(self.tablist) - 1)

	def newdiffviewer(self, text1: str, text2: str, title="Diff Viewer"):
		self.tabfilelist.append(None)
		self.tablist.append(DiffViewer(self))
		self.tablist[-1].setFont(self.FONT)
		options = QTextOption()
		options.setTabStopDistance(QFontMetrics(self.tablist[-1].font()).horizontalAdvance(' ') * 4)
		options.setWrapMode(QTextOption.WrapMode.NoWrap)
		self.tablist[-1].difftxt1.document().setDefaultTextOption(options)
		self.tablist[-1].difftxt2.document().setDefaultTextOption(options)
		lexer = guess_lexer(text1)
		self.tablist[-1].difftxt1.highlighter = Highlighter(window=self,parent=self.tablist[-1].difftxt1.document(), style=STYLE["highlight"], lexer=lexer)
		self.tablist[-1].difftxt2.highlighter = Highlighter(window=self,parent=self.tablist[-1].difftxt2.document(), style=STYLE["highlight"], lexer=lexer)
		self.tablist[-1].diff_texts(text1, text2)
		self.tablist[-1].difftxt1.highlighter.tokenize()
		self.tablist[-1].difftxt2.highlighter.tokenize()
		self.tabs.addTab(self.tablist[-1], title)
		self.tabs.setCurrentIndex(len(self.tablist) - 1)

	def open_(self, file_path):
		try:
			with open(file_path, 'r', encoding='utf-8') as file:
				content = file.read()
				self.newtab(path=file_path)
				current_tab = self.tablist[-1]
				current_tab.setPlainText(content)
				current_tab.highlighter.tokenize()
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
			self.sidebar.explorer.setRootIndex(self.sidebar.explorer.file_model.index(folder_path))
			QDir.setCurrent(folder_path)
			self.settings.setValue("workspace", folder_path)
			self.ConsoleGroup.add_terminal()

	def save_file(self):#保存
		current_tab = self.tablist[self.tabs.currentIndex()]
		if not hasattr(current_tab, 'textCursor'):
			return
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
		if not hasattr(current_tab, 'textCursor'):
			return
		file_path, _ = QFileDialog.getSaveFileName(self, "名前を付けて保存", "", "All Files (*.*)")
		if file_path:
			try:
				with open(file_path, 'w', encoding='utf-8') as file:
					file.write(current_tab.toPlainText())
				current_tab.highlighter.set_filetype(file_path)
				current_tab.highlighter.rehighlight()
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
		if not hasattr(current_tab, 'textCursor'):
			return True
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
		self.ConsoleGroup.switch_terminal(0)
		self.ConsoleGroup.terminals[0].insertPlainText(command)
		self.ConsoleGroup.terminals[0].run_command()

	def run_code(self):#実行
		if self.running:
			return
		current_tab = self.tablist[self.tabs.currentIndex()]
		if not hasattr(current_tab, 'textCursor'):
			return
		if not hasattr(current_tab, 'file_path'):
			return
		if os.path.splitext(current_tab.file_path)[-1] == ".py":
			self.run_command(f"cd {os.path.dirname(current_tab.file_path)} && {embedded_python} {current_tab.file_path}")
	
	def open_file_from_tree(self, index):#ファイルツリーから開く(クリック)
		file_path = self.sidebar.explorer.file_model.filePath(index)
		if file_path in self.tabfilelist:
			tab_index = self.tabfilelist.index(file_path)
			self.tabs.setCurrentIndex(tab_index)
			return
		if QFileInfo(file_path).isFile():
			self.open_(file_path)

	def on_status_message_changed(self, message):#一時的なステータスメッセージが変更された時のハンドラ
		if not message:
			self.statusBar().showMessage("Ready")

	def toggle_wrap(self, checked):#折り返し切替
		for tab in self.tablist:
			if hasattr(tab, 'textCursor'):
				continue
			options = QTextOption()
			options.setTabStopDistance(QFontMetrics(tab.font()).horizontalAdvance(' ') * 4)
			if checked:
				options.setWrapMode(QTextOption.WrapMode.WordWrap)
			else:
				options.setWrapMode(QTextOption.WrapMode.NoWrap)
			tab.document().setDefaultTextOption(options)
		self.settings.setValue("wordWrap", checked)

	def open_search_sidebar(self):#サイドバーの検索を開く
		self.activity_bar.search_btn.click()
		if not self.sidebar.isVisible():
			self.sidebar.show()
		self.sidebar.setCurrentIndex(1)

	def open_diff_viewer(self):
		file_paths, _ = QFileDialog.getOpenFileNames(self, "ファイルを開く", "", "All Files (*.*)")
		if len(file_paths) != 2:
			QMessageBox.warning(self, "警告", "2つのファイルを選択してください。")
			return
		try:
			with open(file_paths[0], 'r', encoding='utf-8') as file1, open(file_paths[1], 'r', encoding='utf-8') as file2:
				content1 = file1.read()
				content2 = file2.read()
			self.newdiffviewer(content1, content2, title=f"title")
		except:
			QMessageBox.warning(self, "警告", "ファイルの読み込みに失敗しました。")
			return

	def toggle_fullscreen(self, checked):#全画面表示切替
		if checked:
			self.showFullScreen()
		else:
			self.showNormal()

	def change_theme(self, theme_name):#テーマ変更
		global STYLE
		STYLE = change_theme(theme_name)
		self.STYLE = STYLE
		self.setStyleSheet(open(STYLE["style"], "r", encoding="utf-8").read())

		for tab in self.tablist:
			if isinstance(tab, DiffViewer):
				# DiffViewerの場合は両方のエディタを更新
				for editor in [tab.difftxt1, tab.difftxt2]:
					editor.setFont(self.FONT)
					editor.highlighter.formats.clear()
					editor.highlighter.replace.clear()
					editor.highlighter.style = STYLE["highlight"]
					editor.highlighter.set_filetype(None)
					editor.highlighter.rehighlight()
				# 差分ハイライトも再適用
				tab.reapply_theme()
			elif hasattr(tab, 'highlighter'):
				tab.highlighter.formats.clear()
				tab.highlighter.replace.clear()
				tab.highlighter.style = STYLE["highlight"]
				tab.highlighter.set_filetype(tab.file_path if hasattr(tab, 'file_path') else None)
				tab.highlighter.rehighlight()
		for btn in self.ConsoleGroup.btn_group.buttons():
			btn.setIcon(QIcon(f"{self.DIR}/assets/terminal.svg"))
		self.ConsoleGroup.btn_group.button(self.ConsoleGroup.terminalstack.currentIndex()).setIcon(QIcon(f"{self.DIR}/assets/terminal-fill.svg"))
		self.settings.setValue("theme", theme_name)

	def load_settings(self):#設定を読み込み
		if self.settings.contains("theme"):
			theme_name = self.settings.value("theme")
			if theme_name:
				try:
					self.change_theme(theme_name)
				except:
					pass
		
		self.word_wrap = self.settings.value("wordWrap", False, type=bool)
		
		if self.settings.contains("verticalSplitter"):
			self.vertical_splitter.restoreState(self.settings.value("verticalSplitter"))
		if self.settings.contains("horizontalSplitter"):
			self.horizontal_splitter.restoreState(self.settings.value("horizontalSplitter"))
		
		if self.settings.contains("workspace"):
			last_folder = self.settings.value("workspace")
			if last_folder and os.path.exists(last_folder):
				self.sidebar.explorer.setRootIndex(self.sidebar.explorer.file_model.index(last_folder))
				QDir.setCurrent(last_folder)
	
	def save_settings(self):#設定を保存
		self.settings.setValue("geometry", self.saveGeometry())
		self.settings.setValue("verticalSplitter", self.vertical_splitter.saveState())
		self.settings.setValue("horizontalSplitter", self.horizontal_splitter.saveState())
		
		current_folder = QDir.currentPath()
		if current_folder:
			self.settings.setValue("workspace", current_folder)
	
	def closeEvent(self, event):#終了前処理など
		can_close = True
		for i in range(len(self.tablist)):
			if not hasattr(self.tablist[i], "textCursor"):
				continue
			if not self.maybe_save(i):
				can_close = False
				break
		if can_close:
			# 設定を保存
			self.save_settings()
			event.accept()
		else:
			event.ignore()
	
	def restart_application(self):
		self.close()
		time.sleep(0.5)
		self.new_window()

	def new_window(self):
		if OS == "Windows":
			subprocess.Popen(
				[sys.executable, os.path.abspath(__file__)], 
				startupinfo=si if OS == "Windows" else None
			)
		else:
			subprocess.Popen([sys.executable, os.path.abspath(__file__)])

if __name__ == "__main__":
	app = QApplication(sys.argv)
	window = Window()
	window.showMaximized()
	sys.exit(app.exec())