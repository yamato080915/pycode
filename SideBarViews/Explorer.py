from PySide6.QtWidgets import *
from PySide6.QtCore import QDir, QFileInfo
from PySide6.QtGui import QIcon

class CustomIconProvider(QFileIconProvider):
	def __init__(self, dir):
		super().__init__()
		# カスタムアイコンの辞書（拡張子: アイコンパス）
		icon_base = f'{dir}/assets/explorer_icons/'
		self.custom_icons = {
			# Python
			'.py': icon_base + 'python.svg',
			'.pyw': icon_base + 'python.svg',
			'.pyi': icon_base + 'python.svg',
			# JavaScript/TypeScript
			'.js': icon_base + 'javascript.svg',
			'.jsx': icon_base + 'react.svg',
			'.mjs': icon_base + 'javascript.svg',
			'.cjs': icon_base + 'javascript.svg',
			'.ts': icon_base + 'typescript.svg',
			'.tsx': icon_base + 'react_ts.svg',
			'.d.ts': icon_base + 'typescript-def.svg',
			# Web
			'.html': icon_base + 'html.svg',
			'.htm': icon_base + 'html.svg',
			'.css': icon_base + 'css.svg',
			'.scss': icon_base + 'sass.svg',
			'.sass': icon_base + 'sass.svg',
			'.less': icon_base + 'less.svg',
			'.svg': icon_base + 'svg.svg',
			# Data/Config
			'.json': icon_base + 'json.svg',
			'.jsonc': icon_base + 'json.svg',
			'.xml': icon_base + 'xml.svg',
			'.yaml': icon_base + 'yaml.svg',
			'.yml': icon_base + 'yaml.svg',
			'.toml': icon_base + 'toml.svg',
			# C/C++
			'.c': icon_base + 'c.svg',
			'.h': icon_base + 'h.svg',
			'.cpp': icon_base + 'cpp.svg',
			'.cxx': icon_base + 'cpp.svg',
			'.cc': icon_base + 'cpp.svg',
			'.hpp': icon_base + 'hpp.svg',
			'.hxx': icon_base + 'hpp.svg',
			# C#
			'.cs': icon_base + 'csharp.svg',
			'.csx': icon_base + 'csharp.svg',
			# Java
			'.java': icon_base + 'java.svg',
			'.class': icon_base + 'javaclass.svg',
			'.jar': icon_base + 'jar.svg',
			# Rust
			'.rs': icon_base + 'rust.svg',
			# Go
			'.go': icon_base + 'go.svg',
			# Ruby
			'.rb': icon_base + 'ruby.svg',
			'.erb': icon_base + 'ruby.svg',
			# PHP
			'.php': icon_base + 'php.svg',
			'.phtml': icon_base + 'php.svg',
			# Swift
			'.swift': icon_base + 'swift.svg',
			# Kotlin
			'.kt': icon_base + 'kotlin.svg',
			'.kts': icon_base + 'kotlin.svg',
			# Shell
			'.sh': icon_base + 'console.svg',
			'.bash': icon_base + 'console.svg',
			'.zsh': icon_base + 'console.svg',
			'.fish': icon_base + 'console.svg',
			'.ps1': icon_base + 'powershell.svg',
			'.psm1': icon_base + 'powershell.svg',
			'.bat': icon_base + 'console.svg',
			'.cmd': icon_base + 'console.svg',
			# Documents
			'.md': icon_base + 'markdown.svg',
			'.markdown': icon_base + 'markdown.svg',
			'.txt': icon_base + 'document.svg',
			'.pdf': icon_base + 'pdf.svg',
			'.doc': icon_base + 'word.svg',
			'.docx': icon_base + 'word.svg',
			# Media
			'.png': icon_base + 'image.svg',
			'.jpg': icon_base + 'image.svg',
			'.jpeg': icon_base + 'image.svg',
			'.gif': icon_base + 'image.svg',
			'.webp': icon_base + 'image.svg',
			'.mp3': icon_base + 'audio.svg',
			'.wav': icon_base + 'audio.svg',
			'.mp4': icon_base + 'video.svg',
			'.avi': icon_base + 'video.svg',
			'.mov': icon_base + 'video.svg',
			# Archives
			'.zip': icon_base + 'zip.svg',
			'.rar': icon_base + 'zip.svg',
			'.7z': icon_base + 'zip.svg',
			'.tar': icon_base + 'zip.svg',
			'.gz': icon_base + 'zip.svg',
			# Other languages
			'.lua': icon_base + 'lua.svg',
			'.r': icon_base + 'r.svg',
			'.dart': icon_base + 'dart.svg',
			'.scala': icon_base + 'scala.svg',
			'.zig': icon_base + 'zig.svg',
			'.ex': icon_base + 'elixir.svg',
			'.exs': icon_base + 'elixir.svg',
			'.clj': icon_base + 'clojure.svg',
			'.elm': icon_base + 'elm.svg',
			'.vim': icon_base + 'vim.svg',
			# Config files
			'.gitignore': icon_base + 'git.svg',
			'.gitattributes': icon_base + 'git.svg',
			'.env': icon_base + 'settings.svg',
			'.editorconfig': icon_base + 'editorconfig.svg',
			'Dockerfile': icon_base + 'docker.svg',
			'.dockerignore': icon_base + 'docker.svg',
		}
		# ファイル名完全一致
		self.filename_icons = {
			'Dockerfile': icon_base + 'docker.svg',
			'Makefile': icon_base + 'makefile.svg',
			'CMakeLists.txt': icon_base + 'cmake.svg',
			'package.json': icon_base + 'nodejs.svg',
			'tsconfig.json': icon_base + 'tsconfig.svg',
			'jsconfig.json': icon_base + 'jsconfig.svg',
			'.gitignore': icon_base + 'git.svg',
			'.eslintrc': icon_base + 'eslint.svg',
			'.prettierrc': icon_base + 'prettier.svg',
			'README.md': icon_base + 'readme.svg',
			'LICENSE': icon_base + 'license.svg',
			'.env': icon_base + 'settings.svg',
		}
	
	def icon(self, type_or_info):
		if isinstance(type_or_info, QFileInfo):
			file_info = type_or_info
			if file_info.isFile():
				# ファイル名完全一致をチェック
				filename = file_info.fileName()
				if filename in self.filename_icons:
					icon = QIcon(self.filename_icons[filename])
					if not icon.isNull():
						return icon
				
				# 拡張子でチェック
				suffix = '.' + file_info.suffix().lower()
				if suffix in self.custom_icons:
					icon = QIcon(self.custom_icons[suffix])
					if not icon.isNull():
						return icon
		return super().icon(type_or_info)

class Explorer(QTreeView):
	def __init__(self, window=None):
		super().__init__()
		self.setObjectName("explorer")
		self.file_model = QFileSystemModel()
		
		# カスタムアイコンプロバイダーを設定
		icon_provider = CustomIconProvider(dir = window.DIR)
		self.file_model.setIconProvider(icon_provider)
		
		self.file_model.setRootPath(QDir.currentPath())
		self.setModel(self.file_model)
		self.setRootIndex(self.file_model.index(QDir.currentPath()))
		for column in range(1, self.file_model.columnCount()):
			self.hideColumn(column)
		self.setColumnWidth(0, 250)
		self.setHeaderHidden(True)
		self.clicked.connect(window.open_file_from_tree)