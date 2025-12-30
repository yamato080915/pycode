from PySide6.QtWidgets import *

class Search(QWidget):
	def __init__(self, window=None):
		super().__init__()
		self.setObjectName("search")

		layout = QVBoxLayout()

		title = QLabel("検索と置換")
		title.setFont(window.FONT)
		title.setContentsMargins(0,0,10,0)
		
		search_input = QLineEdit()
		search_input.setFont(window.FONT)
		search_input.setPlaceholderText("検索")

		rep_layout = QHBoxLayout()
		replace_input = QLineEdit()
		replace_input.setFont(window.FONT)
		replace_input.setPlaceholderText("置換")
		replace_btn = QPushButton("置換")
		replace_btn.setFont(window.FONT)
		rep_layout.addWidget(replace_input)
		rep_layout.addWidget(replace_btn)

		layout.addWidget(title)
		layout.addWidget(search_input)
		layout.addLayout(rep_layout)
		layout.addStretch()
		
		self.setLayout(layout)