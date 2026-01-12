from PySide6.QtWidgets import QPlainTextEdit, QWidget, QTextEdit
from PySide6.QtGui import QPainter, QColor, QTextFormat, QFont, QPen, QPolygon
from PySide6.QtCore import Qt, QRect, QSize, QEvent, QPoint

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

class FoldingArea(QWidget):
	def __init__(self, editor):
		super().__init__(editor)
		self.editor = editor
		self.setMouseTracking(True)
		self.hover_line = -1
	
	def sizeHint(self):
		return QSize(16, 0)
	
	def paintEvent(self, event):
		self.editor.folding_area_paint_event(event)
	
	def mousePressEvent(self, event):
		if event.button() == Qt.MouseButton.LeftButton:
			self.editor.toggle_fold_at_pos(event.pos())
	
	def mouseMoveEvent(self, event):
		line_num = self.editor.get_line_number_at_pos(event.pos())
		if line_num != self.hover_line:
			self.hover_line = line_num
			self.update()
	
	def leaveEvent(self, event):
		self.hover_line = -1
		self.update()

class Editor(QPlainTextEdit):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.setObjectName("TextBox")
		
		self.line_number_area = LineNumberArea(self)
		self.folding_area = FoldingArea(self)
		
		self.folded_blocks = {}  # {start_line: end_line}
		
		self.minimap = MiniMap(self)
		self._minimap_update_pending = False
		
		self.blockCountChanged.connect(self.update_line_number_area_width)
		self.updateRequest.connect(self.update_line_number_area)
		self.cursorPositionChanged.connect(self.highlight_current_line)
		
		self.textChanged.connect(self.schedule_minimap_update)
		self.textChanged.connect(self.update_folding_areas)
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
	
	def folding_area_width(self):
		return 16
	
	def update_line_number_area_width(self, _):
		self.setViewportMargins(self.line_number_area_width() + self.folding_area_width(), 0, 100, 0)
	
	def update_line_number_area(self, rect, dy):
		if dy:
			self.line_number_area.scroll(0, dy)
			self.folding_area.scroll(0, dy)
		else:
			self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
			self.folding_area.update(0, rect.y(), self.folding_area.width(), rect.height())
		
		if rect.contains(self.viewport().rect()):
			self.update_line_number_area_width(0)
	
	def resizeEvent(self, event):
		super().resizeEvent(event)
		
		cr = self.contentsRect()

		self.line_number_area.setGeometry(
			QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height())
		)
		
		self.folding_area.setGeometry(
			QRect(cr.left() + self.line_number_area_width(), cr.top(), 
				  self.folding_area_width(), cr.height())
		)
		
		self.minimap.setGeometry(
			QRect(cr.right() - 100, cr.top(), 100, cr.height())
		)
	
	def changeEvent(self, event):
		if event.type() in (QEvent.Type.StyleChange, QEvent.Type.PaletteChange):
			self.line_number_area.update()
			self.folding_area.update()
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
	
	# ============== Code Folding Methods ==============
	
	def get_indent_level(self, text):
		"""テキストのインデントレベルを取得"""
		indent = 0
		for char in text:
			if char == '\t':
				indent += 4
			elif char == ' ':
				indent += 1
			else:
				break
		return indent
	
	def is_foldable_line(self, block_number):
		"""折りたたみ可能な行かどうかを判定"""
		block = self.document().findBlockByNumber(block_number)
		if not block.isValid():
			return False, -1
		
		text = block.text()
		stripped = text.strip()
		
		# 空行やコメントのみの行は折りたたみ不可
		if not stripped or stripped.startswith('#'):
			return False, -1
		
		# コロンで終わる行（関数、クラス、if文など）をチェック
		if not stripped.endswith(':'):
			return False, -1
		
		current_indent = self.get_indent_level(text)
		next_block = block.next()
		
		# 次の行が存在し、インデントが深い場合は折りたたみ可能
		if next_block.isValid():
			next_text = next_block.text().strip()
			if next_text:  # 空行でない
				next_indent = self.get_indent_level(next_block.text())
				if next_indent > current_indent:
					# 折りたたみ範囲の終端を見つける
					end_line = self.find_fold_end(block_number, current_indent)
					return True, end_line
		
		return False, -1
	
	def find_fold_end(self, start_line, base_indent):
		"""折りたたみ範囲の終端行を見つける"""
		block = self.document().findBlockByNumber(start_line + 1)
		end_line = start_line
		
		while block.isValid():
			text = block.text()
			stripped = text.strip()
			
			# 空行はスキップ
			if not stripped:
				block = block.next()
				end_line += 1
				continue
			
			indent = self.get_indent_level(text)
			
			# インデントが同じかそれより浅い場合は終了
			if indent <= base_indent:
				break
			
			end_line += 1
			block = block.next()
		
		return end_line
	
	def toggle_fold_at_pos(self, pos):
		"""指定位置の折りたたみを切り替え"""
		block_number = self.get_line_number_at_pos(pos)
		if block_number < 0:
			return
		
		# すでに折りたたまれているかチェック
		if block_number in self.folded_blocks:
			self.unfold(block_number)
		else:
			# 折りたたみ可能かチェック
			is_foldable, end_line = self.is_foldable_line(block_number)
			if is_foldable:
				self.fold(block_number, end_line)
	
	def fold(self, start_line, end_line):
		"""指定範囲を折りたたむ"""
		self.folded_blocks[start_line] = end_line
		
		# start_line + 1 から end_line までを非表示にする
		for line_num in range(start_line + 1, end_line + 1):
			block = self.document().findBlockByNumber(line_num)
			if block.isValid():
				block.setVisible(False)
		
		self.document().markContentsDirty(
			self.document().findBlockByNumber(start_line).position(),
			self.document().findBlockByNumber(end_line).position()
		)
		self.viewport().update()
		self.folding_area.update()
		self.update_minimap()
	
	def unfold(self, start_line):
		"""指定行の折りたたみを展開"""
		if start_line not in self.folded_blocks:
			return
		
		end_line = self.folded_blocks[start_line]
		del self.folded_blocks[start_line]
		
		# 行を再表示
		for line_num in range(start_line + 1, end_line + 1):
			block = self.document().findBlockByNumber(line_num)
			if block.isValid():
				block.setVisible(True)
		
		self.document().markContentsDirty(
			self.document().findBlockByNumber(start_line).position(),
			self.document().findBlockByNumber(end_line).position()
		)
		self.viewport().update()
		self.folding_area.update()
		self.update_minimap()
		self.update_minimap()
	
	def get_line_number_at_pos(self, pos):
		"""Y座標から行番号を取得"""
		block = self.firstVisibleBlock()
		block_number = block.blockNumber()
		top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
		bottom = top + self.blockBoundingRect(block).height()
		
		while block.isValid():
			if top <= pos.y() <= bottom:
				return block_number
			
			block = block.next()
			top = bottom
			bottom = top + self.blockBoundingRect(block).height()
			block_number += 1
		
		return -1
	
	def update_folding_areas(self):
		"""折りたたみ領域を更新"""
		self.folding_area.update()
	
	def folding_area_paint_event(self, event):
		"""折りたたみエリアの描画"""
		painter = QPainter(self.folding_area)
		painter.fillRect(event.rect(), self.get_line_number_bg_color())
		
		block = self.firstVisibleBlock()
		block_number = block.blockNumber()
		top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
		bottom = top + self.blockBoundingRect(block).height()
		
		icon_size = 8
		icon_margin = 4
		
		while block.isValid() and top <= event.rect().bottom():
			if block.isVisible() and bottom >= event.rect().top():
				is_foldable, end_line = self.is_foldable_line(block_number)
				is_folded = block_number in self.folded_blocks
				
				if is_foldable or is_folded:
					center_y = int(top + self.fontMetrics().height() / 2)
					center_x = self.folding_area.width() // 2
					
					# ホバー時の背景
					if block_number == self.folding_area.hover_line:
						hover_rect = QRect(
							center_x - icon_size, 
							center_y - icon_size,
							icon_size * 2, 
							icon_size * 2
						)
						painter.fillRect(hover_rect, QColor(100, 100, 100, 50))
					
					# 矢印アイコンを描画
					painter.setPen(QPen(self.get_line_number_fg_color(), 1.5))
					
					if is_folded:
						# 右向き矢印（折りたたまれている）
						arrow = QPolygon([
							QPoint(center_x - 2, center_y - 3),
							QPoint(center_x + 2, center_y),
							QPoint(center_x - 2, center_y + 3)
						])
					else:
						# 下向き矢印（展開されている）
						arrow = QPolygon([
							QPoint(center_x - 3, center_y - 2),
							QPoint(center_x, center_y + 2),
							QPoint(center_x + 3, center_y - 2)
						])
					
					painter.drawPolyline(arrow)
			
			block = block.next()
			top = bottom
			bottom = top + self.blockBoundingRect(block).height()
			block_number += 1
