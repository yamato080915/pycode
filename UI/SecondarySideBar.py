from PySide6.QtWidgets import QTabWidget
import mdPreview
from Git import Graph

class SecondarySideBar(QTabWidget):
	def __init__(self, window=None, addons=[]):
		super().__init__()
		self.win = window
		self.setObjectName("secsidebar")
		self.graph = Graph.Main(window)
		self.addTab(self.graph, self.graph.icon, self.graph.name)
		self.mdPreview = mdPreview.Main(window)
		self.addTab(self.mdPreview, self.mdPreview.icon, self.mdPreview.name)
		self.addons = []
		for i, addon in enumerate(addons):
			self.addons.append(addon(self.win))
			self.addTab(self.addons[i], self.addons[i].icon, self.addons[i].name)
