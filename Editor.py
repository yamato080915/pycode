from PySide6.QtWidgets import QPlainTextEdit, QWidget, QTextEdit
from PySide6.QtGui import QPainter, QColor, QTextFormat, QFont, QPen
from PySide6.QtCore import Qt, QRect, QSize, QEvent

class MiniMap(QWidget):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.editor = parent
		self.setObjectName("MiniMap")
		self.scale_factor = 0.1
		self.viewport_color = QColor(100, 100, 100, 50)
		self.scroll_offset = 0
		
	def paintEvent(self, event):
		if not self.editor:
			return
			
		painter = QPainter(self)
		
		bg_color = self.editor.palette().color(self.editor.backgroundRole())
		painter.fillRect(self.rect(), bg_color.darker(105))
		
		line_height = 2
		total_blocks = self.editor.document().blockCount()
		total_content_height = total_blocks * line_height
		
		if total_content_height > self.height():
			first_visible = self.editor.firstVisibleBlock().blockNumber()
			scroll_ratio = first_visible / max(1, total_blocks - 1)
			max_scroll = total_content_height - self.height()
			self.scroll_offset = int(scroll_ratio * max_scroll)
		else:
			self.scroll_offset = 0
		
		start_block_num = int(self.scroll_offset / line_height)
		block = self.editor.document().findBlockByNumber(start_block_num)
		y_pos = -(self.scroll_offset % line_height)
		
		default_color = self.editor.palette().color(self.editor.foregroundRole())
		default_color.setAlpha(200)
		
		color_cache = {}
		
		while block.isValid() and y_pos < self.height():
			if y_pos + line_height >= 0:
				text = block.text()
				if text:
					layout = block.layout()
					formats = layout.formats() if layout else []
					
					x_pos = 2
					char_index = 0
					current_format_idx = 0
					
					for char in text[:min(len(text), 80)]:
						if not char.isspace():
							color = default_color
							
							for i in range(current_format_idx, len(formats)):
								fmt_range = formats[i]
								if char_index < fmt_range.start:
									break
								if char_index < fmt_range.start + fmt_range.length:
									current_format_idx = i
									fmt_color = fmt_range.format.foreground().color()
									if fmt_color.isValid():
										color_key = (fmt_color.red(), fmt_color.green(), fmt_color.blue())
										if color_key not in color_cache:
											cached_color = QColor(fmt_color)
											cached_color.setAlpha(200)
											color_cache[color_key] = cached_color
										color = color_cache[color_key]
									break
							
							painter.setPen(color)
							painter.drawPoint(x_pos, y_pos + 1)
							x_pos += 1
						elif char == '\t':
							x_pos += 2
						else:
							x_pos += 1
						char_index += 1
			
			y_pos += line_height
			block = block.next()
		
		self.draw_viewport_indicator(painter, line_height)
	
	def draw_viewport_indicator(self, painter, line_height):
		if not self.editor:
			return
		
		first_visible = self.editor.firstVisibleBlock().blockNumber()
		last_visible = self.editor.cursorForPosition(
			self.editor.viewport().rect().bottomRight()
		).blockNumber()
		
		start_y = first_visible * line_height - self.scroll_offset
		height = (last_visible - first_visible + 1) * line_height
		
		painter.fillRect(0, start_y, self.width(), height, self.viewport_color)
		
		painter.setPen(QPen(QColor(150, 150, 150, 100), 1))
		painter.drawRect(0, start_y, self.width() - 1, height)
	
	def mousePressEvent(self, event):
		self.scroll_editor_from_position(event.pos().y())
	
	def mouseMoveEvent(self, event):
		if event.buttons() & Qt.MouseButton.LeftButton:
			self.scroll_editor_from_position(event.pos().y())
	
	def scroll_editor_from_position(self, y_pos):
		editor = self.editor
		if not editor:
			return

		doc = editor.document()
		scrollbar = editor.verticalScrollBar()

		total_blocks = doc.blockCount()
		if total_blocks <= 1:
			return

		ratio = y_pos / max(1, self.height())
		ratio = max(0.0, min(1.0, ratio))

		max_scroll = scrollbar.maximum()
		scrollbar.setValue(int(ratio * max_scroll))

