import json
import importlib
from addons.AddonBase import ActivityBar, SideBar

class AddonManager:
	def __init__(self, window=None):
		self.window = window
		self.addons = {"ActivityBar": [], "SideBar": []}
		with open("addons/addons.json", "r", encoding="utf-8") as f:
			addonsJson = json.load(f)
		for name, path in addonsJson.items():
			addon = getattr(importlib.import_module(".".join(path.split(".")[:-1])), path.split(".")[-1])
			if issubclass(addon, ActivityBar):
				self.addons["ActivityBar"].append(addon)
			elif issubclass(addon, SideBar):
				self.addons["SideBar"].append(addon)