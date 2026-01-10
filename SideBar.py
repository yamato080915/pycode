from PySide6.QtWidgets import *
from PySide6.QtGui import QIcon
from Explorer import Explorer
from Search import Search
#from main import window as win

class SideBar(QStackedWidget):
	def __init__(self, window=None, addons=[]):
		super().__init__()
		self.win = window
		self.setObjectName("sidebar")
		self.explorer = Explorer(window)
		self.addWidget(self.explorer)
		self.search = Search(window)
		self.addWidget(self.search)

		self.setCurrentIndex(0)

		window.activity_bar.explorer_btn.clicked.connect(lambda: self.switch_tab(0))
		window.activity_bar.search_btn.clicked.connect(lambda: self.switch_tab(1))

		self.activity_btn_group = QButtonGroup()
		self.activity_btn_group.addButton(window.activity_bar.explorer_btn, 0)
		self.activity_btn_group.addButton(window.activity_bar.search_btn, 1)
		for i, btn in enumerate(window.activity_bar.addonbtn):
			btn.clicked.connect(lambda checked, index=i + 2: self.switch_tab(index))
			self.activity_btn_group.addButton(btn, i + 2)
			self.addWidget(addons[i](window, index=i + 2))
		
		self.activity_btn_group.setExclusive(True)
	
	def switch_tab(self, index):
		for i, btn in enumerate(self.activity_btn_group.buttons()):
			try:
				btn.setIcon(QIcon(f"{self.win.DIR}/assets/{self.win.activity_bar.icons[i][0]}"))
			except IndexError:
				pass
		if self.currentIndex() == index and self.isVisible():
			self.hide()
		else:
			try:
				self.activity_btn_group.button(index).setIcon(QIcon(f"{self.win.DIR}/assets/{self.win.activity_bar.icons[index][1]}"))
			except IndexError:
				pass
			self.setCurrentIndex(index)
			self.show()