class LineNumberArea(QWidget):
	def __init__(self, editor):
		super().__init__(editor)
		self.editor = editor
	
	def sizeHint(self):
		return QSize(self.editor.line_number_area_width(), 0)
	
	def paintEvent(self, event):
		self.editor.line_number_area_paint_event(event)

class Editor(QPlainTextEdit):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.setObjectName("TextBox")
		
		self.line_number_area = LineNumberArea(self)
		
		self.minimap = MiniMap(self)
		self._minimap_update_pending = False
		
		self.blockCountChanged.connect(self.update_line_number_area_width)
		self.updateRequest.connect(self.update_line_number_area)
		self.cursorPositionChanged.connect(self.highlight_current_line)
		
		self.textChanged.connect(self.schedule_minimap_update)
		self.verticalScrollBar().valueChanged.connect(self.update_minimap)
		
		self.update_line_number_area_width(0)
		self.highlight_current_line()
	
	def get_line_number_bg_color(self):
		editor_bg = self.palette().color(self.backgroundRole())
		return editor_bg.darker(110)
	
	def get_line_number_fg_color(self):
		text_color = self.palette().color(self.foregroundRole())
		text_color.setAlpha(160)
		return text_color
	
	def get_current_line_number_fg_color(self):
		return self.palette().color(self.foregroundRole())
	
	def get_current_line_bg_color(self):
		editor_bg = self.palette().color(self.backgroundRole())
		return editor_bg.lighter(115)
	
	def line_number_area_width(self):
		digits = 1
		max_num = max(1, self.blockCount())
		while max_num >= 10:
			max_num //= 10
			digits += 1
		
		space = 3 + self.fontMetrics().horizontalAdvance('9') * digits + 8
		return space
	
	def update_line_number_area_width(self, _):
		self.setViewportMargins(self.line_number_area_width(), 0, 100, 0)
	
	def update_line_number_area(self, rect, dy):
		if dy:
			self.line_number_area.scroll(0, dy)
		else:
			self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
		
		if rect.contains(self.viewport().rect()):
			self.update_line_number_area_width(0)
	
	def resizeEvent(self, event):
		super().resizeEvent(event)
		
		cr = self.contentsRect()

		self.line_number_area.setGeometry(
			QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height())
		)
		
		self.minimap.setGeometry(
			QRect(cr.right() - 100, cr.top(), 100, cr.height())
		)
	
	def changeEvent(self, event):
		if event.type() in (QEvent.Type.StyleChange, QEvent.Type.PaletteChange):
			self.line_number_area.update()
			self.highlight_current_line()
		super().changeEvent(event)
	
	def line_number_area_paint_event(self, event):
		painter = QPainter(self.line_number_area)
		painter.fillRect(event.rect(), self.get_line_number_bg_color())
		
		block = self.firstVisibleBlock()
		block_number = block.blockNumber()
		top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
		bottom = top + self.blockBoundingRect(block).height()
		
		current_line = self.textCursor().blockNumber()
		
		while block.isValid() and top <= event.rect().bottom():
			if block.isVisible() and bottom >= event.rect().top():
				number = str(block_number + 1)
				
				if block_number == current_line:
					painter.setPen(self.get_current_line_number_fg_color())
				else:
					painter.setPen(self.get_line_number_fg_color())
				
				painter.drawText(
					0, int(top), 
					self.line_number_area.width() - 5, 
					self.fontMetrics().height(),
					Qt.AlignmentFlag.AlignRight, 
					number
				)
			
			block = block.next()
			top = bottom
			bottom = top + self.blockBoundingRect(block).height()
			block_number += 1
	
	def highlight_current_line(self):
		extra_selections = []
		
		if not self.isReadOnly():
			selection = QTextEdit.ExtraSelection()
			
			selection.format.setBackground(self.get_current_line_bg_color())
			selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
			selection.cursor = self.textCursor()
			selection.cursor.clearSelection()
			extra_selections.append(selection)
		
		self.setExtraSelections(extra_selections)
	
	def schedule_minimap_update(self):
		if not self._minimap_update_pending:
			self._minimap_update_pending = True
			from PySide6.QtCore import QTimer
			QTimer.singleShot(50, self._do_minimap_update)
	
	def _do_minimap_update(self):
		self._minimap_update_pending = False
		self.minimap.update()
	
	def update_minimap(self):
		self.minimap.update()
