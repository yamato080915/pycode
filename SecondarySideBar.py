from PySide6.QtWidgets import QTabWidget

class SecondarySideBar(QTabWidget):
	def __init__(self, window=None, addons=[]):
		super().__init__()
		self.win = window
		self.setObjectName("secsidebar")
		self.addons = []
		for i, addon in enumerate(addons):
			self.addons.append(addon(self.win))
			self.addTab(self.addons[i], self.addons[i].icon, self.addons[i].name)
