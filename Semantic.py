from enum import Enum, auto
import ast
import importlib.util
import inspect

class SymbolKind(Enum):
	Class = auto()
	Function = auto()
	Variable = auto()

class SymbolInfo:
	"""シンボルの詳細情報を保持するクラス"""
	def __init__(self, name, kind, lineno=0, signature=None, docstring=None, type_hint=None):
		self.name = name
		self.kind = kind
		self.lineno = lineno
		self.signature = signature
		self.docstring = docstring
		self.type_hint = type_hint
	
	def to_tooltip(self):
		"""ツールチップ用のテキストを生成"""
		lines = []
		
		if self.kind == SymbolKind.Class:
			lines.append(f"(class) {self.name}")
		elif self.kind == SymbolKind.Function:
			if self.signature:
				lines.append(f"(function) {self.name}{self.signature}")
			else:
				lines.append(f"(function) {self.name}(...)")
		elif self.kind == SymbolKind.Variable:
			if self.type_hint:
				lines.append(f"(variable) {self.name}: {self.type_hint}")
			else:
				lines.append(f"(variable) {self.name}")
		
		if self.docstring:
			# ドキュメント文字列の最初の段落のみ表示
			doc_lines = self.docstring.strip().split('\n\n')[0].split('\n')
			doc_preview = '\n'.join(doc_lines[:5])  # 最大5行
			if len(doc_lines) > 5:
				doc_preview += '\n...'
			lines.append('')
			lines.append(doc_preview)
		
		return '\n'.join(lines)

class Scope:
	def __init__(self, parent=None, start=0, end=10**9):
		self.parent = parent
		self.start = start
		self.end = end
		self.symbols = {}

	def contains(self, lineno):
		return self.start <= lineno <= self.end

class ScopeCollector(ast.NodeVisitor):
	def __init__(self):
		self.root = Scope()
		self.current = self.root
		self.modules = {}
		self.imported = set()

	# ---------- scope helpers ----------
	def push_scope(self, node):
		scope = Scope(
			parent=self.current,
			start=node.lineno,
			end=getattr(node, "end_lineno", 10**9)
		)
		self.current = scope

	def pop_scope(self):
		self.current = self.current.parent

	# ---------- definitions ----------
	def visit_ClassDef(self, node):
		self.current.symbols[node.name] = SymbolKind.Class
		self.push_scope(node)
		self.generic_visit(node)
		self.pop_scope()

	def visit_FunctionDef(self, node):
		self.current.symbols[node.name] = SymbolKind.Function
		self.push_scope(node)
		self.generic_visit(node)
		self.pop_scope()

	def visit_AsyncFunctionDef(self, node):
		self.current.symbols[node.name] = SymbolKind.Function
		self.push_scope(node)
		self.generic_visit(node)
		self.pop_scope()

	def visit_Assign(self, node):
		for target in node.targets:
			if isinstance(target, ast.Name):
				self.current.symbols[target.id] = SymbolKind.Variable
		self.generic_visit(node)

	def visit_AnnAssign(self, node):
		if isinstance(node.target, ast.Name):
			self.current.symbols[node.target.id] = SymbolKind.Variable
		self.generic_visit(node)

	# ---------- imports ----------
	def visit_Import(self, node):
		for alias in node.names:
			self.modules[alias.name] = {}
			self.imported.add(alias.asname or alias.name)

	def visit_ImportFrom(self, node):
		if node.module:
			self.modules.setdefault(node.module, {})
			for alias in node.names:
				self.imported.add(alias.asname or alias.name)

class Semantic:
	def __init__(self, text):
		self.root = Scope()
		self.modules = {}
		self.imported = set()
		self.analyze(text)

	def analyze(self, text):
		try:
			tree = ast.parse(text)
		except SyntaxError:
			return
		collector = ScopeCollector()
		collector.visit(tree)
		self.root = collector.root
		self.modules = collector.modules
		self.imported = collector.imported

	def lookup(self, name, lineno):
		scope = self.find_scope(self.root, lineno)
		while scope:
			if name in scope.symbols:
				return scope.symbols[name]
			scope = scope.parent
		return None

	def find_scope(self, scope, lineno):
		for child in getattr(scope, "children", []):
			if child.contains(lineno):
				return self.find_scope(child, lineno)
		return scope if scope.contains(lineno) else None

def get_module_file(module):
	try:
		spec = importlib.util.find_spec(module)
		if spec and spec.origin:
			if spec.origin.endswith('.pyd'):
				return spec.origin.rstrip('.pyd') + '.pyi'
			elif spec.origin == 'built-in' or spec.origin == 'frozen':
				return None
			return spec.origin
		return None
	except:
		return None


