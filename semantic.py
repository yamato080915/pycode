from enum import Enum, auto
import ast
import importlib.util

class SymbolKind(Enum):
	Class = auto()
	Function = auto()
	Variable = auto()

class SymbolTable:
	def __init__(self):
		self.symbols = {}

class SymbolCollector(ast.NodeVisitor):
	def __init__(self):
		self.table = SymbolTable()
	
	def visit_ClassDef(self, node):
		self.table.symbols[node.name] = SymbolKind.Class
		self.generic_visit(node)
	
	def visit_FunctionDef(self, node):
		self.table.symbols[node.name] = SymbolKind.Function
		self.generic_visit(node)
	
	def visit_AsyncFunctionDef(self, node):
		self.table.symbols[node.name] = SymbolKind.Function
		self.generic_visit(node)
	
	def visit_Assign(self, node):
		for target in node.targets:
			if isinstance(target, ast.Name):
				self.table.symbols[target.id] = SymbolKind.Variable
		self.generic_visit(node)
	
	def visit_AnnAssign(self, node):
		if isinstance(node.target, ast.Name):
			self.table.symbols[node.target.id] = SymbolKind.Variable
		self.generic_visit(node)
	
class Semantic:
	def __init__(self, text):
		self.table = SymbolTable()
		self.analyze(text)
	
	def analyze(self, text):
		try:
			tree = ast.parse(text)
		except SyntaxError:
			return
		collector = SymbolCollector()
		collector.visit(tree)
		self.table = collector.table
	
	def lookup(self, name):
		return self.table.symbols.get(name)

class ModuleCollector(ast.NodeVisitor):
	def __init__(self):
		self.symbols = {"modules": {}}
	def visit_Import(self, node):
		for alias in node.names:
			self.symbols["modules"][alias.name] = {}
		self.generic_visit(node)
	def visit_ImportFrom(self, node):
		self.symbols["modules"][node.module] = []
		for alias in node.names:
			self.symbols["modules"][node.module].append(alias.name)
		self.generic_visit(node)
	
def get_module_file(module):
	try:
		spec = importlib.util.find_spec(module)
		if spec and spec.origin:
			if spec.origin.endswith('.pyd'):
				return spec.origin.rstrip('.pyd') + '.pyi'
			return spec.origin
		return None
	except:
		return None