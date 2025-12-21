from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from pygments.lexers import get_lexer_for_filename, get_lexer_by_name
from pygments.token import Token
import json

class PygmentsSyntaxHighlight(QSyntaxHighlighter):
	def __init__(self, parent=None, filename = "*.txt", style=None):
		super().__init__(parent)

		try:
			self.lexer = get_lexer_for_filename(filename)
		except :
			self.lexer = get_lexer_by_name("text")
		self.formats = {}
		lang = str(self.lexer).lstrip("<pygments.lexers.").rstrip("Lexer>")
		self.setup_formats(style, lang)
	
	def setup_formats(self, style=None, lang="Text"):
		style_data = style
		if style is None:
			with open(f"./monokai.json", "r") as f:
				style_data = json.load(f)
		for token_name, token in (list(style_data["Text"].items()) + list(style_data[lang].items()) if lang in style_data else []):
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