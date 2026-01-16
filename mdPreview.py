from addons.AddonBase import SecondarySideBar
from PySide6.QtWidgets import *
from PySide6.QtGui import QIcon, QFont
from PySide6.QtCore import Qt, QTimer
import markdown
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.tables import TableExtension
from markdown.extensions.toc import TocExtension
import cssutils
import logging

cssutils.log.setLevel(logging.CRITICAL)

class Main(SecondarySideBar):
	def __init__(self, window=None):
		super().__init__()
		self.win = window
		self.icon_color(f"{self.win.DIR}/assets/markdown.svg")
		self.name = "md Preview"
		self.icon = QIcon(f"{self.win.DIR}/assets/markdown.svg")
		self.description = "Markdown Preview"
		self.version = "1.0.0"

		self._connected = False
		self.update_timer = QTimer()
		self.update_timer.timeout.connect(self.update_preview)
		self.update_timer.setSingleShot(True)

		main_layout = QVBoxLayout()
		main_layout.setContentsMargins(0, 0, 0, 0)
		main_layout.setSpacing(0)
		
		# ツールバー
		toolbar = QWidget()
		toolbar.setObjectName("mdpreview_toolbar")
		toolbar_layout = QHBoxLayout(toolbar)
		toolbar_layout.setContentsMargins(5, 5, 5, 5)
		
		self.filename_label = QLabel("プレビュー")
		self.filename_label.setFont(QFont("Consolas", 10))
		toolbar_layout.addWidget(self.filename_label)
		
		toolbar_layout.addStretch()
		
		# 更新ボタン
		refresh_btn = QPushButton("🔄")
		refresh_btn.setFixedSize(30, 30)
		refresh_btn.setToolTip("更新")
		refresh_btn.clicked.connect(self.force_update)
		toolbar_layout.addWidget(refresh_btn)
		
		main_layout.addWidget(toolbar)
		
		# プレビュー表示エリア
		self.preview_area = QTextBrowser()
		self.preview_area.setObjectName("mdpreview_area")
		self.preview_area.setOpenExternalLinks(True)
		self.preview_area.setFont(QFont("Segoe UI", 10))
		main_layout.addWidget(self.preview_area)
		
		self.setLayout(main_layout)
		self.current_tab = None

		# Markdown設定
		self.md = markdown.Markdown(
			extensions=[
				'extra',
				'nl2br',
				'sane_lists',
				FencedCodeExtension(),
				CodeHiliteExtension(
					linenums=False,
					guess_lang=False
				),
				TableExtension(),
				TocExtension()
			]
		)
	
	def showEvent(self, event):
		if not self._connected:
			self.win.tabs.currentChanged.connect(self.on_tab_changed)
			self._connected = True
		self.on_tab_changed(self.win.tabs.currentIndex())
		return super().showEvent(event)
	
	def hideEvent(self, event):
		if self.current_tab:
			try:
				if hasattr(self.current_tab, 'textChanged'):
					self.current_tab.textChanged.disconnect(self.schedule_update)
			except:
				pass
		return super().hideEvent(event)
	
	def on_tab_changed(self, index):
		# 既存のタブの接続を解除
		if self.current_tab:
			try:
				if hasattr(self.current_tab, 'textChanged'):
					self.current_tab.textChanged.disconnect(self.schedule_update)
			except:
				pass
		
		# 新しいタブに接続
		if index >= 0 and index < len(self.win.tablist):
			self.current_tab = self.win.tablist[index]
			# textChangedシグナルを持つタブのみ接続
			if hasattr(self.current_tab, 'textChanged'):
				self.current_tab.textChanged.connect(self.schedule_update)
				self.update_preview()
			else:
				self.preview_area.setHtml("<p>このタイプのファイルはプレビューできません</p>")
				self.filename_label.setText("プレビュー")
		else:
			self.current_tab = None
			self.preview_area.setHtml("<p>ファイルが開かれていません</p>")
			self.filename_label.setText("プレビュー")
	
	def schedule_update(self):
		"""テキスト変更時に更新をスケジュール（500ms後）"""
		self.update_timer.stop()
		self.update_timer.start(500)
	
	def force_update(self):
		"""即座に更新"""
		self.update_timer.stop()
		self.update_preview()
	
	def update_preview(self):
		"""プレビューを更新"""
		if not self.current_tab:
			return
		
		# ファイル名を取得
		current_index = self.win.tabs.currentIndex()
		if current_index >= 0 and current_index < len(self.win.tabfilelist):
			filename = self.win.tabfilelist[current_index]
			if filename:
				import os
				self.filename_label.setText(f"📄 {os.path.basename(filename)}")
			else:
				self.filename_label.setText("📄 無題")
		
		# Markdownテキストを取得
		markdown_text = self.current_tab.toPlainText()
		
		# HTMLに変換
		self.md.reset()
		html_content = self.md.convert(markdown_text)
		
		# スタイル付きHTMLを作成
		styled_html = self.create_styled_html(html_content)
		
		# プレビューを更新
		self.preview_area.setHtml(styled_html)
	
	def get_color_from_css(self, selector, property_name, default):
		"""CSSファイルから色を取得"""
		try:
			parser = cssutils.CSSParser(validate=False)
			for rule in parser.parseFile(self.win.STYLE["style"]):
				if rule.type == rule.STYLE_RULE:
					if rule.selectorText == selector:
						value = rule.style.getPropertyValue(property_name)
						if value:
							return value
		except:
			pass
		return default
	
	def create_styled_html(self, content):
		"""スタイル付きHTMLを作成"""
		# CSSファイルから色を取得
		bg_color = self.get_color_from_css("QPlainTextEdit", "background-color", "#282c34")
		fg_color = self.get_color_from_css("QPlainTextEdit", "color", "#abb2bf")
		link_color = "#61afef"  # リンク色（固定）
		code_bg = self.get_color_from_css("#explorer QTreeView::item:hover", "background-color", "#2c313c")
		border_color = self.get_color_from_css("QTabWidget::pane", "border-color", "#3e4451")
		
		html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
