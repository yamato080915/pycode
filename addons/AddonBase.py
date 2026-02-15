from PySide6.QtWidgets import QPushButton, QWidget
from PySide6.QtGui import QIcon
from Color import css_color, icon_color


class AddonMixin:
	"""共通のアドオンメソッドを提供するMixin"""
	def icon_color(self, path):
		icon_color(path, css_color(self.win.STYLE))


class ActivityBar(AddonMixin):
	def __init__(self, window=None):
		self.win = window

	def button(self, name=None, icon_path=None):
		self.btn = QPushButton()
		self.btn.setObjectName(name or "ADDONBASE")
		self.btn.setFixedSize(48, 48)
		self.btn.setCheckable(True)
		if icon_path:
			self.icon_color(icon_path)
			self.btn.setIcon(QIcon(icon_path))
		return self.btn


class SideBar(AddonMixin, QWidget):
	def __init__(self, window=None):
		super().__init__()
		self.name = ""
		self.description = ""
		self.version = "1.0.0"


class SecondarySideBar(AddonMixin, QWidget):
	def __init__(self, window=None):
		super().__init__()
		self.name = ""
		self.icon = None
		self.description = ""
		self.version = "1.0.0"