from PySide6.QtWidgets import *
from PySide6.QtGui import QIcon
from Git import Button

class ActivityBar(QWidget):
	def __init__(self, window=None, addons=[]):
		super().__init__()
		self.setObjectName("activity_bar")
		
		self.dir = window.DIR

		self.bar_layout = QVBoxLayout(self)
		self.setFixedWidth(48)
		self.bar_layout.setContentsMargins(0,0,0,0)
		self.bar_layout.setSpacing(0)

		self.icons = [("folder.svg", "folder-open.svg"), ("search.svg", "search.svg"), ("git.svg", "git.svg")]
	
		self.explorer()
		self.search()
		self.git_btn = Button(window).button()

		self.bar_layout.addWidget(self.explorer_btn)
		self.bar_layout.addWidget(self.search_btn)
		self.bar_layout.addWidget(self.git_btn)
		self.addonbtn = []
		for i in addons:
			addon = i(window)
			btn = addon.button()
			self.bar_layout.addWidget(btn)
			self.addonbtn.append(btn)
		self.bar_layout.addStretch()

	def explorer(self):
		self.explorer_btn = QPushButton()
		self.explorer_btn.setObjectName("explorer_btn")
		self.explorer_btn.setIcon(QIcon(f"{self.dir}/assets/{self.icons[0][1]}"))
		self.explorer_btn.setFixedSize(48,48)
		self.explorer_btn.setCheckable(True)
		self.explorer_btn.setChecked(True)
	
	def search(self):
		self.search_btn = QPushButton()
		self.search_btn.setObjectName("search_btn")
		self.search_btn.setIcon(QIcon(f"{self.dir}/assets/{self.icons[1][0]}"))
		self.search_btn.setFixedSize(48,48)
		self.search_btn.setCheckable(True)
