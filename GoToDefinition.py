"""定義へ移動機能モジュール"""
import ast
import os
import re
from Semantic import Semantic, SymbolKind, get_module_file


class DefinitionFinder:
    """シンボルの定義位置を検索するクラス"""
    
    def __init__(self, window):
        self.window = window
    
    def get_word_at_position(self, editor, line, col):
        """カーソル位置の単語を取得"""
        block = editor.document().findBlockByNumber(line)
        if not block.isValid():
            return None
        
        text = block.text()
        if not text or col > len(text):
            return None
        
        # 識別子の範囲を特定
        start = col
        end = col
        
        # 左方向に拡張
        while start > 0 and (text[start - 1].isalnum() or text[start - 1] == '_'):
            start -= 1
        
        # 右方向に拡張
        while end < len(text) and (text[end].isalnum() or text[end] == '_'):
            end += 1
        
        if start == end:
            return None
        
        return text[start:end]
    
    def find_definition_in_text(self, text, symbol_name):
        """テキスト内でシンボルの定義位置を検索"""
        try:
            tree = ast.parse(text)
        except SyntaxError:
            return None
        
        for node in ast.walk(tree):
            # クラス定義
            if isinstance(node, ast.ClassDef) and node.name == symbol_name:
                return node.lineno, self._get_name_col(text, node.lineno, node.name)
            
            # 関数定義
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == symbol_name:
                return node.lineno, self._get_name_col(text, node.lineno, node.name)
            
            # 変数代入
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == symbol_name:
                        return node.lineno, self._get_name_col(text, node.lineno, target.id)
            
            # 型注釈付き変数
            if isinstance(node, ast.AnnAssign):
                if isinstance(node.target, ast.Name) and node.target.id == symbol_name:
                    return node.lineno, self._get_name_col(text, node.lineno, node.target.id)
        
        return None
    
    def _get_name_col(self, text, lineno, name):
        """指定行でシンボル名の列位置を取得"""
        lines = text.splitlines()
        if lineno <= len(lines):
            line = lines[lineno - 1]
            match = re.search(rf'\b{re.escape(name)}\b', line)
            if match:
                return match.start()
        return 0
    
    def find_import_target(self, text, symbol_name):
        """インポート文からシンボルのモジュールを検索"""
        try:
            tree = ast.parse(text)
        except SyntaxError:
            return None, None
        
        for node in ast.walk(tree):
            # import module
            if isinstance(node, ast.Import):
                for alias in node.names:
                    actual_name = alias.asname or alias.name
                    if actual_name == symbol_name:
                        module_file = get_module_file(alias.name)
                        if module_file:
                            return module_file, 1
            
            # from module import name
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    actual_name = alias.asname or alias.name
                    if actual_name == symbol_name:
                        module_file = get_module_file(node.module)
                        if module_file:
                            # モジュールファイル内でシンボルを検索
                            try:
                                with open(module_file, 'r', encoding='utf-8') as f:
                                    module_text = f.read()
                                result = self.find_definition_in_text(module_text, alias.name)
                                if result:
                                    return module_file, result[0]
                            except:
                                pass
                            return module_file, 1
        
        return None, None
    
    def find_definition(self, editor):
        """カーソル位置のシンボルの定義を検索"""
        cursor = editor.textCursor()
        line = cursor.blockNumber()
        col = cursor.columnNumber()
        
        # カーソル位置の単語を取得
        word = self.get_word_at_position(editor, line, col)
        if not word:
            return None
        
        text = editor.document().toPlainText()
        file_path = getattr(editor, 'file_path', None)
        
        # 同じファイル内で定義を検索
        result = self.find_definition_in_text(text, word)
        if result:
            def_line, def_col = result
            return {
                'file_path': file_path,
                'line': def_line,
                'col': def_col,
                'symbol': word,
                'same_file': True
            }
        
        # インポートされたモジュールを検索
        module_file, module_line = self.find_import_target(text, word)
        if module_file:
            return {
                'file_path': module_file,
                'line': module_line,
                'col': 0,
                'symbol': word,
                'same_file': False
            }
        
        return None
    
    def navigate_to_definition(self, definition):
        """定義位置へ移動"""
        if not definition:
            return False
        
        file_path = definition['file_path']
        line = definition['line']
        col = definition['col']
        
        # 同じファイル内の場合
        if definition['same_file']:
            current_index = self.window.tabs.currentIndex()
            editor = self.window.tablist[current_index]
            self._move_cursor(editor, line, col)
            return True
        
        # 別ファイルの場合
        if file_path and os.path.exists(file_path):
            # 既に開いているタブを確認
            if file_path in self.window.tabfilelist:
                tab_index = self.window.tabfilelist.index(file_path)
                self.window.tabs.setCurrentIndex(tab_index)
                editor = self.window.tablist[tab_index]
                self._move_cursor(editor, line, col)
                return True
            
            # 新しいタブで開く
            self.window.open_(file_path)
            current_index = self.window.tabs.currentIndex()
            editor = self.window.tablist[current_index]
            self._move_cursor(editor, line, col)
            return True
        
        return False
    
    def _move_cursor(self, editor, line, col):
        """エディタのカーソルを指定位置に移動"""
        cursor = editor.textCursor()
        cursor.movePosition(cursor.MoveOperation.Start)
        cursor.movePosition(cursor.MoveOperation.Down, cursor.MoveMode.MoveAnchor, line - 1)
        cursor.movePosition(cursor.MoveOperation.Right, cursor.MoveMode.MoveAnchor, col)
        editor.setTextCursor(cursor)
        editor.centerCursor()
        editor.setFocus()


def go_to_definition(window):
    """定義へ移動を実行"""
    current_index = window.tabs.currentIndex()
    if current_index < 0 or current_index >= len(window.tablist):
        return
    
    editor = window.tablist[current_index]
    if not hasattr(editor, 'textCursor'):
        return
    
    finder = DefinitionFinder(window)
    definition = finder.find_definition(editor)
    
    if definition:
        finder.navigate_to_definition(definition)
    else:
        window.statusBar().showMessage("定義が見つかりませんでした", 3000)
