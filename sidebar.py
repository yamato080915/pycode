from PySide6.QtWidgets import *
from explorer import Explorer

class SideBar(QStackedWidget):
	def __init__(self, window=None):
		super().__init__()
		self.setObjectName("sidebar")
		self.explorer = Explorer(window)
		self.addWidget(self.explorer)

		self.addWidget(QWidget())

		self.setCurrentIndex(0)

		window.activity_bar.explorer_btn.clicked.connect(lambda: self.switch_tab(0))
		window.activity_bar.search_btn.clicked.connect(lambda: self.switch_tab(1))

		self.activity_btn_group = QButtonGroup()
		self.activity_btn_group.addButton(window.activity_bar.explorer_btn, 0)
		self.activity_btn_group.addButton(window.activity_bar.search_btn, 1)
		self.activity_btn_group.setExclusive(True)
	
	def switch_tab(self, index):
		if self.currentIndex() == index and self.isVisible():
			self.hide()
		else:
			self.setCurrentIndex(index)
			self.show()