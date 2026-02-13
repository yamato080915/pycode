from PySide6.QtWidgets import *
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QTextCharFormat, QBrush, QColor
from utils import navigate_to_position, perform_search_across_tabs
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

	def search(self, pattern):
		def create_widget(highlighted_text, result_index):
			widget = QWidget()
			h_layout = QHBoxLayout(widget)
			h_layout.setContentsMargins(0, 0, 0, 0)
			label = QLabel(highlighted_text)
			label.setTextFormat(Qt.TextFormat.RichText)
			replace_btn = QPushButton("置換")
			replace_btn.setFont(self.win.FONT)
			replace_btn.clicked.connect(lambda idx=result_index: self.replace(idx))
			h_layout.addWidget(label, 1)
			h_layout.addWidget(replace_btn, 0)
			return widget

		self.ress = perform_search_across_tabs(self.win, self.tree, pattern, create_item_widget=create_widget)

	def on_item_clicked(self, item, column):
		data = item.data(0, Qt.UserRole)
		if data:
			tab, line_num, col = data
			navigate_to_position(self.win, tab, line_num, col)
	
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