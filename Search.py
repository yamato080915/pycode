from PySide6.QtWidgets import *
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QTextCharFormat, QBrush, QColor
#from main import window as win

class Search(QWidget):
	def __init__(self, window=None):
		super().__init__()
		self.win = window
		self.setObjectName("search")

		layout = QVBoxLayout()

		title = QLabel("検索と置換")
		title.setFont(window.FONT)
		title.setContentsMargins(0,0,10,0)
		
		self.search_input = QLineEdit()
		self.search_input.setFont(window.FONT)
		self.search_input.setPlaceholderText("検索")
		self.search_input.textChanged.connect(lambda: (self.timer.stop(), self.timer.start()))
		
		self.timer = QTimer()
		self.timer.setSingleShot(True)
		self.timer.setInterval(300)
		self.timer.timeout.connect(self.main)

		rep_layout = QHBoxLayout()
		self.replace_input = QLineEdit()
		self.replace_input.setFont(window.FONT)
		self.replace_input.setPlaceholderText("置換")
		self.replace_input.textChanged.connect(lambda: (self.timer.stop(), self.timer.start()))
		replace_btn = QPushButton("置換")
		replace_btn.setFont(window.FONT)
		replace_btn.clicked.connect(self.replace_all)
		rep_layout.addWidget(self.replace_input)
		rep_layout.addWidget(replace_btn)

		self.tree = QTreeWidget()
		self.tree.setHeaderHidden(True)
		self.tree.itemClicked.connect(self.on_item_clicked)

		layout.addWidget(title)
		layout.addWidget(self.search_input)
		layout.addLayout(rep_layout)
		layout.addWidget(self.tree)
		
		self.setLayout(layout)
	
	def build_lps(self, pattern: str) -> list[int]:
		lps = [0] * len(pattern)
		j = 0  # prefix の長さ

		for i in range(1, len(pattern)):
			while j > 0 and pattern[i] != pattern[j]:
				j = lps[j - 1]

			if pattern[i] == pattern[j]:
				j += 1
				lps[i] = j

		return lps

	def kmp_search(self, text: str, pattern: str) -> list[int]:
		"""text 中の pattern の開始位置をすべて返す"""
		if not pattern:
			return []

		lps = self.build_lps(pattern)
		result = []

		j = 0  # pattern 側のインデックス
		for i in range(len(text)):
			while j > 0 and text[i] != pattern[j]:
				j = lps[j - 1]

			if text[i] == pattern[j]:
				j += 1

			if j == len(pattern):
				result.append(i - j + 1)  # マッチ開始位置
				j = lps[j - 1]  # 次の探索へ

		return result

	def search(self, pattern):
		self.tree.clear()
		root = []
		
		# すべてのタブのハイライトをクリア
		for tab in self.win.tablist:
			tab.setExtraSelections([])
		
		for tab in self.win.tablist:
			root.append(QTreeWidgetItem(self.tree, [tab.file_path if hasattr(tab, "file_path") else "Untitled"]))
			text = tab.document().toPlainText()
			indices = self.kmp_search(text, pattern)
			self.ress = []
			
			# エディタ内でハイライト表示
			if pattern and indices:
				extra_selections = []
				for index in indices:
					selection = QTextEdit.ExtraSelection()
					selection.format.setBackground(QColor(self.win.STYLE["theme"]["search"]["background"]))
					cursor = tab.textCursor()
					cursor.setPosition(index)
					cursor.movePosition(cursor.MoveOperation.Right, cursor.MoveMode.KeepAnchor, len(pattern))
					selection.cursor = cursor
					extra_selections.append(selection)
				tab.setExtraSelections(extra_selections)
			for i, index in enumerate(indices):
				flag = False
				line_start = text.rfind('\n', 0, index) + 1
				line_end = text.find('\n', index)
				if line_end == -1:
					line_end = len(text)
				line_text = text[line_start:line_end]
				line_text_stripped = line_text.lstrip()
				
				pattern_pos = index - line_start - (len(line_text) - len(line_text_stripped))
				
				if index-line_start>=20:
					line_text_stripped = f"...{line_text_stripped[index-line_start-20:]}"
					pattern_pos = pattern_pos - (index-line_start-20) + 3
				
				line_num = text[:index].count('\n') + 1
				
				before = line_text_stripped[:pattern_pos]
				match = line_text_stripped[pattern_pos:pattern_pos+len(pattern)]
				after = line_text_stripped[pattern_pos+len(pattern):]
				highlighted_text = f'{before}<span style="background-color: {self.win.STYLE["theme"]["search"]["background"]};">{match}</span>{after}'
				
				item = QTreeWidgetItem(root[-1])
				
				widget = QWidget()
				h_layout = QHBoxLayout(widget)
				h_layout.setContentsMargins(0, 0, 0, 0)
				
				label = QLabel(highlighted_text)
				label.setTextFormat(Qt.TextFormat.RichText)
				replace_btn = QPushButton("置換")
				replace_btn.setFont(self.win.FONT)
				replace_btn.clicked.connect(lambda idx=i: self.replace(idx))

				h_layout.addWidget(label, 1)
				h_layout.addWidget(replace_btn, 0)

				self.tree.setItemWidget(item, 0, widget)
				item.setData(0, Qt.UserRole, (tab, line_num, index - line_start))
				self.ress.append((tab, index, line_num, index - line_start, len(pattern)))
				
		self.tree.expandAll()
		self.tree.show()

	def on_item_clicked(self, item, column):
		data = item.data(0, Qt.UserRole)
		if data:
			tab, line_num, col = data
			index = self.win.tablist.index(tab)
			self.win.tabs.setCurrentIndex(index)
			cursor = tab.textCursor()
			cursor.movePosition(cursor.MoveOperation.Start)
			cursor.movePosition(cursor.MoveOperation.Down, cursor.MoveMode.MoveAnchor, line_num - 1)
			cursor.movePosition(cursor.MoveOperation.Right, cursor.MoveMode.MoveAnchor, col)
			tab.setTextCursor(cursor)
			tab.setFocus()
	
	def main(self):
		search = self.search_input.text()
		self.search(search)

	def replace_all(self):
		for i in range(len(self.ress)-1, -1, -1):
			self.replace(i)

	def replace(self, i):
		tab, index, line_num, col, length = self.ress[i]
		replace_text = self.replace_input.text()
		
		cursor = tab.textCursor()
		cursor.setPosition(index)
		cursor.movePosition(cursor.MoveOperation.Right, cursor.MoveMode.KeepAnchor, length)
		cursor.insertText(replace_text)
		
		self.main()