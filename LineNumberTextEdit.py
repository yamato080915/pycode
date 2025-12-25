from PySide6.QtWidgets import QPlainTextEdit, QWidget, QTextEdit
from PySide6.QtGui import QPainter, QColor, QTextFormat
from PySide6.QtCore import Qt, QRect, QSize, QEvent


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
    
    def sizeHint(self):
        return QSize(self.editor.line_number_area_width(), 0)
    
    def paintEvent(self, event):
        self.editor.line_number_area_paint_event(event)


class LineNumberTextEdit(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TextBox")
        
        # 行番号表示用のウィジェット
        self.line_number_area = LineNumberArea(self)
        
        # シグナル接続
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        
        # 初期化
        self.update_line_number_area_width(0)
        self.highlight_current_line()
    
    def get_line_number_bg_color(self):
        editor_bg = self.palette().color(self.backgroundRole())
        return editor_bg.darker(110)
    
    def get_line_number_fg_color(self):
        text_color = self.palette().color(self.foregroundRole())
        # 通常の行番号は少し薄く
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
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)
    
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
        
        # 現在の行番号
        current_line = self.textCursor().blockNumber()
        
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                
                # 現在の行は強調表示
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
