from PySide6.QtWidgets import QPushButton, QWidget
from Color import css_color, icon_color

class ActivityBar:
	def __init__(self, window=None):
		self.win = window
	
	def button(self):
		self.btn = QPushButton()
		self.btn.setObjectName("ADDONBASE")
		self.btn.setFixedSize(48,48)
		self.btn.setCheckable(True)
		return self.btn

	def icon_color(self, path):
		icon_color(path, css_color(self.win.STYLE))

class SideBar(QWidget):
	def __init__(self, window=None):
		super().__init__()
		self.name = ""
		self.description = ""
		self.version = "1.0.0"
	
	def icon_color(self, path):
		icon_color(path, css_color(self.win.STYLE))

class SecondarySideBar(QWidget):
	def __init__(self, window=None):
		super().__init__()
		self.name = ""
		self.icon = None
		self.description = ""
		self.version = "1.0.0"
	
	def icon_color(self, path):
		icon_color(path, css_color(self.win.STYLE))