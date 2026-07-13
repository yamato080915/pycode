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

		auto_update_label = QLabel("終了時に最新の状態へ自動更新します。")
		auto_update_label.setWordWrap(True)
		layout.addWidget(auto_update_label)

		self.auto_update_checkbox = QCheckBox("Auto Update")
		self.auto_update_checkbox.setChecked(self.win.settings.value("autoUpdate", True, type=bool))
		self.auto_update_checkbox.toggled.connect(self.toggle_auto_update)
		layout.addWidget(self.auto_update_checkbox)

		layout.addStretch()

	def toggle_auto_update(self, checked):
		self.win.settings.setValue("autoUpdate", checked)
