import sys
from PySide6.QtWidgets import *

class Settings(QWidget):
	def __init__(self, window=None):
		super().__init__()
		self.win = window
		self.setObjectName("Settings")

		layout = QVBoxLayout(self)
		layout.setContentsMargins(12, 12, 12, 12)
		layout.setSpacing(10)

		title = QLabel("設定")
		title.setObjectName("settings_title")
		layout.addWidget(title)

		layout.addSpacing(10)

		auto_update_label = QLabel("終了時に最新の状態へ自動更新します。")
		auto_update_label.setWordWrap(True)
		layout.addWidget(auto_update_label)

		self.auto_update_checkbox = QCheckBox("Auto Update")
		self.auto_update_checkbox.setChecked(self.win.settings.value("autoUpdate", True, type=bool))
		self.auto_update_checkbox.toggled.connect(self.toggle_auto_update)
		layout.addWidget(self.auto_update_checkbox)

		layout.addSpacing(10)

		dev_update_label = QLabel("Dev版にアクセス")
		dev_update_label.setWordWrap(True)
		layout.addWidget(dev_update_label)

		self.dev_update_checkbox = QCheckBox("Enable Development Version")
		self.dev_update_checkbox.setChecked(self.win.settings.value("DevUpdate", False, type=bool))
		self.dev_update_checkbox.toggled.connect(self.toggle_dev_update)
		layout.addWidget(self.dev_update_checkbox)

		layout.addSpacing(10)

		python_interpreter_label = QLabel("Pythonインタープリター")
		python_interpreter_label.setWordWrap(True)
		layout.addWidget(python_interpreter_label)

		interpreter_row = QHBoxLayout()
		self.python_interpreter_edit = QLineEdit()
		self.python_interpreter_edit.setReadOnly(True)
		self.python_interpreter_edit.setPlaceholderText(sys.executable)
		self.python_interpreter_edit.setText(self.win.settings.value("pythonInterpreter", sys.executable, type=str))
		interpreter_row.addWidget(self.python_interpreter_edit)

		self.python_interpreter_button = QPushButton("参照")
		self.python_interpreter_button.clicked.connect(self.choose_python_interpreter)
		interpreter_row.addWidget(self.python_interpreter_button)

		layout.addLayout(interpreter_row)

		layout.addStretch()

	def toggle_auto_update(self, checked):
		self.win.settings.setValue("autoUpdate", checked)
	
	def toggle_dev_update(self, checked):
		self.win.settings.setValue("DevUpdate", checked)

	def choose_python_interpreter(self):
		path, _ = QFileDialog.getOpenFileName(
			self,
			"Pythonインタープリターを選択",
			self.python_interpreter_edit.text() or sys.executable,
			"実行ファイル (*.exe);;すべてのファイル (*.*)"
		)
		if not path:
			return
		self.python_interpreter_edit.setText(path)
		self.win.settings.setValue("pythonInterpreter", path)
