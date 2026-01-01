from PySide6.QtWidgets import *
from PySide6.QtGui import QAction, QActionGroup
import os
#from main import window as win

class MenuBar:
	def __init__(self, window=None):
		self.window = window
		self.menubar = self.window.menuBar()
		self.filemenu()
		self.editmenu()
		self.runmenu()
		self.viewmenu()
	
	def filemenu(self):
		self.file_menu = self.menubar.addMenu("ファイル(&F)")
		self.file_menu.setFont(self.window.FONT)

		new_action = QAction("新しいテキストファイル", self.window)
		new_action.setShortcut("Ctrl+N")
		new_action.triggered.connect(lambda: self.window.newtab(name="Untitled"))

		new_win_action = QAction("新しいウィンドウ", self.window)
		new_win_action.setShortcut("Ctrl+Shift+N")
		new_win_action.triggered.connect(self.window.new_window)

		open_action = QAction("ファイルを開く...", self.window)
		open_action.setShortcut("Ctrl+O")
		open_action.triggered.connect(self.window.open_file)

		open_folder_action = QAction("フォルダーを開く...", self.window)
		open_folder_action.setShortcut("Ctrl+K Ctrl+O")
		open_folder_action.triggered.connect(self.window.open_folder)

		save_action = QAction("保存", self.window)
		save_action.setShortcut("Ctrl+S")
		save_action.triggered.connect(self.window.save_file)

		save_as_action = QAction("名前を付けて保存", self.window)
		save_as_action.setShortcut("Ctrl+Shift+S")
		save_as_action.triggered.connect(self.window.save_file_as)

		close_tab_action = QAction("タブを閉じる", self.window)
		close_tab_action.triggered.connect(lambda: self.window.close_tab(self.window.tabs.currentIndex()))

		close_all_action = QAction("すべてのタブを閉じる", self.window)
		close_all_action.triggered.connect(lambda: [self.window.close_tab(i) for i in reversed(range(self.window.tabs.count()))])

		exit_action = QAction("終了", self.window)
		exit_action.triggered.connect(self.window.close)

		self.file_menu.addAction(new_action)
		self.file_menu.addAction(new_win_action)
		self.file_menu.addSeparator()
		self.file_menu.addAction(open_action)
		self.file_menu.addAction(open_folder_action)
		self.file_menu.addSeparator()
		self.file_menu.addAction(save_action)
		self.file_menu.addAction(save_as_action)
		self.file_menu.addSeparator()
		self.file_menu.addAction(close_tab_action)
		self.file_menu.addAction(close_all_action)
		self.file_menu.addAction(exit_action)

	def editmenu(self):
		self.edit_menu = self.menubar.addMenu("編集(&E)")
		self.edit_menu.setFont(self.window.FONT)

		undo_action = QAction("元に戻す", self.window)
		undo_action.setShortcut("Ctrl+Z")
		undo_action.triggered.connect(lambda: self.window.tablist[self.window.tabs.currentIndex()].undo())

		redo_action = QAction("やり直し", self.window)
		redo_action.setShortcut("Ctrl+Y")
		redo_action.triggered.connect(lambda: self.window.tablist[self.window.tabs.currentIndex()].redo())

		cut_action = QAction("切り取り", self.window)
		cut_action.setShortcut("Ctrl+X")
		cut_action.triggered.connect(lambda: self.window.tablist[self.window.tabs.currentIndex()].cut())

		copy_action = QAction("コピー", self.window)
		copy_action.setShortcut("Ctrl+C")
		copy_action.triggered.connect(lambda: self.window.tablist[self.window.tabs.currentIndex()].copy())

		paste_action = QAction("貼り付け", self.window)
		paste_action.setShortcut("Ctrl+V")
		paste_action.triggered.connect(lambda: self.window.tablist[self.window.tabs.currentIndex()].paste())

		select_all_action = QAction("すべて選択", self.window)
		select_all_action.setShortcut("Ctrl+A")
		select_all_action.triggered.connect(lambda: self.window.tablist[self.window.tabs.currentIndex()].selectAll())

		search_action = QAction("検索", self.window)
		search_action.setShortcut("Ctrl+F")
		search_action.triggered.connect(self.window.open_search_sidebar)
		
		replace_action = QAction("置換", self.window)
		replace_action.setShortcut("Ctrl+H")
		replace_action.triggered.connect(self.window.open_search_sidebar)

		self.edit_menu.addAction(undo_action)
		self.edit_menu.addAction(redo_action)
		self.edit_menu.addSeparator()
		self.edit_menu.addAction(cut_action)
		self.edit_menu.addAction(copy_action)
		self.edit_menu.addAction(paste_action)
		self.edit_menu.addSeparator()
		self.edit_menu.addAction(select_all_action)
		self.edit_menu.addSeparator()
		self.edit_menu.addAction(search_action)
		self.edit_menu.addAction(replace_action)

	def viewmenu(self):
		self.view_menu = self.menubar.addMenu("表示(&V)")
		self.view_menu.setFont(self.window.FONT)

		fullscreen_action = QAction("全画面表示", self.window)
		fullscreen_action.setShortcut("F11")
		fullscreen_action.setCheckable(True)
		fullscreen_action.triggered.connect(self.window.toggle_fullscreen)

		wrap_action = QAction("右端での折り返し", self.window)
		wrap_action.setCheckable(True)
		wrap_action.setChecked(self.window.tablist[self.window.tabs.currentIndex()].lineWrapMode() != QTextEdit.NoWrap)
		wrap_action.triggered.connect(self.window.toggle_wrap)

		self.view_menu.addAction(fullscreen_action)
		self.view_menu.addAction(wrap_action)
		
		self.theme_menu = self.view_menu.addMenu("配色テーマ")
		self.theme_menu.setFont(self.window.FONT)

		self.theme_action_group = QActionGroup(self.window)
		self.theme_action_group.setExclusive(True)

		themes_dir = f"{self.window.DIR}/themes"
		theme_files = []
		for root, dirs, files in os.walk(themes_dir):
			for file in files:
				if file.endswith('.json'):
					rel_path = os.path.relpath(os.path.join(root, file), themes_dir)
					theme_files.append(rel_path)
		
		current_theme = self.window.STYLE if isinstance(self.window.STYLE, str) else "monokai"
		
		for theme_file in sorted(theme_files):
			theme_name = os.path.splitext(theme_file)[0]
			theme_action = QAction(theme_name, self.window)
			theme_action.setCheckable(True)
			theme_action.triggered.connect(lambda checked, t=theme_name: self.window.change_theme(t))
			
			if theme_name == current_theme:
				theme_action.setChecked(True)
			
			self.theme_action_group.addAction(theme_action)
			self.theme_menu.addAction(theme_action)

	def runmenu(self):
		self.run_menu = self.menubar.addMenu("実行(&R)")
		self.run_menu.setFont(self.window.FONT)

		run_action = QAction("デバッグなしで実行", self.window)
		run_action.setShortcut("F5")
		run_action.triggered.connect(self.window.run_code)

		new_terminal_action = QAction("新しいターミナル", self.window)
		new_terminal_action.setShortcut("Ctrl+Shift+@")
		new_terminal_action.triggered.connect(self.window.ConsoleGroup.add_terminal)

		self.run_menu.addAction(run_action)
		self.run_menu.addSeparator()
		self.run_menu.addAction(new_terminal_action)