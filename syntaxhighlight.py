from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from pygments.lexers import get_lexer_for_filename, get_lexer_by_name
from pygments.token import Token
import json

class PygmentsSyntaxHighlight(QSyntaxHighlighter):
	def __init__(self, parent=None, filename = "*.txt", style=None):
		super().__init__(parent)
		self.style = style
		self.set_filetype(filename)
	
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
	
	def highlightBlock(self, text):#1行ごとにハイライト処理
		try:
			tokens = list(self.lexer.get_tokens(text))
			
			offset = 0
			for token, value in tokens:
				length = len(value)
				format = self.get_format_for_token(token)
				if format:
					self.setFormat(offset, length, format)
				offset += length
		except Exception as e:
			print(f"Error in highlightBlock: {e}")
	
	def get_format_for_token(self, token):
		if token in self.formats:
			return self.formats[token]
		while token.parent is not None:
			token = token.parent
			if token in self.formats:
				return self.formats[token]
		return None