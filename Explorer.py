from PySide6.QtWidgets import *
from PySide6.QtCore import QDir

class Explorer(QTreeView):
	def __init__(self, window=None):
		super().__init__()
		self.setObjectName("explorer")
		self.file_model = QFileSystemModel()
		self.file_model.setRootPath(QDir.currentPath())
		self.setModel(self.file_model)
		self.setRootIndex(self.file_model.index(QDir.currentPath()))
		for column in range(1, self.file_model.columnCount()):
			self.hideColumn(column)
		self.setColumnWidth(0, 250)
		self.setHeaderHidden(True)
		self.clicked.connect(window.open_file_from_tree)