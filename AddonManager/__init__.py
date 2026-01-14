import json
import importlib
from addons.AddonBase import ActivityBar, SideBar, SecondarySideBar
from addons.AddonBase import ActivityBar, SideBar
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import *

class managerBtn(ActivityBar):
	def __init__(self, window=None):
		super().__init__(window)
		self.win = window
	
	def button(self):
		self.btn = super().button()
		self.btn.setObjectName("manager_btn")
		self.icon_color(f"{self.win.DIR}/AddonManager/manager.svg")
		self.btn.setIcon(QIcon(f"{self.win.DIR}/AddonManager/manager.svg"))
		return self.btn

class AddonManager:
	def __init__(self, window=None):
		self.window = window
		# addonsにはクラスオブジェクトのリストを保持（設定には保存しない）
		self.addons = {
			"ActivityBar": [],
			"SideBar": [],
			"SecondarySideBar": []
		}
		
		# インストール済みアドオンを自動ロード
		self.load_installed_addons()
		self.addons["ActivityBar"].append(managerBtn)
		self.addons["SideBar"].append(main)

	def load_installed_addons(self):
		installed = self.window.settings.value("addons", [])
		
		with open("addons/addons.json", "r", encoding="utf-8") as f:
			addons_json = json.load(f)
		
		for addon_name in installed:
			if addon_name in addons_json:
				addon = addons_json[addon_name]
				self.load_addon_by_name(addon_name, addon)

	def load_addon_by_name(self, addon_name, addon):
		if type(addon) == list:
			for a in addon:
				self.load_addon(a)
		else:
			self.load_addon(addon)

	def load_addon(self, addon):
		a = getattr(importlib.import_module(".".join(addon.split(".")[:-1])), addon.split(".")[-1])
		if issubclass(a, ActivityBar):
			self.addons["ActivityBar"].append(a)
		elif issubclass(a, SideBar):
			self.addons["SideBar"].append(a)
		elif issubclass(a, SecondarySideBar):
			self.addons["SecondarySideBar"].append(a)

class main(SideBar):
	def __init__(self, window=None, index=2):
		super().__init__(window)
		self.name = "Addon Manager"
		self.description = ""
		self.version = ""

		self.win = window
		self.index = index
		self._connected = False
		self.addon_widgets = {}
		self.setup()

	def get_installed_addons(self):
		return self.win.settings.value("addons", [])
	
	def save_installed_addons(self, installed):
		self.win.settings.setValue("addons", installed)

	def is_addon_installed(self, addon_name):
		installed = self.get_installed_addons()
		return addon_name in installed

	def install_addon(self, addon_name, addon):
		installed = self.get_installed_addons()
		if addon_name not in installed:
			installed.append(addon_name)
			self.save_installed_addons(installed)
		
		self.update_addon_button(addon_name)
		
		self.win.addon_manager.load_addon_by_name(addon_name, addon)
		
		# 再起動の確認ダイアログを表示
		reply = QMessageBox.question(
			self, 
			"アドオンマネージャー", 
			f"{addon_name}をインストールしました。\n変更を完全に反映するにはアプリケーションを再起動する必要があります。\n\n今すぐ再起動しますか?",
			QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
			QMessageBox.StandardButton.Yes
		)
		
		if reply == QMessageBox.StandardButton.Yes:
			self.win.restart_application()
	
	def uninstall_addon(self, addon_name):
		installed = self.get_installed_addons()
		if addon_name in installed:
			installed.remove(addon_name)
			self.save_installed_addons(installed)
		
		self.update_addon_button(addon_name)

		# 再起動の確認ダイアログを表示
		reply = QMessageBox.question(
			self, 
			"アドオンマネージャー", 
			f"{addon_name}をアンインストールしました。\n変更を反映するにはアプリケーションを再起動する必要があります。\n\n今すぐ再起動しますか?",
			QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
			QMessageBox.StandardButton.Yes
		)
		
		if reply == QMessageBox.StandardButton.Yes:
			self.win.restart_application()
	
	def update_addon_button(self, addon_name):
		if addon_name not in self.addon_widgets:
			return
		
		widget_data = self.addon_widgets[addon_name]
		btn = widget_data["button"]
		installed = self.is_addon_installed(addon_name)
		
		try:
			btn.clicked.disconnect()
		except RuntimeError:
			pass

		if installed:
			btn.setText("Uninstall")
			btn.clicked.connect(lambda checked=False: self.uninstall_addon(addon_name))
		else:
			btn.setText("Install")
			btn.clicked.connect(lambda checked=False: self.install_addon(addon_name, widget_data["addon"]))

	def setup(self):
		with open("addons/addons.json", "r", encoding="utf-8") as f:
			self.addonsJson = json.load(f)
		
		layout = QVBoxLayout()
		
		for name, addon in self.addonsJson.items():
			w = QWidget()
			l = QHBoxLayout()
			title = QLabel(name)
			l.addWidget(title, 1)
			
			installed = self.is_addon_installed(name)
			btn = QPushButton("Uninstall" if installed else "Install")
			
			if installed:
				btn.clicked.connect(lambda checked=False, n=name: self.uninstall_addon(n))
			else:
				btn.clicked.connect(lambda checked=False, n=name, a=addon: self.install_addon(n, a))
			
			l.addWidget(btn, 0)
			w.setLayout(l)
			layout.addWidget(w)
			
			self.addon_widgets[name] = {
				"widget": w,
				"button": btn,
				"addon": addon
			}
		
		layout.addStretch()
		self.setLayout(layout)