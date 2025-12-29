from enum import Enum, auto
import ast
import importlib.util

class SymbolKind(Enum):
	Class = auto()
	Function = auto()
	Variable = auto()

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
			elif spec.origin == 'built-in':
				return None
			return spec.origin
		return None
	except:
		return None