def get_symbol_info(text, symbol_name, lineno=1):
	"""テキスト内のシンボルの詳細情報を取得"""
	try:
		tree = ast.parse(text)
	except SyntaxError:
		return None
	
	for node in ast.walk(tree):
		# クラス定義
		if isinstance(node, ast.ClassDef) and node.name == symbol_name:
			docstring = ast.get_docstring(node)
			bases = [ast.unparse(base) for base in node.bases] if node.bases else []
			signature = f"({', '.join(bases)})" if bases else ""
			return SymbolInfo(
				name=symbol_name,
				kind=SymbolKind.Class,
				lineno=node.lineno,
				signature=signature,
				docstring=docstring
			)
		
		# 関数定義
		if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == symbol_name:
			docstring = ast.get_docstring(node)
			# シグネチャを構築
			args = []
			defaults_offset = len(node.args.args) - len(node.args.defaults)
			
			for i, arg in enumerate(node.args.args):
				arg_str = arg.arg
				if arg.annotation:
					arg_str += f": {ast.unparse(arg.annotation)}"
				default_idx = i - defaults_offset
				if default_idx >= 0 and default_idx < len(node.args.defaults):
					arg_str += f" = {ast.unparse(node.args.defaults[default_idx])}"
				args.append(arg_str)
			
			if node.args.vararg:
				vararg_str = f"*{node.args.vararg.arg}"
				if node.args.vararg.annotation:
					vararg_str += f": {ast.unparse(node.args.vararg.annotation)}"
				args.append(vararg_str)
			
			if node.args.kwarg:
				kwarg_str = f"**{node.args.kwarg.arg}"
				if node.args.kwarg.annotation:
					kwarg_str += f": {ast.unparse(node.args.kwarg.annotation)}"
				args.append(kwarg_str)
			
			signature = f"({', '.join(args)})"
			if node.returns:
				signature += f" -> {ast.unparse(node.returns)}"
			
			return SymbolInfo(
				name=symbol_name,
				kind=SymbolKind.Function,
				lineno=node.lineno,
				signature=signature,
				docstring=docstring
			)
		
		# 変数代入（型注釈付き）
		if isinstance(node, ast.AnnAssign):
			if isinstance(node.target, ast.Name) and node.target.id == symbol_name:
				type_hint = ast.unparse(node.annotation) if node.annotation else None
				return SymbolInfo(
					name=symbol_name,
					kind=SymbolKind.Variable,
					lineno=node.lineno,
					type_hint=type_hint
				)
		
		# 通常の変数代入
		if isinstance(node, ast.Assign):
			for target in node.targets:
				if isinstance(target, ast.Name) and target.id == symbol_name:
					# 値から型を推測
					type_hint = None
					if isinstance(node.value, ast.Constant):
						type_hint = type(node.value.value).__name__
					elif isinstance(node.value, ast.List):
						type_hint = "list"
					elif isinstance(node.value, ast.Dict):
						type_hint = "dict"
					elif isinstance(node.value, ast.Set):
						type_hint = "set"
					elif isinstance(node.value, ast.Tuple):
						type_hint = "tuple"
					elif isinstance(node.value, ast.Call):
						if isinstance(node.value.func, ast.Name):
							type_hint = node.value.func.id
						elif isinstance(node.value.func, ast.Attribute):
							type_hint = node.value.func.attr
					
					return SymbolInfo(
						name=symbol_name,
						kind=SymbolKind.Variable,
						lineno=node.lineno,
						type_hint=type_hint
					)
	
	return None


def get_import_info(text, symbol_name):
	"""インポートされたシンボルの情報を取得"""
	try:
		tree = ast.parse(text)
	except SyntaxError:
		return None
	
	for node in ast.walk(tree):
		# import module
		if isinstance(node, ast.Import):
			for alias in node.names:
				actual_name = alias.asname or alias.name
				if actual_name == symbol_name:
					return SymbolInfo(
						name=symbol_name,
						kind=SymbolKind.Variable,
						lineno=node.lineno,
						type_hint=f"module '{alias.name}'"
					)
		
		# from module import name
		if isinstance(node, ast.ImportFrom):
			for alias in node.names:
				actual_name = alias.asname or alias.name
				if actual_name == symbol_name:
					module_name = node.module or ""
					# インポート先のモジュールから情報を取得
					module_file = get_module_file(module_name)
					if module_file:
						try:
							with open(module_file, 'r', encoding='utf-8') as f:
								module_text = f.read()
							info = get_symbol_info(module_text, alias.name)
							if info:
								return info
						except:
							pass
					
					return SymbolInfo(
						name=symbol_name,
						kind=SymbolKind.Variable,
						lineno=node.lineno,
						type_hint=f"from {module_name}"
					)
	
	return None
