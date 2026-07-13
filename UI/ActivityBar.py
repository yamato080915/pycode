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
	
		self.explorer_btn = self._create_button("explorer_btn", f"{self.dir}/assets/{self.icons[0][1]}", checked=True)
		self.search_btn = self._create_button("search_btn", f"{self.dir}/assets/{self.icons[1][0]}")
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

	def _create_button(self, name, icon_path, checked=False):
		"""アクティビティバーのボタンを作成"""
		btn = QPushButton()
		btn.setObjectName(name)
		btn.setIcon(QIcon(icon_path))
		btn.setFixedSize(48, 48)
		btn.setCheckable(True)
		if checked:
			btn.setChecked(True)
		return btn
