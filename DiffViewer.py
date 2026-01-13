from PySide6.QtWidgets import QWidget, QHBoxLayout
from PySide6.QtGui import QTextBlockFormat, QColor, QFont
from Editor import Editor
import difflib

class DiffViewer(QWidget):
	def __init__(self, window=None):
		super().__init__()
		self.win = window
		self.setObjectName("DiffViewer")
		layout = QHBoxLayout(self)
		self.difftxt1 = Editor(self)
		self.difftxt1.setReadOnly(True)
		self.difftxt2 = Editor(self)
		self.difftxt2.setReadOnly(True)
		layout.addWidget(self.difftxt1)
		layout.addWidget(self.difftxt2)
		self.setLayout(layout)
		
		# スクロールを同期
		self.difftxt1.verticalScrollBar().valueChanged.connect(
			self.difftxt2.verticalScrollBar().setValue
		)
		self.difftxt2.verticalScrollBar().valueChanged.connect(
			self.difftxt1.verticalScrollBar().setValue
		)
		self.difftxt1.horizontalScrollBar().valueChanged.connect(
			self.difftxt2.horizontalScrollBar().setValue
		)
		self.difftxt2.horizontalScrollBar().valueChanged.connect(
			self.difftxt1.horizontalScrollBar().setValue
		)
	
	def _align_texts(self, text1_lines, text2_lines, opcodes):
		"""テキストを整列し、各行のタイプ（追加/削除/変更/等しい）を返す"""
		leftlines = []
		rightlines = []
		lefttypes = []
		righttypes = []
		
		for tag, i1, i2, j1, j2 in opcodes:
			if tag == 'equal':
				for i in range(i1, i2):
					leftlines.append(text1_lines[i])
					rightlines.append(text2_lines[j1 + i - i1])
					lefttypes.append('equal')
					righttypes.append('equal')
			elif tag == 'delete':
				for i in range(i1, i2):
					leftlines.append(text1_lines[i])
					rightlines.append('')
					lefttypes.append('delete')
					righttypes.append('empty')
			elif tag == 'insert':
				for j in range(j1, j2):
					leftlines.append('')
					rightlines.append(text2_lines[j])
					lefttypes.append('empty')
					righttypes.append('insert')
			elif tag == 'replace':
				left_count = i2 - i1
				right_count = j2 - j1
				max_count = max(left_count, right_count)
				
				for k in range(max_count):
					if k < left_count:
						leftlines.append(text1_lines[i1 + k])
						lefttypes.append('replace')
					else:
						leftlines.append('')
						lefttypes.append('empty')
					
					if k < right_count:
						rightlines.append(text2_lines[j1 + k])
						righttypes.append('replace')
					else:
						rightlines.append('')
						righttypes.append('empty')
		
		return leftlines, rightlines, lefttypes, righttypes
	
	def diff_texts(self, text1: str, text2: str):
		text1_lines = text1.splitlines()
		text2_lines = text2.splitlines()
		
		text1_lines_stripped = [line.lstrip() for line in text1_lines]
		text2_lines_stripped = [line.lstrip() for line in text2_lines]
		
		matcher = difflib.SequenceMatcher(None, text1_lines_stripped, text2_lines_stripped)
		opcodes = matcher.get_opcodes()
		
		leftlines, rightlines, lefttypes, righttypes = self._align_texts(text1_lines, text2_lines, opcodes)
		self.difftxt1.setPlainText('\n'.join(leftlines))
		self.difftxt2.setPlainText('\n'.join(rightlines))
		
		# 再ハイライト用に保存
		self.lefttypes = lefttypes
		self.righttypes = righttypes
		
		self._apply_highlighting(self.difftxt1, lefttypes, "left")
		self._apply_highlighting(self.difftxt2, righttypes, "right")
	
	def reapply_theme(self):
		"""テーマ変更時に差分ハイライトを再適用"""
		if hasattr(self, 'lefttypes') and hasattr(self, 'righttypes'):
			self._apply_highlighting(self.difftxt1, self.lefttypes, "left")
			self._apply_highlighting(self.difftxt2, self.righttypes, "right")
	
	def _apply_highlighting(self, editor, line_types, side):
		cursor = editor.textCursor()
		cursor.movePosition(cursor.MoveOperation.Start)
		
		for i, line_type in enumerate(line_types):
			block_fmt = QTextBlockFormat()
			
			if line_type == 'delete':
				block_fmt.setBackground(QColor(*self.win.STYLE["theme"]["diff"]["delete"]))
			elif line_type == 'insert':
				block_fmt.setBackground(QColor(*self.win.STYLE["theme"]["diff"]["insert"]))
			elif line_type == 'replace':
				if side == "left":
					block_fmt.setBackground(QColor(*self.win.STYLE["theme"]["diff"]["delete"]))
				else:
					block_fmt.setBackground(QColor(*self.win.STYLE["theme"]["diff"]["insert"]))
			elif line_type == 'empty':
				block_fmt.setBackground(QColor(*self.win.STYLE["theme"]["diff"]["empty"]))
			
			if line_type != 'equal':
				cursor.setBlockFormat(block_fmt)
			
			cursor.movePosition(cursor.MoveOperation.Down)
			cursor.movePosition(cursor.MoveOperation.StartOfLine)

if __name__ == "__main__":
	from PySide6.QtWidgets import QApplication
	import sys

	app = QApplication(sys.argv)
	viewer = DiffViewer()
	viewer.setFont(QFont("Consolas", 11))
	viewer.diff_texts(open("main.py", encoding="utf-8").read(), open("mainco.py", encoding="utf-8").read())
	viewer.show()
	sys.exit(app.exec())