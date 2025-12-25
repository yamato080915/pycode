import sys, time, re, platform, os
from threading import Thread
from PySide6.QtWidgets import QApplication, QMainWindow, QPlainTextEdit
from PySide6.QtGui import QFont
from PySide6.QtCore import QDir, Qt, Signal

OS = platform.system()

if OS == "Windows":
	from winpty import PtyProcess
else:
	import pty, subprocess

class Terminal(QPlainTextEdit):
	output_received = Signal(tuple)
	def __init__(self):
		super().__init__()
		self.setObjectName("Terminal")
		if OS == "Windows":
			self.setFont(QFont("Cascadia Mono", 11))
		else:
			self.setFont(QFont("Monospace", 11))
		
		self.output_received.connect(self.append_output)
		self.prompt_position = 0
		self.left_clicking = False
		self.command = "-------"
		self.count = 0
		self.cursorPositionChanged.connect(self.cursor_moved)
		self.start_terminal()
		
		self.ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
		self.osc_escape = re.compile(r'\]0;[^\x07]*\x07')
		self.control_chars = re.compile(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]')
		self.cmd_pattern = re.compile(r'\d+;C:\\WINDOWS\\system32\\cmd\.exe[^\n]*')

	def start_terminal(self):
		self.cwd = QDir.currentPath()
		if OS == "Windows":
			if hasattr(self, 'pty') and self.pty.isalive():
				self.end_terminal()
			self.pty = PtyProcess.spawn("cmd.exe", cwd=self.cwd, env=None)
		else:
			self.master, self.slave = pty.openpty()
			self.pty = subprocess.Popen(
				["/bin/bash"], 
				stdin=self.slave, 
				stdout=self.slave, 
				stderr=self.slave, 
				cwd=self.cwd, 
				preexec_fn=os.setsid, 
				text=True
			)
		Thread(target=self.output_thread, daemon=True, name="output").start()

	def end_terminal(self):
		if OS == "Windows":
			if self.pty.isalive():
				self.pty.terminate()
				self.clear()
		else:
			if self.pty.poll() is None:
				self.pty.terminate()
				self.clear()
	
	def output_thread(self):
		if OS == "Windows":
			while self.pty.isalive():
				try:
					output = self.pty.read()
					clean_output = self.strip_ansi_escape_sequences(output)
					if clean_output == "" or (clean_output == "\n" and self.count > 0):
						continue
					self.output_received.emit(clean_output)
					self.count += 1
				except Exception as e:
					print(e, e.__class__)
				time.sleep(0.001)
		else:
			while self.pty.poll() is None:
				try:
					output = os.read(self.master, 1024).decode(errors='ignore')
					clean_output = self.strip_ansi_escape_sequences(output)
					if clean_output == "" or (clean_output == "\n" and self.count > 0):
						continue
					self.output_received.emit(clean_output)
					self.count += 1
				except Exception as e:
					print(e, e.__class__)

	def strip_ansi_escape_sequences(self, text):
		text = self.ansi_escape.sub('', text)
		text = self.osc_escape.sub('', text)
		text = self.control_chars.sub('', text)
		text = text.replace("\r\n", "\n")
		if "C:\\WINDOWS\\system32\\cmd.exe" in text:
			text = self.cmd_pattern.sub('', text)
		if self.command.replace("\n", "") == text:
			text = ""
		return text

	def append_output(self, text):
		self.appendPlainText(text.strip("\r\n"))
		self.prompt_position = self.textCursor().position()

	def run_command(self):
		self.command = self.toPlainText()[self.prompt_position:]
		if len(self.command.split("\n")) >= 2:
			cursor = self.textCursor()
			cursor.setPosition(self.prompt_position)
			cursor.movePosition(cursor.MoveOperation.End, cursor.MoveMode.KeepAnchor)
			cursor.removeSelectedText()
		self.count = 0
		if OS == "Windows":
			self.pty.write(self.command.replace("\n", "\r\n").rstrip("\r\n") + "\r\n")
		else:
			os.write(self.master, (self.command.replace("\n", "\r\n").rstrip("\r\n") + "\r\n").encode())

	def keyPressEvent(self, event):
		cursor = self.textCursor()
		current_pos = cursor.position()
		selection_start = cursor.selectionStart()
		has_selection = cursor.hasSelection()
		
		if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
			self.run_command()
			return
		
		if has_selection and selection_start < self.prompt_position:
			if event.key() in (Qt.Key_Backspace, Qt.Key_Delete) or event.text():
				return
		
		if event.key() == Qt.Key_Backspace:
			if current_pos <= self.prompt_position:
				return
		elif event.key() == Qt.Key_Delete:
			if current_pos < self.prompt_position:
				return
		elif event.key() == Qt.Key_Left:
			if current_pos <= self.prompt_position:
				return
		
		super().keyPressEvent(event)

	def cursor_moved(self):
		if self.left_clicking:
			return
		cursor = self.textCursor()
		if cursor.position() < self.prompt_position and not cursor.hasSelection():
			cursor.setPosition(self.prompt_position)
			self.setTextCursor(cursor)

	def insertFromMimeData(self, source):
		text = source.text()
		if text and '\n' in text:
			super().insertFromMimeData(source)
			self.run_command()
		else:
			super().insertFromMimeData(source)

	def mousePressEvent(self, event):
		if event.button() == Qt.LeftButton:
			self.left_clicking = True
		super().mousePressEvent(event)

	def mouseReleaseEvent(self, event):
		if event.button() == Qt.LeftButton:
			self.left_clicking = False
			self.cursor_moved()
		super().mouseReleaseEvent(event)

	def contextMenuEvent(self, event):
		cursor = self.textCursor()
		if cursor.hasSelection():
			self.copy()
			cursor.clearSelection()
			cursor.movePosition(cursor.MoveOperation.End)
			self.setTextCursor(cursor)

class Window(QMainWindow):
	def __init__(self):
		super().__init__()
		self.setWindowTitle("Terminal")
		self.terminal = Terminal()
		self.setCentralWidget(self.terminal)

if __name__ == "__main__":
	app = QApplication(sys.argv)
	window = Window()
	window.showMaximized()
	sys.exit(app.exec())