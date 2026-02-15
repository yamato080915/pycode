"""Git共通ユーティリティ - ステータス定数、非同期Gitコマンド実行"""
import os
import re
import subprocess
from PySide6.QtCore import QDir, QThread, Signal, QObject

# ─── ステータスアイコン / カラー ───────────────────────────
GIT_STATUS_ICONS = {
	'M': '◆', 'A': '+', 'D': '−', 'R': '→',
	'U': '?', 'C': '©', 'T': '≠', '!': '⊘',
}
GIT_STATUS_COLORS = {
	'M': '#E5C07B', 'A': '#98C379', 'D': '#E06C75',
	'R': '#61AFEF', 'U': '#4EC9B0', 'C': '#C678DD',
	'T': '#56B6C2', '!': '#858585',
}
GIT_STATUS_LABELS = {
	'M': '変更', 'A': '追加', 'D': '削除', 'R': '名前変更',
	'U': '未追跡', 'C': 'コピー', 'T': '型変更', '!': '無視',
}

DEFAULT_ICON = '•'
DEFAULT_COLOR = '#ABB2BF'


def get_status_icon(status):
	"""ステータスに対応するアイコン文字を返す"""
	key = status[0] if status else 'M'
	return GIT_STATUS_ICONS.get(key, DEFAULT_ICON)


def get_status_color(status):
	"""ステータスに対応する色コードを返す"""
	key = status[0] if status else 'M'
	return GIT_STATUS_COLORS.get(key, DEFAULT_COLOR)


def get_status_label(status):
	"""ステータスに対応するラベルを返す"""
	key = status[0] if status else 'M'
	return GIT_STATUS_LABELS.get(key, '不明')


# ─── 同期 Git コマンド実行 ────────────────────────────────
def run_git(args, cwd=None, show_error=False, error_callback=None):
	"""Gitコマンドを実行して結果を返す（同期）

	Returns:
		成功時: stdout 文字列  |  失敗時: None
	"""
	try:
		work_dir = cwd or QDir.currentPath()
		kwargs = dict(
			capture_output=True,
			text=True,
			encoding='utf-8',
			errors='replace',
			cwd=work_dir,
		)
		if os.name == 'nt':
			si = subprocess.STARTUPINFO()
			si.dwFlags = subprocess.STARTF_USESHOWWINDOW
			kwargs['startupinfo'] = si

		result = subprocess.run(['git'] + args, **kwargs)
		if result.returncode != 0:
			if show_error and error_callback:
				error_callback(f"⚠ {result.stderr.strip()[:80]}")
			return None
		return result.stdout.strip()
	except FileNotFoundError:
		if show_error and error_callback:
			error_callback("⚠ Gitが見つかりません")
		return None
	except Exception:
		if show_error and error_callback:
			error_callback("⚠ Gitコマンドエラー")
		return None


# ─── 非同期 Git ワーカー ──────────────────────────────────
class GitWorker(QThread):
	"""バックグラウンドでGitコマンドを実行するワーカースレッド"""
	finished = Signal(str, object)   # (task_name, result_or_None)
	error = Signal(str, str)         # (task_name, error_message)

	def __init__(self, task_name, args, cwd=None, parent=None):
		super().__init__(parent)
		self.task_name = task_name
		self.args = args
		self.cwd = cwd

	def run(self):
		result = run_git(self.args, cwd=self.cwd)
		if result is not None:
			self.finished.emit(self.task_name, result)
		else:
			self.error.emit(self.task_name, f"コマンド失敗: git {' '.join(self.args)}")


class GitRunner(QObject):
	"""複数のGit操作を管理するランナー"""
	taskFinished = Signal(str, object)
	taskError = Signal(str, str)

	def __init__(self, parent=None):
		super().__init__(parent)
		self._workers = []

	def run(self, task_name, args, cwd=None):
		"""非同期でGitコマンドを実行"""
		worker = GitWorker(task_name, args, cwd, self)
		worker.finished.connect(self._on_finished)
		worker.error.connect(self._on_error)
		worker.finished.connect(lambda: self._cleanup(worker))
		worker.error.connect(lambda: self._cleanup(worker))
		self._workers.append(worker)
		worker.start()

	def _on_finished(self, task, result):
		self.taskFinished.emit(task, result)

	def _on_error(self, task, msg):
		self.taskError.emit(task, msg)

	def _cleanup(self, worker):
		if worker in self._workers:
			self._workers.remove(worker)


# ─── ユーティリティ ──────────────────────────────────────
def parse_status_line(line):
	"""git status --porcelain の1行をパースして (file_path, index_status, work_status) を返す"""
	if len(line) < 4:
		return None
	index_status = line[0]
	work_status = line[1]
	file_path = line[3:]
	if ' -> ' in file_path:
		file_path = file_path.split(' -> ')[-1]
	return file_path, index_status, work_status


def parse_ahead_behind(output):
	"""'ahead N, behind M' 形式の文字列から (ahead, behind) を返す"""
	ahead = behind = 0
	if not output:
		return ahead, behind
	m_ahead = re.search(r'ahead (\d+)', output)
	m_behind = re.search(r'behind (\d+)', output)
	if m_ahead:
		ahead = int(m_ahead.group(1))
	if m_behind:
		behind = int(m_behind.group(1))
	return ahead, behind