body {{
	font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
	line-height: 1.6;
	color: {fg_color};
	background-color: {bg_color};
	padding: 20px;
	margin: 0;
}}

h1, h2, h3, h4, h5, h6 {{
	margin-top: 24px;
	margin-bottom: 16px;
	font-weight: 600;
	line-height: 1.25;
	border-bottom: 1px solid {border_color};
	padding-bottom: 0.3em;
}}

h1 {{ font-size: 2em; }}
h2 {{ font-size: 1.5em; }}
h3 {{ font-size: 1.25em; }}

a {{
	color: {link_color};
	text-decoration: none;
}}

a:hover {{
	text-decoration: underline;
}}

code {{
	background-color: {code_bg};
	padding: 2px 6px;
	border-radius: 3px;
	font-family: 'Consolas', 'Monaco', monospace;
	font-size: 0.9em;
}}

pre {{
	background-color: {code_bg};
	padding: 16px;
	border-radius: 6px;
	overflow-x: auto;
	border: 1px solid {border_color};
}}

pre code {{
	background-color: transparent;
	padding: 0;
}}

blockquote {{
	margin: 0;
	padding: 0 1em;
	color: {fg_color};
	opacity: 0.8;
	border-left: 4px solid {link_color};
}}

table {{
	border-collapse: collapse;
	width: 100%;
	margin: 16px 0;
}}

table th, table td {{
	border: 1px solid {border_color};
	padding: 8px 12px;
}}

table th {{
	background-color: {code_bg};
	font-weight: 600;
}}

table tr:nth-child(even) {{
	background-color: {code_bg};
	opacity: 0.5;
}}

ul, ol {{
	padding-left: 2em;
}}

li {{
	margin: 0.25em 0;
}}

hr {{
	border: none;
	border-top: 1px solid {border_color};
	margin: 24px 0;
}}

img {{
	max-width: 100%;
	height: auto;
}}
</style>
</head>
<body>
{content}
</body>
</html>
"""
		return html
