from PySide6.QtWidgets import *
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from Terminal import Terminal

class TerminalGroup(QWidget):
	def __init__(self, window=None):
		super().__init__()
		self.win = window

		self.mainlayout = QHBoxLayout(self)
		self.mainlayout.setContentsMargins(0,0,0,0)
		self.mainlayout.setSpacing(0)

		self.btn_group = QButtonGroup()
		self.btn_group.setExclusive(True)

		self.tab = QWidget()
		self.tab.setFixedWidth(30)
		self.tab_layout = QVBoxLayout(self.tab)
		self.tab_layout.setContentsMargins(0,0,0,0)
		self.tab_layout.setSpacing(2)
		self.tab_layout.setAlignment(Qt.AlignTop)

		self.terminals = []

		self.terminalstack = TerminalStack(window)

		self.mainlayout.addWidget(self.terminalstack)
		self.mainlayout.addWidget(self.tab)
		self.add_terminal("Runner")
		self.add_terminal()
	
	def add_terminal(self, name="Terminal"):
		for btn in self.btn_group.buttons():
			btn.setIcon(QIcon(f"{self.win.DIR}/assets/terminal.svg"))
		btn = QPushButton()
		btn.setObjectName(f"{name}_Tab_Button")
		btn.setIcon(QIcon(f"{self.win.DIR}/assets/terminal-fill.svg"))
		btn.setCheckable(True)
		btn.setChecked(True)
		terminal_index = len(self.terminals)
		self.btn_group.addButton(btn, terminal_index)
		self.tab_layout.addWidget(btn)
		btn.clicked.connect(lambda: self.switch_terminal(terminal_index))
		terminal = self.terminalstack.new(name)
		self.terminals.append(terminal)
	
	def switch_terminal(self, index):
		for i, btn in enumerate(self.btn_group.buttons()):
			btn.setIcon(QIcon(f"{self.win.DIR}/assets/terminal.svg"))
		self.btn_group.button(index).setIcon(QIcon(f"{self.win.DIR}/assets/terminal-fill.svg"))
		self.terminalstack.setCurrentIndex(index)
		self.terminals[index].show()

class TerminalStack(QStackedWidget):
	def __init__(self, window=None):
		super().__init__()
		self.setObjectName("terminal_stacked")
	
	def new(self, name="Terminal"):
		terminal = Terminal()
		self.addWidget(terminal)
		self.setCurrentWidget(terminal)
		if name=="Runner":
			terminal.setReadOnly(True)
			terminal.appendPlainText("This terminal is for running scripts.(Read-only)\n")
		return terminal