from PySide6.QtWidgets import *

class ActivityBar(QWidget):
	def __init__(self, window=None):
		super().__init__()
		self.setObjectName("activity_bar")

		self.bar_layout = QVBoxLayout(self)
		self.bar_layout.setContentsMargins(0,0,0,0)
		self.bar_layout.setSpacing(0)

		self.explorer()
		self.search()

		self.bar_layout.addWidget(self.explorer_btn)
		self.bar_layout.addWidget(self.search_btn)
		self.bar_layout.addStretch()
	
	def explorer(self):
		self.explorer_btn = QPushButton()
		self.explorer_btn.setObjectName("explorer_btn")
		self.explorer_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon))
		self.explorer_btn.setFixedSize(48,48)
		self.explorer_btn.setCheckable(True)
		self.explorer_btn.setChecked(True)
	
	def search(self):
		self.search_btn = QPushButton()
		self.search_btn.setObjectName("search_btn")
		self.search_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogContentsView))
		self.search_btn.setFixedSize(48,48)
		self.search_btn.setCheckable(True)
