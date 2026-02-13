"""Git共通ユーティリティ - ステータスアイコン/カラー定数とGitコマンド実行"""
import os
import subprocess
from PySide6.QtCore import QDir

# Git ステータスアイコン
GIT_STATUS_ICONS = {
	'M': '◆', 'A': '+', 'D': '−', 'R': '→', 'U': '?', 'C': '©', 'T': '≠'
}

# Git ステータスカラー
GIT_STATUS_COLORS = {
	'M': '#E5C07B', 'A': '#98C379', 'D': '#E06C75',
	'R': '#61AFEF', 'U': '#4EC9B0', 'C': '#C678DD', 'T': '#56B6C2'
}

DEFAULT_STATUS_ICON = '•'
DEFAULT_STATUS_COLOR = '#ABB2BF'


def get_status_icon(status):
	"""ステータスに対応するアイコン文字を返す"""
	key = status[0] if status else 'M'
	return GIT_STATUS_ICONS.get(key, DEFAULT_STATUS_ICON)


def get_status_color(status):
	"""ステータスに対応する色コードを返す"""
	key = status[0] if status else 'M'
	return GIT_STATUS_COLORS.get(key, DEFAULT_STATUS_COLOR)


def run_git(args, show_error=False, error_callback=None):
	"""共通のGitコマンド実行

	Args:
		args: gitサブコマンドと引数のリスト
		show_error: エラー時にコールバックを呼ぶかどうか
		error_callback: エラーメッセージを受け取るコールバック関数

	Returns:
		成功時はstdout文字列、失敗時はNone
	"""
	try:
		cwd = QDir.currentPath()
		kwargs = dict(
			capture_output=True,
			text=True,
			encoding='utf-8',
			errors='replace',
			cwd=cwd,
		)
		if os.name == 'nt':
			si = subprocess.STARTUPINFO()
			si.dwFlags = subprocess.STARTF_USESHOWWINDOW
			kwargs['startupinfo'] = si

		result = subprocess.run(['git'] + args, **kwargs)

		if result.returncode != 0:
			if show_error and error_callback:
				error_callback(f"⚠ {result.stderr.strip()[:50]}")
			return None
		return result.stdout.strip()
	except:
		if show_error and error_callback:
			error_callback("⚠ Gitが見つかりません")
		return None
