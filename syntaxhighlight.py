from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PySide6.QtCore import QTimer
from pygments.lexers import get_lexer_for_filename, get_lexer_by_name
from pygments.token import Token
import json

class PygmentsSyntaxHighlight(QSyntaxHighlighter):
	def __init__(self, parent=None, filename = "*.txt", style=None):
		super().__init__(parent)
		self.style = style
		self.set_filetype(filename)
		self.token_cache = {}
		
		self.tokenize_timer = QTimer()
		self.tokenize_timer.setSingleShot(True)
		self.tokenize_timer.setInterval(1000)
		self.tokenize_timer.timeout.connect(self.tokenize)
		
		self.document().contentsChanged.connect(self.schedule_tokenize)
	
	def schedule_tokenize(self):
		self.tokenize_timer.stop()
		self.tokenize_timer.start()
	
	def set_filetype(self, filename):
		try:
			self.lexer = get_lexer_for_filename(filename)
		except :
			self.lexer = get_lexer_by_name("text")
		lang = str(self.lexer).lstrip("<pygments.lexers.").rstrip("Lexer>")
		self.formats = {}
		self.setup_formats(lang)

	def setup_formats(self, lang="Text"):
		if self.style is None:
			with open(f"./themes/monokai.json", "r") as f:
				self.style = json.load(f)
		for token_name, token in (list(self.style["Text"].items()) + list(self.style[lang].items()) if lang in self.style else []):
			token_format = QTextCharFormat()
			if "Foreground" in token:
				token_format.setForeground(QColor(token["Foreground"]))
			if "FontStyle" in token:
				if "bold" in token["FontStyle"]:
					token_format.setFontWeight(QFont.Weight.Bold)
				if "italic" in token["FontStyle"]:
					token_format.setFontItalic(True)
			token = Token
			for part in token_name.split('.'):
				token = getattr(token, part)
			self.formats[token] = token_format
	
	def tokenize(self):
		text = self.document().toPlainText()
		tokens = list(self.lexer.get_tokens(text))
		num = 0
		offset = 0
		cache = []
		self.token_cache.clear()
		
		for token, value in tokens:
			if value == "\n":
				self.token_cache[num] = cache
				num += 1
				cache = []
				offset = 0
			else:
				cache.append((token, value, offset))
				offset += len(value)
		
		if cache:
			self.token_cache[num] = cache
		
		self.rehighlight()
	def highlightBlock(self, text):
		block_number = self.currentBlock().blockNumber()
		tokens = self.token_cache.get(block_number, [])
		
		for token, value, offset in tokens:
			format = self.get_format_for_token(token)
			if format:
				self.setFormat(offset, len(value), format)

	def get_format_for_token(self, token):
		if token in self.formats:
			return self.formats[token]
		while token.parent is not None:
			token = token.parent
			if token in self.formats:
				return self.formats[token]
		return None