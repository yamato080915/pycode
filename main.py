import sys, os, json, cssutils, logging, threading, time
from pathlib import Path
import xml.etree.ElementTree as ET
from PySide6.QtWidgets import *
from PySide6.QtGui import QFont, QTextOption, QFontMetrics
from PySide6.QtCore import Qt, QFileInfo, QDir, QSettings
from SyntaxHighlight import PygmentsSyntaxHighlight
from LineNumberTextEdit import LineNumberTextEdit as TextBox
from ActivityBar import ActivityBar
from SideBar import SideBar
from MenuBar import MenuBar
from TerminalGroup import TerminalGroup

DIR = os.getcwd()
embedded_python = f"{DIR}/python/python.exe"
STYLE = "onedarkpro"
with open(f"{DIR}/themes/{STYLE}.json", "r", encoding="utf-8") as f:
	STYLE = json.load(f)
if not "style" in STYLE:
	STYLE["style"] = "themes/monokai.css"
STYLE["style"] = f"{DIR}/{STYLE["style"]}"

cssutils.log.setLevel(logging.CRITICAL)
parser = cssutils.CSSParser(validate=False)
for rule in parser.parseFile(STYLE["style"]):
	if rule.type == rule.STYLE_RULE:
		if rule.selectorText == "QTextEdit":
			color = rule.style.getPropertyValue("color")
if not color:color = "#000000"
ET.register_namespace("", "http://www.w3.org/2000/svg")
for i in iter(p.name for p in Path(f"{DIR}/assets").iterdir() if p.is_file() and p.suffix.lower() == ".svg"):
	tree = ET.parse(f"{DIR}/assets/{i}")
	root = tree.getroot()
	for elem in root.iter():
		if 'fill' in elem.attrib:
			elem.attrib['fill'] = color
	tree.write(f"{DIR}/assets/{i}", encoding="utf-8", xml_declaration=False)
	
class Window(QMainWindow):
	def __init__(self):
		super().__init__()		
		self.DIR = DIR
		self.setStyleSheet(open(STYLE["style"], "r", encoding="utf-8").read())
		self.setWindowTitle(f"PyCode2")
		self.resize(1600, 900)
		
		self.FONT = QFont("Consolas", 11)

		self.main_widget = QWidget()
		self.setCentralWidget(self.main_widget)
		self.main_layout = QVBoxLayout(self.main_widget)
		self.main_layout.setContentsMargins(2, 2, 2, 2)

		vertical_splitter = QSplitter(Qt.Vertical)
		horizontal_splitter = QSplitter(Qt.Horizontal)

		# -----------------------------------------------------------
		# アクティビティバー
		# -----------------------------------------------------------
		self.activity_bar = ActivityBar(self)
		self.sidebar = SideBar(self)
		# -----------------------------------------------------------
		# テキストエディタ部
		# -----------------------------------------------------------
		self.tabs = QTabWidget()
		self.tabs.setTabsClosable(True)
		self.tabs.tabCloseRequested.connect(self.close_tab)

		self.tablist = []
		self.tabfilelist = []
		self.newtab(name="Untitled")
		# -----------------------------------------------------------
		# 下：コンソール・出力ビュー
		# -----------------------------------------------------------
		self.ConsoleGroup = TerminalGroup(self)
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
		horizontal_splitter.setStretchFactor(0, 0)
		horizontal_splitter.setStretchFactor(1, 0)
		horizontal_splitter.setStretchFactor(2, 1)

		self.main_layout.addWidget(horizontal_splitter)

		MenuBar(self)
		self.create_status_bar()

	def create_status_bar(self):
		self.status_bar = self.statusBar()
		self.status_bar.setObjectName("status_bar")
		self.status_bar.setFont(self.FONT)

		self.permanent_message = QLabel()
		self.permanent_message.setFont(self.FONT)
		self.permanent_message.setText("Coming Soon")
		
		self.status_bar.addPermanentWidget(self.permanent_message)

		self.status_bar.messageChanged.connect(self.on_status_message_changed)
		threading.Thread(target=self.update_status, daemon=True).start()

	def update_status(self):
		running = False
		while True:
			flag = False
			if any((pid, name) for pid, name in self.ConsoleGroup.terminals[0].running):
				flag = True
			if flag and not running:
				self.status_bar.setStyleSheet("#status_bar {background-color: " + STYLE["theme"]["status_bar"]["running"]["background"] + "; color: " + STYLE["theme"]["status_bar"]["running"]["foreground"] + ";}")
			elif not flag and running:
				self.status_bar.setStyleSheet(open(STYLE["style"], "r", encoding="utf-8").read())
			running = flag
			time.sleep(0.1)

	def newtab(self, name=None, path=None):#新しいテキストファイル
		if path is not None:
			name = QFileInfo(path).fileName()
			self.tabfilelist.append(path)
		else:
			self.tabfilelist.append(None)
		self.tablist.append(TextBox())
		self.tablist[-1].setFont(self.FONT)
		
		options = QTextOption()
		options.setTabStopDistance(QFontMetrics(self.tablist[-1].font()).horizontalAdvance(' ') * 4)
		self.tablist[-1].document().setDefaultTextOption(options)
		self.tablist[-1].highlighter = PygmentsSyntaxHighlight(window=self,parent=self.tablist[-1].document(), filename=name, style=STYLE["highlight"])
		
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
			self.sidebar.explorer.setRootIndex(self.sidebar.explorer.file_model.index(folder_path))
			QDir.setCurrent(folder_path)
			self.ConsoleGroup.add_terminal()

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
		current_tab = self.tablist[self.tabs.currentIndex()]
		if not hasattr(current_tab, 'file_path'):
			return
		if os.path.splitext(current_tab.file_path)[-1] == ".py":
			self.run_command(f"{embedded_python} {current_tab.file_path}")

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