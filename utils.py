"""共通ユーティリティモジュール"""
import os
import subprocess
from PySide6.QtWidgets import QTextEdit, QTreeWidgetItem, QWidget, QHBoxLayout, QLabel
from PySide6.QtGui import QColor, QTextOption, QFontMetrics
from PySide6.QtCore import Qt


def get_startupinfo():
	"""Windows用のSTARTUPINFOを返す。非Windowsの場合はNone"""
	if os.name == 'nt':
		si = subprocess.STARTUPINFO()
		si.dwFlags = subprocess.STARTF_USESHOWWINDOW
		return si
	return None


def run_subprocess(args, **kwargs):
	"""OS共通のsubprocess.run ラッパー"""
	si = get_startupinfo()
	if si:
		kwargs['startupinfo'] = si
	return subprocess.run(args, **kwargs)


def build_lps(pattern: str) -> list[int]:
	"""KMP検索のLPS配列を構築"""
	lps = [0] * len(pattern)
	j = 0

	for i in range(1, len(pattern)):
		while j > 0 and pattern[i] != pattern[j]:
			j = lps[j - 1]

		if pattern[i] == pattern[j]:
			j += 1
			lps[i] = j

	return lps


def kmp_search(text: str, pattern: str) -> list[int]:
	"""text中のpatternの開始位置をすべて返す"""
	if not pattern:
		return []

	lps = build_lps(pattern)
	result = []

	j = 0
	for i in range(len(text)):
		while j > 0 and text[i] != pattern[j]:
			j = lps[j - 1]

		if text[i] == pattern[j]:
			j += 1

		if j == len(pattern):
			result.append(i - j + 1)
			j = lps[j - 1]

	return result


def navigate_to_position(win, tab, line_num, col):
	"""エディタタブの指定位置にカーソルを移動"""
	index = win.tablist.index(tab)
	win.tabs.setCurrentIndex(index)
	cursor = tab.textCursor()
	cursor.movePosition(cursor.MoveOperation.Start)
	cursor.movePosition(cursor.MoveOperation.Down, cursor.MoveMode.MoveAnchor, line_num - 1)
	cursor.movePosition(cursor.MoveOperation.Right, cursor.MoveMode.MoveAnchor, col)
	tab.setTextCursor(cursor)
	tab.setFocus()


def apply_text_options(tab, wrap=False):
	"""タブにQTextOptionを適用"""
	options = QTextOption()
	options.setTabStopDistance(QFontMetrics(tab.font()).horizontalAdvance(' ') * 4)
	options.setWrapMode(QTextOption.WrapMode.WordWrap if wrap else QTextOption.WrapMode.NoWrap)
	tab.document().setDefaultTextOption(options)


def reset_highlighter(highlighter, style, filename=None):
	"""ハイライタのテーマをリセット"""
	highlighter.formats.clear()
	highlighter.replace.clear()
	highlighter.style = style
	highlighter.set_filetype(filename)
	highlighter.rehighlight()


def build_search_highlights(tab, pattern, indices, search_bg_color):
	"""検索のExtraSelectionsを構築"""
	if not pattern or not indices:
		return []
	extra_selections = []
	for index in indices:
		selection = QTextEdit.ExtraSelection()
		selection.format.setBackground(QColor(search_bg_color))
		cursor = tab.textCursor()
		cursor.setPosition(index)
		cursor.movePosition(cursor.MoveOperation.Right, cursor.MoveMode.KeepAnchor, len(pattern))
		selection.cursor = cursor
		extra_selections.append(selection)
	return extra_selections


def build_search_result_line(text, index, pattern, search_bg_color):
	"""検索結果の行テキストをリッチテキストとして構築。(highlighted_text, line_num, col)を返す"""
	line_start = text.rfind('\n', 0, index) + 1
	line_end = text.find('\n', index)
	if line_end == -1:
		line_end = len(text)
	line_text = text[line_start:line_end]
	line_text_stripped = line_text.lstrip()

	pattern_pos = index - line_start - (len(line_text) - len(line_text_stripped))

	if index - line_start >= 20:
		line_text_stripped = f"...{line_text_stripped[index-line_start-20:]}"
		pattern_pos = pattern_pos - (index - line_start - 20) + 3

	line_num = text[:index].count('\n') + 1

	before = line_text_stripped[:pattern_pos]
	match = line_text_stripped[pattern_pos:pattern_pos+len(pattern)]
	after = line_text_stripped[pattern_pos+len(pattern):]
	highlighted_text = f'{before}<span style="background-color: {search_bg_color};">{match}</span>{after}'

	return highlighted_text, line_num, index - line_start


def perform_search_across_tabs(win, tree, pattern, create_item_widget=None):
	"""全タブで検索を実行し、結果をツリーに表示する。

	Args:
		win: ウィンドウオブジェクト
		tree: QTreeWidget
		pattern: 検索パターン
		create_item_widget: カスタムウィジェット作成関数 (highlighted_text, result_index) -> QWidget or None

	Returns:
		list of (tab, index, line_num, col, pattern_len) tuples
	"""
	tree.clear()
	root = []
	all_results = []
	search_bg = win.STYLE["theme"]["search"]["background"]

	# すべてのタブのハイライトをクリア
	for tab in win.tablist:
		tab.setExtraSelections([])

	for tab in win.tablist:
		root.append(QTreeWidgetItem(tree, [tab.file_path if hasattr(tab, "file_path") else "Untitled"]))
		text = tab.document().toPlainText()
		indices = kmp_search(text, pattern)

		# エディタ内でハイライト表示
		tab.setExtraSelections(build_search_highlights(tab, pattern, indices, search_bg))

		for i, index in enumerate(indices):
			highlighted_text, line_num, col = build_search_result_line(text, index, pattern, search_bg)

			item = QTreeWidgetItem(root[-1])

			if create_item_widget:
				widget = create_item_widget(highlighted_text, len(all_results))
			else:
				widget = QWidget()
				h_layout = QHBoxLayout(widget)
				h_layout.setContentsMargins(0, 0, 0, 0)
				label = QLabel(highlighted_text)
				label.setTextFormat(Qt.TextFormat.RichText)
				h_layout.addWidget(label)

			tree.setItemWidget(item, 0, widget)
			item.setData(0, Qt.UserRole, (tab, line_num, col))
			all_results.append((tab, index, line_num, col, len(pattern)))

	tree.expandAll()
	tree.show()
	return all_results
