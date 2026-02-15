"""プレビューアドオンの共通基底クラス"""
from addons.AddonBase import SecondarySideBar
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QVBoxLayout
from PySide6.QtGui import QFont
from PySide6.QtCore import QTimer


class PreviewBase(SecondarySideBar):
	"""プレビューアドオンの共通基底クラス
	タブ追跡・更新タイマー・ツールバー構築を共通化する。
	"""
	def __init__(self, window=None):
		super().__init__()
		self.win = window
		self._connected = False
		self.current_tab = None

		self.update_timer = QTimer()
		self.update_timer.timeout.connect(self.update_preview)
		self.update_timer.setSingleShot(True)

	def create_toolbar(self, title_text="プレビュー", object_name=None, extra_buttons=None):
		"""共通のツールバーを作成して返す"""
		toolbar = QWidget()
		if object_name:
			toolbar.setObjectName(object_name)
		toolbar_layout = QHBoxLayout(toolbar)
		toolbar_layout.setContentsMargins(5, 5, 5, 5)

		self.filename_label = QLabel(title_text)
		self.filename_label.setFont(QFont("Consolas", 10))
		toolbar_layout.addWidget(self.filename_label)

		toolbar_layout.addStretch()

		refresh_btn = QPushButton("🔄")
		refresh_btn.setFixedSize(30, 30)
		refresh_btn.setToolTip("更新")
		refresh_btn.clicked.connect(self.force_update)
		toolbar_layout.addWidget(refresh_btn)

		if extra_buttons:
			for btn in extra_buttons:
				toolbar_layout.addWidget(btn)

		return toolbar

	def showEvent(self, event):
		if not self._connected:
			self.win.tabs.currentChanged.connect(self.on_tab_changed)
			self._connected = True
		self.on_tab_changed(self.win.tabs.currentIndex())
		return super().showEvent(event)

	def hideEvent(self, event):
		self._disconnect_current_tab()
		return super().hideEvent(event)

	def _disconnect_current_tab(self):
		"""現在のタブのtextChangedシグナルを切断"""
		if self.current_tab:
			try:
				if hasattr(self.current_tab, 'textChanged'):
					self.current_tab.textChanged.disconnect(self.schedule_update)
			except:
				pass

	def _connect_tab(self, tab):
		"""タブのtextChangedシグナルを接続"""
		self.current_tab = tab
		if hasattr(tab, 'textChanged'):
			tab.textChanged.connect(self.schedule_update)

	def on_tab_changed(self, index):
		"""タブ変更時の処理。サブクラスでオーバーライドする。"""
		raise NotImplementedError

	def schedule_update(self):
		"""テキスト変更時に更新をスケジュール（500ms後）"""
		if self.isVisible():
			self.update_timer.stop()
			self.update_timer.start(500)

	def force_update(self):
		"""即座に更新"""
		self.update_timer.stop()
		self.update_preview()

	def update_preview(self):
		"""プレビューを更新。サブクラスでオーバーライドする。"""
		raise NotImplementedError
