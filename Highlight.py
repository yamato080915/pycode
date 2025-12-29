from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PySide6.QtCore import QTimer
from pygments.lexers import get_lexer_for_filename, get_lexer_by_name
from pygments.token import Token, Punctuation, Name
import json
from semantic import *

Punctuation.Bracket
Punctuation.Bracket.Depth0
Punctuation.Bracket.Depth1
Punctuation.Bracket.Depth2

class Highlighter(QSyntaxHighlighter):
	def __init__(self, window=None, parent=None, filename = "*.txt", style=None):
		super().__init__(parent)
		self.win = window
		self.style = style
		self.set_filetype(filename)
		self.token_cache = {}
		self.use_cache = False
		
		self.tokenize_timer = QTimer()
		self.tokenize_timer.setSingleShot(True)
		self.tokenize_timer.setInterval(1000)
		self.tokenize_timer.timeout.connect(self.tokenize)

		self.document().contentsChange.connect(self.changed)
	
	def changed(self, position, chars_removed, chars_added):
		if self.tokenize_timer.isActive():
			self.use_cache = False
			
			doc = self.document()
			start_block = doc.findBlock(position)
			end_block = doc.findBlock(position + chars_added)
			
			block = start_block
			while block.isValid() and block.blockNumber() <= end_block.blockNumber():
				self.rehighlightBlock(block)
				block = block.next()
		
		self.schedule_tokenize()
	
	def schedule_tokenize(self):
		self.tokenize_timer.stop()
		self.tokenize_timer.start()
	
	def set_filetype(self, filename):
		try:
			self.lexer = get_lexer_for_filename(filename)
		except Exception as e:
			print(f"Error getting lexer for {filename}: {e}")
			self.lexer = get_lexer_by_name("text")
		lang = str(self.lexer).lstrip("<pygments.lexers.").rstrip("Lexer>")
		self.formats = {}
		self.replace = {}
		self.setup_formats(lang)

	def setup_formats(self, lang="Text"):
		if self.style is None:
			with open(f"{self.win.DIR}/themes/monokai.json", "r") as f:
				self.style = json.load(f)
		for token_name, token in (list(self.style["Text"].items()) + (list(self.style[lang].items()) if lang in self.style else [])):
			token_format = QTextCharFormat()
			if "Foreground" in token:
				token_format.setForeground(QColor(token["Foreground"]))
			if "FontStyle" in token:
				if "bold" in token["FontStyle"]:
					token_format.setFontWeight(QFont.Weight.Bold)
				if "italic" in token["FontStyle"]:
					token_format.setFontItalic(True)
			if "Replace" in token:
				self.replace[token_name] = []
				for i, j in token["Replace"]:
					t = Token
					for x in j.split('.'):
						t = getattr(t, x)
					self.replace[token_name].append((tuple(i), t))
				self.replace[token_name] = tuple(self.replace[token_name])
						
			token = Token
			for part in token_name.split('.'):
				token = getattr(token, part)
			self.formats[token] = token_format
	
	def tokenize(self):
		self.document().contentsChange.disconnect(self.changed)
		
		text = self.document().toPlainText()
		tokens = list(self.lexer.get_tokens(text))
		num = 0
		offset = 0
		cache = []
		self.token_cache.clear()
		brackets = 0
		semantic_analyzer = Semantic(text)
		modules = semantic_analyzer.modules
		imported = semantic_analyzer.imported
		modulefiles = {}
		for key in modules.keys():
			file = get_module_file(key)
			if file:
				with open(file, 'r', encoding='utf-8') as f:
					modulefiles[key] = Semantic(f.read())
			for value in modules[key].keys():
				file = get_module_file(f"{value}")
				if file:
					with open(file, 'r', encoding='utf-8') as f:
						modulefiles[value] = Semantic(f.read())
		for token, value in tokens:
			if value in (')', '}', ']') and token == Punctuation:
				brackets = (brackets - 1)%3
			if '\n' in value:
				lines = value.split('\n')
				for i, line in enumerate(lines):
					if line:
						cache.append((token, line, offset))
						offset += len(line)
					
					if i < len(lines) - 1:
						self.token_cache[num] = cache
						num += 1
						cache = []
						offset = 0
			else:
				if value in ('(', ')', '{', '}', '[', ']') and token == Punctuation:
					if brackets == 0:
						bracket_token = Punctuation.Bracket.Depth0
					elif brackets == 1:
						bracket_token = Punctuation.Bracket.Depth1
					elif brackets == 2:
						bracket_token = Punctuation.Bracket.Depth2
					
					cache.append((bracket_token, value, offset))
				elif str(token).replace("Token.", "") in self.replace:
					flag = False
					for x, y in self.replace[str(token).replace("Token.", "")]:
						if value in x:
							cache.append((y, value, offset))
							flag = True
							break
					if not flag:
						cache.append((token, value, offset))
				elif token == Name:
					kind = set([module.lookup(value) for module in modulefiles.values()])
					kind.discard(None)
					if len(kind) == 1:
						kind = kind.pop()
					else:
						kind = semantic_analyzer.lookup(value)
					if kind == SymbolKind.Class:
						token_ = Name.Class
					elif kind == SymbolKind.Function:
						token_ = Name.Function
					elif kind == SymbolKind.Variable:
						token_ = Name.Variable
					elif value in imported:
						token_ = Name.Namespace
					else:
						token_ = token
					
					cache.append((token_, value, offset))
				else:
					cache.append((token, value, offset))
				offset += len(value)
			if value in ('(', '{', '[') and token == Punctuation:
				brackets = (brackets + 1)%3
		
		if cache:
			self.token_cache[num] = cache
		
		self.use_cache = True
		self.rehighlight()
		self.document().contentsChange.connect(self.changed)
	
	def highlightBlock(self, text):
		block_number = self.currentBlock().blockNumber()
		
		if self.use_cache:
			tokens = self.token_cache.get(block_number, [])
			for token, value, offset in tokens:
				format = self.get_format_for_token(token)
				if format:
					self.setFormat(offset, len(value), format)
		else:
			try:
				tokens = list(self.lexer.get_tokens(text))
				offset = 0
				for token, value in tokens:
					length = len(value)
					if value in ('(', ')', '{', '}', '[', ']'):
						token = Punctuation.Bracket
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