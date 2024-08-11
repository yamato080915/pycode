version = ["3.0.0-Preview4.8", "3.0.0"]

from time import time
starttime = time()

import tkinter as tk
from tkinter import ttk, font, messagebox as msg, filedialog
import signal as sig, os, sys, json, glob, zlib, base64, webcolors as c, importlib, asyncio, ctypes
import subprocess
from PIL import Image
import threading
from time import sleep

from pygments.lexers import *

import appdata
import setup

OS = appdata.OS

def importer():
	try:
		global pyperclip, webbrowser, urllib, p, re, lex, perf_counter
		import pyperclip, webbrowser, urllib, multiprocessing as p, re
		from pygments import lex
		from time import perf_counter
	except Exception as e:
		msg.showerror(title=str(e.__class__.__name__), message=e)

class txtedit(tk.Frame):
	def __init__(self, fps_limit, master = None):
		threading.Thread(target=importer, name="Importing").start()
		self.loop = asyncio.new_event_loop()
		threading.Thread(target=self.autosaver, daemon=True, name="auto save")
		self.fps_string = fps_limit
		super().__init__(master)

		global nowdata, nowfile, geoli
		self.f1 = font.Font(family = family_li[setjs["Font"]["Family"]], size = 12)

		self.frame = tk.Frame(master)
		self.frame.grid(column=0, row=0, sticky=tk.NSEW)

		self.loop.run_until_complete(self.panel())

		txtframe = tk.Frame(self.frame)
		txtframe.grid(column=1, row=0, sticky=tk.NSEW)

		self.frame.grid_rowconfigure(0, weight=1)
		self.panelframe.grid_rowconfigure(1, weight=1)
		self.panelframe.grid_rowconfigure(0, weight=0)
		self.panelframe["height"]=216
		self.frame.grid_columnconfigure(1, weight=1)

		self.iconreload()

		self.sidefind = tk.PhotoImage(file=f"{assetdir}/__Cache__/icons/{iconsdatali[1]}").subsample(2, 2)

		self.langvar = tk.IntVar(value = langsli.index(setjs["gui"]["lang"]))

		self.sidebar()

		root.title(lang["untitled"][self.langvar.get()] +f" - PyCode {version[0]}")
		try:root.geometry(geoli[0])
		except:
			root.geometry("1140x520")
			if len(geoli) < 1:geoli.append("1140x520")
			else:geoli[0] = "1140x520"
		try:root.state(geoli[1])
		except:
			if len(geoli) < 2:geoli.append("normal")
			else:geoli[1] = "normal"
			root.state("normal")
			if geoli[1] == "zoomed":
				root.geometry("1140x520")
				geoli[0] = "1140x520"
		try:root.attributes('-fullscreen', geoli[2])
		except:
			if len(geoli) < 3:geoli.append("0")
			else:geoli[2] = "0"
		geosave()
		root.minsize(380, 210)
		root.rowconfigure(0, weight=1)
		root.columnconfigure(0, weight=1)

		menubar = tk.Menu(self)

		self.filemenu = tk.Menu(menubar, tearoff = 0, bg=theme["menu"]["bg"], activebackground=theme["menu"]["abg"], fg=theme["menu"]["fg"], activeforeground=theme["menu"]["afg"])
		filemenuli = [[self.newfile, "Ctrl+N", self.newimg, "newfile"], [self.newwindow, "Ctrl+Shift+N", None, "newwindow"], [lambda: self.openfile(False, "text", False), "Ctrl+O", self.openimg, "open"], [self.savefile, "Ctrl+S", self.saveimg, "save"], [lambda: self.saveas(encode, True), "Ctrl+Shift+S", self.asimg, "saveas"]]
		for i in filemenuli:self.filemenu.add_command(label=lang[i[3]][self.langvar.get()], image=i[2], compound="left", command=i[0], accelerator=i[1])
		self.filemenu.add_separator()
		self.autosave = tk.IntVar(value = setjs["AutoSave"])
		self.filemenu.add_checkbutton(label=lang["auto"][self.langvar.get()], command=self.autosaveset, variable=self.autosave)
		self.filemenu.add_separator()
		self.filemenu.add_command(label = lang["exit"][self.langvar.get()], compound="left", command = self.closesavecheck, accelerator = "Alt+F4")

		self.editmenu = tk.Menu(menubar, tearoff = 0, bg=theme["menu"]["bg"], activebackground=theme["menu"]["abg"], fg=theme["menu"]["fg"], activeforeground=theme["menu"]["afg"])
		
		self.editmenu.add_command(label = lang["undo"][self.langvar.get()], image=self.undoimg, compound="left", command = lambda: self.reundo("un"), accelerator = "Ctrl+Z")
		self.editmenu.add_command(label = lang["redo"][self.langvar.get()], command = lambda: self.reundo("re"), accelerator = "Ctrl+Y")
		self.editmenu.add_separator()
		self.editmenu.add_command(label = lang["cut"][self.langvar.get()], image=self.cutimg, compound="left", accelerator="Ctrl+X", command=lambda: self.copypaste("x"))
		self.editmenu.add_command(label = lang["copy"][self.langvar.get()], image=self.copyimg, compound="left", accelerator="Ctrl+C", command=lambda: self.copypaste("c"))
		self.editmenu.add_command(label = lang["paste"][self.langvar.get()], image=self.pasteimg, compound="left", accelerator="Ctrl+V", command=lambda: self.copypaste("v"))
		self.editmenu.add_separator()
		self.editmenu.add_command(label="Find...(Beta)", accelerator="Ctrl+F", image=self.findimg, compound="left", command=self.sidebarpack)
		self.editmenu.add_command(label="Replace...", accelerator="Ctrl+H", image=self.replaceimg, compound="left", command=self.sidebarpack, state="disabled")
		
		self.convmenu = tk.Menu(menubar, tearoff = 0, bg=theme["menu"]["bg"], activebackground=theme["menu"]["abg"], fg=theme["menu"]["fg"], activeforeground=theme["menu"]["afg"])

		self.encmenu = tk.Menu(self.convmenu, tearoff = 0, bg=theme["menu"]["bg"], activebackground=theme["menu"]["abg"], fg=theme["menu"]["fg"], activeforeground=theme["menu"]["afg"])
		self.encmenu.add_command(label="Shift-JIS", command=lambda: self.enc("cp932"))
		self.encmenu.add_command(label="JIS", command=lambda: self.enc("iso-2022-jp"))
		self.encmenu.add_command(label="UTF-8", command=lambda: self.enc("utf-8"))
		self.encmenu.add_command(label="UTF-7", command=lambda: self.enc("utf-7"))
		self.encmenu.add_separator()
		self.encmenu.add_command(label="US-ASCII", command=lambda: self.enc("ascii"))

		self.reopmenu = tk.Menu(self.convmenu, tearoff = 0, bg=theme["menu"]["bg"], activebackground=theme["menu"]["abg"], fg=theme["menu"]["fg"], activeforeground=theme["menu"]["afg"])
		self.reopmenu.add_command(label="Shift-JIS", command=lambda: self.reop("cp932"))
		self.reopmenu.add_command(label="JIS", command=lambda: self.reop("iso-2022-jp"))
		self.reopmenu.add_command(label="UTF-8", command=lambda: self.reop("utf-8"))
		self.reopmenu.add_command(label="UTF-7", command=lambda: self.reop("utf-7"))
		self.reopmenu.add_separator()
		self.reopmenu.add_command(label="US-ASCII", command=lambda: self.reop("ascii"))

		self.convmenu.add_cascade(label = lang["convert"][self.langvar.get()], menu=self.encmenu)
		self.convmenu.add_cascade(label = lang["reopen"][self.langvar.get()], menu=self.reopmenu)
		
		self.runmenu = tk.Menu(menubar, tearoff = 0, bg=theme["menu"]["bg"], activebackground=theme["menu"]["abg"], fg=theme["menu"]["fg"], activeforeground=theme["menu"]["afg"])
		self.runmenu.add_command(label = "Python", command = lambda: self.runpy(True), accelerator = "F5")
		self.runmenu.add_command(label = "Python(" + lang["noconsole"][self.langvar.get()] + ")", command = lambda: self.runpy(False), accelerator = "Ctrl+F5")
		self.runmenu.add_command(label=lang["openwith"][self.langvar.get()], command=lambda: self.openfile(False, "webopen", False))

		self.viewmenu = tk.Menu(menubar, tearoff = 0, bg=theme["menu"]["bg"], activebackground=theme["menu"]["abg"], fg=theme["menu"]["fg"], activeforeground=theme["menu"]["afg"])

		self.thememenu = tk.Menu(self.viewmenu, tearoff=0, bg=theme["menu"]["bg"], activebackground=theme["menu"]["abg"], fg=theme["menu"]["fg"], activeforeground=theme["menu"]["afg"])
		
		if theme == DefaultTheme:self.themevar = tk.IntVar(value = 1)
		elif theme == DarkTheme:self.themevar = tk.IntVar(value=2)
		elif theme in themes.values():
			for i in range(len(themes)):
				if theme == list(themes.values())[i]:
					self.themevar = tk.IntVar(value=i+3)
					break
		else:self.themevar = tk.IntVar(value=0)

		self.thememenu.add_radiobutton(label=lang["themeli"][self.langvar.get()][0], command=self.themeset, variable=self.themevar, value=1)
		self.thememenu.add_radiobutton(label=lang["themeli"][self.langvar.get()][1], command=self.themeset, variable=self.themevar, value=2)
		for i in range(len(themes)):self.thememenu.add_radiobutton(label=list(themes.keys())[i], command=self.themeset, variable=self.themevar, value=i+3)
		self.thememenu.add_radiobutton(label=lang["themeli"][self.langvar.get()][2], command=lambda: threading.Thread(target=self.themecustom, name="theme-setting", daemon=True).start(), variable=self.themevar, value=0)

		self.fullvar = tk.IntVar(value = geoli[2])
		self.viewmenu.add_checkbutton(label = lang["fullscreen"][self.langvar.get()], command = lambda: self.fullsc(False), accelerator = "F11", variable = self.fullvar)
		self.wrapvar = tk.IntVar(value = setjs["gui"]["wrap"])
		self.viewmenu.add_checkbutton(label = lang["wrap"][self.langvar.get()], command = self.wrapset, variable = self.wrapvar)
		self.pnlfgrid = tk.BooleanVar()
		self.viewmenu.add_checkbutton(label="パネルの表示", command=lambda event=None: self.panelgrid("menu"), variable=self.pnlfgrid)
		self.syntvar = tk.IntVar(value=setjs["gui"]["syntax"]["syntax"])
		self.viewmenu.add_command(label=lang["fontset"][self.langvar.get()], command=self.fontset)
		self.viewmenu.add_cascade(label=lang["theme"][self.langvar.get()], menu=self.thememenu)
		if argfile == f"{assetdir}/Content/Theme.json":self.viewmenu.entryconfig(3, state = "disable")
		self.viewmenu.add_checkbutton(label = lang["syntax"][self.langvar.get()], command = self.syntax, variable = self.syntvar)
		
		self.setmenu = tk.Menu(menubar, tearoff = 0, bg=theme["menu"]["bg"], activebackground=theme["menu"]["abg"], fg=theme["menu"]["fg"], activeforeground=theme["menu"]["afg"])

		self.runpysetmenu = tk.Menu(self.setmenu, tearoff = 0, bg=theme["menu"]["bg"], activebackground=theme["menu"]["abg"], fg=theme["menu"]["fg"], activeforeground=theme["menu"]["afg"])
		self.runpysetmenu.add_command(label = "Python.exe", command = lambda: self.runpyset("py"))
		self.runpysetmenu.add_command(label = "Pythonw.exe", command = lambda: self.runpyset("pyw"))

		self.langmenu = tk.Menu(self.viewmenu, tearoff = 0, bg=theme["menu"]["bg"], activebackground=theme["menu"]["abg"], fg=theme["menu"]["fg"], activeforeground=theme["menu"]["afg"])
		for i in langsli:self.langmenu.add_radiobutton(label=i, command= self.radio, variable=self.langvar, value=langsli.index(i))

		self.encsetmenu = tk.Menu(self.setmenu, tearoff = 0, bg=theme["menu"]["bg"], activebackground=theme["menu"]["abg"], fg=theme["menu"]["fg"], activeforeground=theme["menu"]["afg"])
		self.encsetmenu.add_command(label="Shift-JIS", command=lambda: self.encset("cp932"))
		self.encsetmenu.add_command(label="JIS", command=lambda: self.encset("iso-2022-jp"))
		self.encsetmenu.add_command(label="UTF-8", command=lambda: self.encset("utf-8"))
		self.encsetmenu.add_command(label="UTF-7", command=lambda: self.encset("utf-7"))
		
		self.setmenu.add_cascade(label = lang["language"][self.langvar.get()], menu = self.langmenu)
		self.setmenu.add_cascade(label = "Python", menu = self.runpysetmenu)
		self.setmenu.add_cascade(label = lang["encode"][self.langvar.get()], menu = self.encsetmenu)
		self.setmenu.add_separator()
		self.setmenu.add_command(label = lang["reset"][self.langvar.get()], command = reset)

		self.helpmenu = tk.Menu(menubar, tearoff = 0, bg=theme["menu"]["bg"], activebackground=theme["menu"]["abg"], fg=theme["menu"]["fg"], activeforeground=theme["menu"]["afg"])
		self.helpmenu.add_command(label=lang["about"][self.langvar.get()])

		menubarli = [["file", self.filemenu], ["edit", self.editmenu], ["encode", self.convmenu], ["run", self.runmenu], ["view", self.viewmenu], ["settings", self.setmenu], ["help", self.helpmenu]]
		for i in menubarli:menubar.add_cascade(label = lang[i[0]][self.langvar.get()], menu = i[1])

		self.filemenu.bind_all("<Control-n>", self.newfile)
		self.filemenu.bind_all("<Control-N>", self.newwindow)
		self.filemenu.bind_all("<Control-s>", self.savefile)
		self.filemenu.bind_all("<Control-S>", lambda event=None: self.saveas(encode, True))
		self.runmenu.bind_all("<F5>", lambda c: self.runpy(True))
		self.runmenu.bind_all("<Control-F5>", lambda c: self.runpy(False))
		self.viewmenu.bind_all("<F11>", lambda bind: self.fullsc(True))

		txtframe.grid_rowconfigure(0, weight=1)
		txtframe.grid_columnconfigure(1, weight=1)

		self.linetxt = tk.Text(txtframe, wrap=tk.NONE, width=1, padx=8, takefocus=0)
		self.linetxt.grid(column=0, row=0, rowspan=2, sticky=tk.NS)
		self.linetxt.tag_configure('line', justify='right', foreground=theme["text"]["line"])
		self.linetxt.tag_configure('insert', justify='right', foreground=theme["text"]["insertline"])
		self.linetxt.insert("end", "1", "line")
		self.linetxt["state"] = "disable"
		self.linetxt.configure(bg=theme["text"]["back"], fg=theme["text"]["line"])
		
		self.txt = SyntaxHighlightText(txtframe, wrap=tk.NONE, undo=True)
		self.txt.grid(column=1, row=0, rowspan=2, sticky=tk.NSEW)
		if setjs["gui"]["wrap"] == 1:
			if setjs["gui"]["wrap2"] == "word":self.txt["wrap"] = tk.WORD
			elif setjs["gui"]["wrap2"] == "char":self.txt["wrap"] = tk.CHAR

		self.txt.bind_all("<<Modified>>", self.titlechange)
		self.txt.bind_all("<Control-o>", lambda event=None: app.openfile(False, "text", True, event))
		self.txt.bind("<Button-3>", self.rightclick)
		self.txt.configure(selectbackground=theme["text"]["sback"], selectforeground=theme["text"]["sfore"], bg=theme["text"]["back"], fg=theme["text"]["fore"], insertbackground=theme["text"]["insert"])

		self.dialog = tk.Label(txtframe, text="シンタックスハイライトを実行中...", font=("Segoe UI", 12, "bold"))
		
		self.xbar = tk.Scrollbar(txtframe, orient=tk.HORIZONTAL, command=self.txt.xview, width=20)
		self.xbargrid = False

		self.ybar = tk.Scrollbar(txtframe, command=self.txt.yview, width=20)
		self.ybargrid = False

		self.txt.config(xscrollcommand=self.xbar.set, yscrollcommand=self.ybar.set)

		self.sbartxt = tk.StringVar()
		self.sbartxt.set(setjs["gui"]["encode"])
		self.sbar = ttk.Label(root, textvariable = self.sbartxt, background = theme["statusbar"]["0"], foreground = theme["statusbar"]["0fg"], anchor="e")
		self.sbar.grid(column=0, row=1, sticky=tk.EW)
		self.last_time = perf_counter()
		self.frame_count = 0
		self.fps_limit = fps_limit
		self.enccheck = False
		self.fps = fps_limit
		self.lines = 1
		self.timestack = 0
		self.viewtime = perf_counter()
		self.loop.run_until_complete(self.update_fps())
		root.config(menu = menubar)
		root.iconbitmap(default=f"{assetdir}/Content/pycode.ico")
		root.protocol("WM_DELETE_WINDOW", (lambda: self.closesavecheck)())
		self.fontreload()
		self.programopen()
		print(f"App execution time: {str(time()-starttime)}s")

	async def panel(self):
		global panel, cwd, termdata
		import panel
		cwd = os.getcwd()
		termdata = cwd + ">"
		panel.OS = OS
		panel.user = user
		panel.setjs = setjs
		panel.theme = theme
		panel.si = si
		panel.cwd = cwd
		panel.termdata = termdata
		self.panelframe = panel.panel(self.frame)
		self.panelframe.close.bind("<Button-1>", lambda event=None: self.panelgrid("click"))
		
	def panelgrid(self, type, event=None):
		if type != "menu":self.pnlfgrid.set(value=not(self.pnlfgrid.get()))
		if self.pnlfgrid.get():
			self.panelframe.grid(column=1, row=1, sticky=tk.EW)
			self.panelframe.grid_propagate(False)
			self.panelframe["height"]=216
		else:
			self.panelframe.grid_forget()

	def sidebar(self):
		sideframe = tk.Frame(self.frame, bg="#21252b")
		sideframe.grid(column=0, row=0, rowspan=2, sticky=tk.NS)
		
		self.sidebaricon = tk.Frame(sideframe, bg="#21252b", bd=1, relief="groove")
		self.sidebaricon.pack(side=tk.LEFT, fill=tk.Y)

		sidebutton = tk.Button(self.sidebaricon, image=self.sidefind, bg="#21252b", activebackground="#21252b", bd=0, relief="flat", cursor="hand2", command=self.sidebarpack)
		sidebutton.pack()

		self.sidebarfind = tk.Frame(sideframe, bg="#21252b", bd=1, relief="groove")
		self.findpacked = False

		findentryframe = tk.Frame(self.sidebarfind, bg="#21252b")
		findentryframe.pack()

		findtitle = tk.Label(findentryframe, text="検索", fg="#ffffff", bg="#21252b")
		findtitle.pack()
		self.sidereplace = tk.PhotoImage(file=f"{assetdir}/__Cache__/icons/{iconsdatali[6]}").subsample(4, 4)
		replacebutton = tk.Button(findentryframe, image=self.sidereplace, bg="#21252b", activebackground="#21252b", bd=0, relief="flat", cursor="hand2")
		replacebutton.pack(side=tk.RIGHT)
		self.findentry = tk.Text(findentryframe, width=25, height=1)
		self.findentry.pack(padx=10, pady=2)
		self.findjob = None
		self.findentry.bind('<<Modified>>', self.findcom)
		self.findentry.configure(fg="#ffffff", bg="#21252b")
		self.replaceentry = tk.Text(findentryframe, width=25, height=1)
		self.replaceentry.pack(padx=10, pady=2)
		self.replaceentry.configure(fg="#ffffff", bg="#21252b")
		self.findlist = ()
		self.findlistvar = tk.StringVar(value=self.findlist)
		self.listboxscrollpack = False
		self.listboxframe = tk.Frame(self.sidebarfind)
		self.listboxframe.pack(fill=tk.BOTH, expand=True)
		self.listbox = tk.Listbox(self.listboxframe, bd=0, relief="flat", selectmode=tk.SINGLE, listvariable=self.findlistvar, selectborderwidth=0)
		self.replacelist = tk.StringVar(value=())
		self.listboxscroll = tk.Scrollbar(self.sidebarfind, orient=tk.VERTICAL, command=self.listbox.yview)
		self.listbox["font"] = self.f1
		self.findentry["font"] = self.f1
		self.replaceentry["font"] = self.f1
		self.listbox.pack(fill=tk.BOTH, expand=True)
		self.listbox.bind('<<ListboxSelect>>', self.listselect)
		self.listbox.configure(fg="#abb2bf", bg="#21252b")
		self.listbox["yscrollcommand"] = self.listboxscroll.set

	async def update_fps(self):
		self.frame_count += 1
		if int(self.txt.index('end-1c').split('.')[0])<self.lines:
			for i in range(self.lines, int(self.txt.index('end-1c').split('.')[0]), -1):
				self.linetxt["state"] = "normal"
				self.linetxt.delete(self.linetxt.index("end-1c linestart"), "end")
				self.linetxt["state"] = "disable"
		else:
			for i in range(self.lines, int(self.txt.index('end-1c').split('.')[0])):
				self.linetxt["state"] = "normal"
				self.linetxt.insert("end", "\n" + str(i+1), "line")
				self.linetxt["state"] = "disable"
		insert = self.txt.index("insert").split(".")[0]
		self.linetxt.tag_remove("insert", "1.0", "end")
		self.linetxt.tag_add("insert", f"{insert}.0", f"{insert}.end")

		self.linetxt["width"] = len(str(self.lines))
		self.linetxt.yview_moveto(self.ybar.get()[0])
		self.lines = int(self.txt.index('end-1c').split('.')[0])
		
		li = self.txt.index("insert").split(".")
		if self.txt.tag_ranges(tk.SEL):sel = len(self.txt.get("sel.first", "sel.last"))
		else:sel = 0
		temptxt = self.sbartxt.get()
		extension = os.path.splitext(nowfile)[1]


		if runcheck == 0:
			if extension == ".py" or extension == ".pyw":
				temptxt = f" | {pyversion} | {encode} "	
			elif extension in self.txt.extension_to_lexer:temptxt = " | " + self.txt.extension_to_lexer[extension].replace("Lexer", "") + f" | {encode} "
			else:temptxt = f" | {encode} "
		else:
			temptxt = f" | {pyversion} | {encode} "
		
		current_time = perf_counter()
		
		self.fps = round(self.frame_count / (current_time - self.last_time), 2)

		if perf_counter() - self.viewtime >= 1:
			self.viewtime = perf_counter()
			self.fps_string = f"fps: {self.fps} | "
		
		self.last_time = current_time
		self.frame_count = 0

		if self.fps_string == self.fps_limit:self.fps_string = ""

		sbartemp = lang["line"][self.langvar.get()] + str(li[0]) + lang["column"][self.langvar.get()] + f" {int(li[1]) + 1}"
		if sel != 0:sbartemp += f" ({sel} " + lang["selected"][self.langvar.get()] + f"){temptxt}"
		else:sbartemp += f"{temptxt}"

		self.sbartxt.set(self.fps_string + sbartemp)
		if runcheck != 0:self.sbar.configure(foreground=theme["statusbar"]["0fg"])
		else:self.sbar.configure(foreground=theme["statusbar"]["1fg"])

		#print(max(1, int(1000/self.fps_limit - (perf_counter() - current_time)*1000)))
		if self.fps*0.8 <= self.fps_limit:
			self.timestack += 1
		if self.fps*1.1 >= self.fps_limit:
			self.timestack -= 1
		time_to_wait = max(1, int(1000/self.fps_limit - (perf_counter() - current_time)*1000)-self.timestack)
		#print(self.fps, self.fps*0.7 <= self.fps_limit, self.timestack)
		#sleep(time_to_wait)
		
		if self.xbar.get() == (0.0, 1.0):
			if self.xbargrid:
				self.xbar.grid_remove()
				self.xbargrid = False
		elif self.xbar.get() != (0.0, 0.0, 0.0, 0.0):
			if not self.xbargrid:
				self.xbar.grid(column=0, row=1, columnspan=2, sticky=tk.EW)
				self.xbargrid = True
			if float(self.ybar.get()[0]) != 0.0 and float(self.ybar.get()[1]) == 1.0:
				text = self.txt.get("1.0", "end-1c")
				last_char = text[-1] if text else ""
				is_newline = last_char.endswith("\n")
				if not is_newline:self.txt.insert("end-1c", "\n")
		if self.ybar.get() == (0.0, 1.0):
			if self.ybargrid:
				self.ybar.grid_remove()
				self.ybargrid = False
		elif self.ybar.get() != (0.0, 0.0, 0.0, 0.0) and self.ybar.get() != (0.0, 0.05):
			if not self.ybargrid:
				self.ybar.grid(column=2, rowspan=2, row=0, sticky=tk.NS)
				self.ybargrid = True
		if self.listboxscroll.get() == (0.0, 1.0):
			if self.listboxscrollpack:
				self.listboxscroll.pack_forget()
				self.listboxscrollpack = False
		elif self.listboxscroll.get() != (0.0, 0.0, 0.0, 0.0) and self.listboxscroll.get() != (0.0, 0.05):
			if not self.listboxscrollpack:
				self.listboxframe.pack_forget()
				self.listboxscroll.pack(side=tk.RIGHT, fill=tk.Y)
				self.listboxframe.pack(fill=tk.BOTH, expand=True)
				self.listboxscrollpack = True
		root.after(time_to_wait, lambda: asyncio.run(self.update_fps()))

	def listselect(self, event):
		try:
			findget = self.findentry.get("1.0", "end-1c")
			replaceget = self.replaceentry.get("1.0", "end-1c")
			last_selected_item = self.listbox.get(event.widget.curselection())
			returncount = 1
			for i in range(self.findlist.index(last_selected_item) + 1):
				returncount += str(self.txt.get("1.0", "end-1c")).split(findget)[i].count("\n")
			self.txt.yview_moveto(0.0)
			self.txt.yview_scroll(returncount-1, "units")
			self.listbox.select_clear(0, tk.END)
		except:pass

	def sidebarpack(self):
		if self.findpacked:
			self.sidebarfind.pack_forget()
			self.findpacked = False
		else:
			self.sidebarfind.pack(fill=tk.Y, expand=True)
			self.findpacked = True

	def find(self):
		self.txt.tag_remove("find", "1.0", "end")
		findlist = []
		self.findlist = ()
		listtemp = []
		if self.findentry.get("1.0", "end-1c") != "":
			pattern = re.compile(self.findentry.get("1.0", "end-1c"))
			for match in pattern.finditer(self.txt.get("1.0", "end")):
				start, end = match.span()
				start = '1.0+%dc' % start
				end = '1.0+%dc' % end
				self.txt.tag_add("find", start, end)
			findlist = self.txt.get("1.0", "end-1c").split(self.findentry.get("1.0", "end-1c"))
			del findlist[0]
			for i in findlist:listtemp.append(str(self.findentry.get("1.0", "end-1c") + i)[:40])
		self.findlist = listtemp
		self.findlistvar.set(self.findlist)

	def findcom(self, e):
		if self.findjob:self.after_cancel(self.findjob)
		try:
			if setjs["gui"]["syntax"]["syntax"] == 1:self.findjob = self.after(500, self.find)
		except:pass

	def replace(self):
		pass

	def iconconfig(self):
		filemenu = [[0, self.newimg], [2, self.openimg], [3, self.saveimg], [4, self.asimg]]
		for i in filemenu:self.filemenu.entryconfigure(i[0], image=i[1])
		editmenu = [[0, self.undoimg], [3, self.cutimg], [4, self.copyimg], [5, self.pasteimg], [7, self.findimg], [8, self.replaceimg]]
		for i in editmenu:self.editmenu.entryconfigure(i[0], image=i[1])

	def iconreload(self):
		iconload()
		iconspath = f"{assetdir}/Content/icons/"
		self.undoimg = tk.PhotoImage(file=f"{iconspath}{iconsdatali[0]}").subsample(3, 3)
		self.findimg = tk.PhotoImage(file=f"{iconspath}{iconsdatali[1]}").subsample(3, 3)
		self.cutimg = tk.PhotoImage(file=f"{iconspath}{iconsdatali[2]}").subsample(3, 3)
		self.saveimg = tk.PhotoImage(file=f"{iconspath}{iconsdatali[3]}").subsample(3, 3)
		self.pasteimg = tk.PhotoImage(file=f"{iconspath}{iconsdatali[4]}").subsample(3, 3)
		self.openimg = tk.PhotoImage(file=f"{iconspath}{iconsdatali[5]}").subsample(3, 3)
		self.replaceimg = tk.PhotoImage(file=f"{iconspath}{iconsdatali[6]}").subsample(3, 3)
		self.copyimg = tk.PhotoImage(file=f"{iconspath}{iconsdatali[7]}").subsample(3, 3)
		self.asimg = tk.PhotoImage(file=f"{iconspath}{iconsdatali[8]}").subsample(3, 3)
		self.newimg = tk.PhotoImage(file=f"{iconspath}{iconsdatali[9]}").subsample(3, 3)
		try:self.iconconfig()
		except:pass

	def themeset(self, event=None):
		with open(f"{assetdir}/Content/Theme.json", "w", encoding="utf-8") as themef:
			if self.themevar.get() == 1:json.dump(DefaultTheme, themef, indent=4)
			elif self.themevar.get() == 2:json.dump(DarkTheme, themef, indent=4)
			elif self.themevar.get() > 2:json.dump(list(themes.values())[self.themevar.get()-3], themef, indent=4)
		self.themereload()

	def themecustom(self, event=None):
		if os.path.splitext(selfname)[1] == ".exe":p = subprocess.Popen([selfname, f"{assetdir}/Content/Theme.json", "--lebel", "2"], start_new_session=True)
		elif os.path.splitext(selfname)[1] == ".py" or os.path.splitext(selfname)[1] == ".pyw":p = subprocess.Popen(["pyw", selfname, f"{assetdir}/Content/Theme.json", "--lebel", "2"])
		p.wait()
		self.themereload()

	def programopen(self):
		global encode, argfile, nowdata, nowfile
		if OS == "Windows":
			if argfile != "" and not(":" in argfile):argfile = os.path.join(selfdir, argfile)
		if argfile != "" and os.path.isfile(argfile) and argdata == "":
			try:
				with open(argfile, "r", encoding="utf-8") as f:temp = f.read()
				encode = "utf-8"
				if "" in temp:raise
			except:
				try:
					with open(argfile, "r", encoding="cp932") as f:temp = f.read()
					encode = "cp932"
					if "" in temp:raise
				except:
					try:
						with open(argfile, "r", encoding="iso-2022-jp") as f:temp = f.read()
						encode = "iso-2022-jp"
						if "" in temp:raise
					except:
						try:
							with open(argfile, "r", encoding="utf-7") as f:temp = f.read()
							encode = "utf-7"
							if "" in temp:raise
						except:encode = None
			encerr = True
			if encode == None:
				try:
					with open(argfile, "r", encoding="utf-8") as f:temp = f.read()
					encode = "utf-8"
				except Exception as e:
					encode = setjs["gui"]["encode"]
					encerr = False
					msg.showerror(title=str(e.__class__.__name__), message=e)
			if encode != None and encerr:
				try:
					with open(argfile, "r", encoding = encode) as f:openfiledata = f.read()
					self.txt.delete("1.0", "end")
					self.txt.insert("1.0", openfiledata)
					nowdata = openfiledata
					nowfile = argfile
					self.titlechange_()
					if not os.path.splitext(nowfile)[1] in blacklist:
						threading.Thread(target=self.txt.highlight, daemon=True, name="highlight").start()
				except Exception as e:
					encode = setjs["gui"]["encode"]
					msg.showerror(title=str(e.__class__.__name__), message=e)
		elif argfile != "" and argdata != "":
			self.txt.delete("1.0", "end")
			self.txt.insert("1.0", argdata)
			nowfile = argfile
			nowdata = argdata
			self.titlechange_()
			if not os.path.splitext(nowfile)[1] in blacklist:threading.Thread(target=self.txt.highlight, daemon=True, name="highlight").start()
		elif argfile != "" and not(os.path.isfile(argfile)):
			createfile = msg.askyesno(title="PyCode", message=msgisf[self.langvar.get()], icon=msg.ERROR)
			if createfile:
				cf = open(argfile, "w", encoding=setjs["gui"]["encode"])
				cf.close()
				self.programopen()

	def fontreload(self):
		global ftemp
		try:ftemp = int(setjs["Font"]["Size"])
		except Exception as e:
			msg.showerror(title=str(e.__class__.__name__), message=e)
			ftemp = 11
			setjs["Font"]["Size"] = "11"
			jsonsave()
		if setjs["Font"]["Style"] == 1:styletemp = ["italic", "normal"]
		elif setjs["Font"]["Style"] == 2:styletemp = ["roman", "bold"]
		elif setjs["Font"]["Style"] == 3:styletemp = ["italic", "bold"]
		else:
			styletemp = ["roman", "normal"]
			if setjs["Font"]["Style"] != 0:
				setjs["Font"]["Style"] == 0
				jsonsave()
		self.f1 = font.Font(family=family_li[setjs["Font"]["Family"]],size=ftemp, slant=styletemp[0], weight=styletemp[1])
		li = [self.filemenu, self.editmenu, self.runmenu, self.setmenu, self.viewmenu, self.thememenu, self.langmenu, self.runpysetmenu, self.convmenu, self.encmenu, self.reopmenu, self.encsetmenu, self.helpmenu, self.txt, self.linetxt, self.sbar, self.listbox, self.findentry, self.replaceentry]
		for i in li:i["font"] = self.f1
	
	def themereload(self):
		themeload()
		self.linetxt.configure(bg=theme["text"]["back"], selectbackground=theme["text"]["back"], selectforeground=theme["text"]["fore"])
		self.linetxt.tag_configure('line', justify='right', foreground=theme["text"]["line"])
		self.linetxt.tag_configure('insert', justify='right', foreground=theme["text"]["insertline"])
		self.txt.configure(bg=theme["text"]["back"], fg=theme["text"]["fore"], selectbackground=theme["text"]["sback"], selectforeground=theme["text"]["sfore"], insertbackground=theme["text"]["insert"])
		self.panelframe.termtxt.configure(bg=theme["text"]["back"], fg=theme["text"]["fore"], selectbackground=theme["text"]["sback"], selectforeground=theme["text"]["sfore"], insertbackground=theme["text"]["insert"])
		if runcheck != 0:self.sbar.configure(background=theme["statusbar"]["1"], foreground=theme["statusbar"]["1fg"])
		else:self.sbar.configure(background=theme["statusbar"]["0"], foreground=theme["statusbar"]["0fg"])
		for i in [self.filemenu, self.editmenu, self.convmenu, self.encmenu, self.reopmenu, self.runmenu, self.viewmenu, self.thememenu, self.setmenu, self.runpysetmenu, self.langmenu, self.encsetmenu]:#, self.helpmenu]:
			i.configure(bg=theme["menu"]["bg"], activebackground=theme["menu"]["abg"], fg=theme["menu"]["fg"], activeforeground=theme["menu"]["afg"])
		self.txt.highlightcolorset()
		self.iconreload()

	def fontset(self):
		def fontreload_(event=None):
			family = family_li.index(combo1.get())
			style = styles.index(combo2.get())
			fsizeget = combo3.get()
			if fsizeget == "14(" + font_set[self.langvar.get()][3] + ")":
				fsizeget = "14"
				if fsizeli[-1] == font_set[self.langvar.get()][4]:fsizeli.pop()
				combo3.configure(values=fsizeli, height=len(fsizeli))
			elif "Custom" in  fsizeget:fsizeget=setjs["Font"]["Size"]
			if setjs["Font"]["Family"] != family:
				setjs["Font"]["Family"] = family
				jsonsave()
			if setjs["Font"]["Style"] != style:
				setjs["Font"]["Style"] = style
				jsonsave()
			if str(setjs["Font"]["Size"]) != fsizeget:
				setjs["Font"]["Size"] = fsizeget
				jsonsave()
				if fsizeli[-1] == font_set[self.langvar.get()][4]:fsizeli.pop()
				combo3.configure(values=fsizeli, height=len(fsizeli))
			app.fontreload()
			lblf["font"] = self.f1
			lblfam["font"] = self.f1
			combo1["font"] = self.f1
			lblsty["font"] = self.f1
			combo2["font"] = self.f1
			lblsize["font"] = self.f1
			combo3["font"] = self.f1
			#self.f1 = font.Font(size=ftemp)
			#self.panelframe.termtxt["font"] = self.f1
		root.grab_set()
		configapp = tk.Toplevel()
		configapp.attributes("-topmost", True)
		configapp.title(lang["fontset"][self.langvar.get()])
		configapp.resizable(False, False)
		configapp.grab_set()
		configapp.focus_set()

		lblf = tk.Label(configapp, text=lang["fontset"][self.langvar.get()])
		lblf.grid(columnspan=2, column=0, row=0)
		lblf["font"] = self.f1
		lblfam = tk.Label(configapp, text=font_set[self.langvar.get()][0])
		lblfam.grid(column=0, row=1, padx=10)
		lblfam["font"] = self.f1
		combo1 = ttk.Combobox(configapp, values=family_li, height=10, justify="center", state="readonly", font=(family_li[setjs["Font"]["Family"]], setjs["Font"]["Size"]))
		combo1.current(family_li.index(family_li[setjs["Font"]["Family"]]))
		combo1.grid(column=1, row=1, pady=5, padx=10)
		combo1.bind('<<ComboboxSelected>>', fontreload_)
		combo1["font"] = self.f1
		
		lblsty = tk.Label(configapp, text=font_set[self.langvar.get()][1])
		lblsty.grid(column=0, row=2, padx=10)
		lblsty["font"] = self.f1
		combo2 = ttk.Combobox(configapp, values=styles, height=4, justify="center", state="readonly", font=(family_li[setjs["Font"]["Family"]], setjs["Font"]["Size"]))
		combo2.current(setjs["Font"]["Style"])
		combo2.grid(column=1, row=2, pady=5, padx=10)
		combo2.bind('<<ComboboxSelected>>', fontreload_)
		combo2["font"] = self.f1

		lblsize = tk.Label(configapp, text=font_set[self.langvar.get()][2])
		lblsize.grid(column=0, row=3, padx=10)
		lblsize["font"] = self.f1
		fsizeli = ["8", "9", "10", "11", "12", "13", "14(" + font_set[self.langvar.get()][3] + ")", "15", "16", "17", "18"]
		combo3 = ttk.Combobox(configapp, values=fsizeli, height=len(fsizeli), justify="center", state="readonly", font=(family_li[setjs["Font"]["Family"]], setjs["Font"]["Size"]))

		if setjs["Font"]["Size"] == "14":combo3.current(fsizeli.index("14(" + font_set[self.langvar.get()][3] + ")"))
		elif setjs["Font"]["Size"] in fsizeli:combo3.current(fsizeli.index(str(setjs["Font"]["Size"])))
		else:
			fsizeli.append(font_set[self.langvar.get()][4])
			combo3.configure(values=fsizeli)
			combo3.current(fsizeli.index(font_set[self.langvar.get()][4]))
		combo3.grid(column=1, row=3, pady=5, padx=10)
		combo3.bind('<<ComboboxSelected>>', fontreload_)
		btn = ttk.Button(configapp, text="OK", command=configapp.destroy)
		btn.grid(column=1, row=4, pady=10, padx=10, sticky=tk.E)
		configapp.mainloop()
		try:root.grab_release()
		except:pass

	def copypaste(self, cxv):
		if cxv == "v":
			try:
				clipboard = str(pyperclip.paste())
				if clipboard != "":self.txt.insert(self.txt.index(tk.INSERT), clipboard)
			except:pass
		else:
			try:
				selected_text = self.txt.get("sel.first", "sel.last")
				if selected_text:
					if cxv == "c":pyperclip.copy(selected_text)
					elif cxv == "x":
						pyperclip.copy(selected_text)
						self.txt.delete("sel.first", "sel.last")
			except:pass

	def autosaver(self):
		while setjs["AutoSave"] == 1:
			if setjs["AutoSave"] == 1 and nowfile != "":
				if not(self.filecheck()):self.savefile()
			for i in range(60):
				sleep(1)
				if setjs["AutoSave"] == 0:break

	def autosaveset(self):
		setjs["AutoSave"] = self.autosave.get()
		jsonsave()
		threading.Thread(target=self.autosaver, daemon=True, name="auto save")

	def encset(self, enc):
		global encode
		setjs["gui"]["encode"] = enc
		if nowfile == "":encode = enc
		jsonsave()

	def reop(self, to):
		try:
			global nowfile, nowdata, encode, rootopenfile
			if nowfile != "":
				with open(nowfile, "r", encoding=to) as f:nowdata = f.read()
				self.txt.delete("1.0", "end")
				self.txt.insert("1.0", nowdata)
				encode = to
				if not os.path.splitext(nowfile)[1] in blacklist:threading.Thread(target=self.txt.highlight, daemon=True, name="highlight").start()
			elif self.txt.get("1.0", "end-1c") != "":encode = to
			else:
				rootopenfile = tk.Toplevel()#TODO 鮮明化
				rootopenfile.attributes("-topmost", True)
				rootopenfile.withdraw()
				self.openf(False, "text")
				if nowfile != "":self.reop(to)
		except:pass

	def enc(self, to):
		global nowdata, nowfile, encode
		path = self.saveas(to, False)
		if path != False:
			if msg.askyesno(title=langmsg[self.langvar.get()][14], message=langmsg[self.langvar.get()][15]):
				with open(path, "r", encoding=to) as f:nowdata = f.read()
				if nowfile != "" and os.path.isfile(f"{nowfile}.lock"):os.remove(f"{nowfile}.lock")
				nowfile = path
				self.txt.edit_reset()
				encode = to
				self.txt.delete("1.0", "end")
				self.txt.insert("1.0", nowdata)
			if not os.path.splitext(nowfile)[1] in blacklist:threading.Thread(target=self.txt.highlight, daemon=True, name="highlight").start()

	def reundo(self, reun):
		if reun == "re":self.txt.edit_redo()
		elif reun == "un":self.txt.edit_undo()

	def syntax(self):
		syntax = self.syntvar.get()
		setjs["gui"]["syntax"]["syntax"] = syntax
		jsonsave()
		self.txt.on_key_release()

	def radio(self, event=None):
		global geoli
		jsonload()
		if setjs["gui"]["lang"] != langsli[self.langvar.get()]:
			setjs["gui"]["lang"] = langsli[self.langvar.get()]
			jsonsave()
			geoli = [root.geometry().split("+")[0], root.state(), root.attributes('-fullscreen')]
			fc = self.filecheck()
			if fc == None or fc == True:
				root.destroy()
				print(os.path.join(launchfile, "launch.exe"))

				if os.path.splitext(selfname)[1] == ".exe":
					if nowfile != "":app.newwinexeprocess(launchfile, os.path.join(launchfile, "launch.exe"), [nowfile])
					else:app.newwinexeprocess(launchfile, os.path.join(launchfile, "launch.exe"), [])
			
				elif os.path.splitext(selfname)[1] == ".py" or os.path.splitext(selfname)[1] == ".pyw":
					if nowfile != "":subprocess.call(["pyw", selfname, nowfile], start_new_session=True)
					else:subprocess.call(["pyw", selfname], start_new_session=True)
				
			elif fc == False:
				with open(f"{assetdir}/__Cache__/last-session.json", "w", encoding="utf-8") as temp:temp.write('{"File": "' + nowfile + '", "Data": "last-session-data.txt"}')
				with open(f"{assetdir}/__Cache__/last-session-data.txt", "w", encoding="utf-8") as temp:temp.write(self.txt.get("1.0", "end-1c"))
				root.destroy()
				if os.path.splitext(selfname)[1] == ".exe":
					if nowfile != "":app.newwinexeprocess(launchfile, os.path.join(launchfile, "launch.exe"), ["--last-session"])
					else:app.newwinexeprocess(launchfile, os.path.join(launchfile, "launch.exe"), ["--last-session"])
				elif os.path.splitext(selfname)[1] == ".py" or os.path.splitext(selfname)[1] == ".pyw":
					if nowfile != "":subprocess.call(["pyw", selfname, nowfile, "--last-session"], start_new_session=True)
					else:subprocess.call(["pyw", selfname, "--last-session"], start_new_session=True)

	def runpyset(self, exe, event = None):
		if exe == "py":self.openfile(False, "pyexe", False)
		elif exe == "pyw":self.openfile(False, "pywexe", False)

	def titlechange_(self):
		if argfile == f"{assetdir}/Content/Theme.json":title = "Color Theme"
		else:title = nowfile
		fc = self.filecheck()
		if fc == False:
			if nowfile != "":root.title("*" + title +f" - PyCode {version[0]}")
			else:root.title("*" + lang["untitled"][self.langvar.get()] +f" - PyCode {version[0]}")
		else:
			if nowfile != "":root.title(title +f" - PyCode {version[0]}")
			else:root.title(lang["untitled"][self.langvar.get()] +f" - PyCode {version[0]}")
	def titlechange(self, e):
		self.titlechange_()
		e.widget.edit_modified(False)

	def newwinexeprocess(self, cwd, filepath, args):
		subprocess.Popen(["start", filepath] + args, start_new_session=True, shell=True, cwd=cwd)

	def newwindow(self, event=None):
		print(selfname)
		if os.path.splitext(selfname)[1] == ".exe":
			p.Process(target = app.newwinexeprocess, args=(selfname,[],)).start()
		elif os.path.splitext(selfname)[1] == ".py" or os.path.splitext(selfname)[1] == ".pyw":
			threading.Thread(target=lambda: subprocess.call(["pyw", selfname], start_new_session=True)).start()

	def savecheck(self):
		global nowfile, nowdata
		msgres = msg.askyesnocancel(title = langmsg[self.langvar.get()][0], message = langmsg[self.langvar.get()][1])
		if msgres:
			if self.savefile():return True
		elif msgres == False:return False
		return None

	def filecheck(self):
		global nowdata, nowfile
		nowdata = str(self.txt.get("1.0","end-1c"))
		if nowfile != "":
			with open(nowfile, "r", encoding = encode) as f:read = f.read()
			if nowdata == read:return True
			else:
				if nowdata != "":
					if nowdata[-1] == "\n" and read == nowdata[:-1]:return True
					else:return False
				else:
					if read == "":return True
					else:return False
		else:
			if nowdata == "":return None
			else:return False

	def newfile(self, event = None):
		global nowfile, nowdata
		fc = self.filecheck()
		if fc == None or fc == True:
			nowdata = ""
			if nowfile != "" and os.path.isfile(f"{nowfile}.lock"):os.remove(f"{nowfile}.lock")
			nowfile = ""
			self.txt.edit_reset()
			self.txt.delete("1.0", "end")
		elif nowdata != "\n":
			sc = self.savecheck()
			if sc == True or sc == False:
				self.txt.delete("1.0", "end")
				if nowfile != "" and os.path.isfile(f"{nowfile}.lock"):os.remove(f"{nowfile}.lock")
				nowfile = ""
				self.txt.edit_reset()
				nowdata = ""
		#root.title(lang["untitled"][self.langvar.get()] +f" - PyCode {version[0]}")#TODO
	
	def openf(self, c1 , run1):
		def opef():
			global nowdata, nowfile, encode, filename
			if not(filename == () or filename ==""):
				if os.path.getsize(filename) > 524288:
					sizetemp = os.path.getsize(filename)
					size = str(round(sizetemp/1024, 3)) + " KB (" + str(sizetemp) + "Byte)"
					openyn = msg.askyesno(title = langmsg[self.langvar.get()][2], message = langmsg[self.langvar.get()][3] + size)
				else:openyn = True
				if openyn:
					self.enccheck = True
					lock = open(f"{filename}.lock", "w", encoding="utf-8")
					try:
						with open(filename, "r", encoding="utf-8") as f:openfiledata = f.read()
						encode = "utf-8"
						if "" in openfiledata:raise
					except:
						try:
							with open(filename, "r", encoding="cp932") as f:openfiledata = f.read()
							encode = "cp932"
							if "" in openfiledata:raise
						except:
							try:
								with open(filename, "r", encoding="iso-2022-jp") as f:openfiledata = f.read()
								encode = "iso-2022-jp"
								if "" in openfiledata:raise
							except:
								try:
									with open(filename, "r", encoding="utf-7") as f:openfiledata = f.read()
									encode = "utf-7"
									if "" in openfiledata:raise
								except:encode = None
					self.enccheck = False
					encerr = True
					if encode == None:
						lock.close()
						try:
							with open(filename, "r", encoding="utf-8") as f:openfiledata = f.read()
							encode = "utf-8"
						except:
							try:
								with open(filename, "r", encoding="cp932") as f:openfiledata = f.read()
								encode = "cp932"
							except:
								try:
									with open(filename, "r", encoding="iso-2022-jp") as f:openfiledata = f.read()
									encode = "iso-2022-jp"
								except:
									try:
										with open(filename, "r", encoding="utf-7") as f:openfiledata = f.read()
										encode = "utf-7"
									except Exception as e:
										if filename != "" and os.path.isfile(f"{filename}.lock"):os.remove(f"{filename}.lock")
										encerr = False
										encode = setjs["gui"]["encode"]
										msg.showerror(title=str(e.__class__.__name__), message=e)
					if encode != None or encode != "":
						if encerr:
							try:
								if nowfile != "" and os.path.isfile(f"{nowfile}.lock"):os.remove(f"{nowfile}.lock")
								with open(filename, "r", encoding = encode) as f:openfiledata = f.read()
								self.txt.delete("1.0", "end")
								self.txt.insert("1.0", openfiledata)
								nowdata = openfiledata
								nowfile = filename
								self.panelframe.termtxt.insert("end-1c", f"\n")
								os.chdir(os.path.dirname(nowfile))
								self.panelframe.start_command(event=None)
								self.txt.edit_reset()
							except Exception as e:
								encode = setjs["gui"]["encode"]
								msg.showerror(title=str(e.__class__.__name__), message=e)
					if not os.path.splitext(nowfile)[1] in blacklist:
						threading.Thread(target=self.txt.highlight, daemon=True, name="highlight").start()
		global filename, nowfile, nowdata
		dirdialog = f"C:/Users/{user}/Downloads"
		if run1 == "pyexe" or run1 == "pywexe":dirdialog = f"C:/Users/{user}/AppData/Local/Programs/Python"
		if run1 == "Py":typ = [("Python", "*.py *.pyw"), ("TextFile", "*.txt"), ("All Files", "*.*")]
		elif run1 == "text" or run1 == "webopen":typ = [("All Files", "*.*"), ("TextFile", "*.txt"), ("Python", "*.py *.pyw")]
		elif run1 == "pyexe":typ = [("AppFile", "python.exe")]
		elif run1 == "pywexe":typ = [("AppFile", "pythonw.exe")]
		filename = filedialog.askopenfilename(title = lang["open"][self.langvar.get()], filetypes = typ, initialdir = dirdialog)
		rootopenfile.destroy()
		if run1 == "Py":
			opef()
			self.titlechange_()
			if nowfile != "":
				threading.Thread(target = lambda : self.runpy(c1), name = "runpy").start()
				return nowfile
			else:return
		elif run1 == "text":
			opef()
			self.titlechange_()
			if nowfile != "":return nowfile
			else:return
		elif run1 == "webopen":
			webbrowser.open(filename)
		elif run1 == "pyexe" or run1 == "pywexe":
			jsonload()
			if filename != "":
				if run1 == "pyexe":setjs["path"]["python"] = filename
				else:setjs["path"]["pythonw.exe"] = filename
			else:
				setres = msg.askyesno(title = langmsg[self.langvar.get()][4], message = langmsg[self.langvar.get()][5])
				try:
					if setres:
						if run1 == "pyexe":setjs["path"]["python"] = "py"
						else:setjs["path"]["pythonw.exe"] = "pyw"
				except:
					setup.setting(assetdir, setjsdata)
					jsonload()
			jsonsave()
			return "exe"
		
	def openfile(self, c, run_, focus, event=None):
		if str(self.txt.focus_get()) != "." and focus == True:self.txt.delete("insert-1c")

		global nowdata, nowfile, rootopenfile
		fc = self.filecheck()
		rootopenfile = tk.Toplevel()
		rootopenfile.attributes("-topmost", True)
		rootopenfile.withdraw()
		if run_ == "pyexe" or run_ == "pywexe":threading.Thread(target = lambda: self.openf(c, run_), name = "runexedialog").start()
		elif fc == None or fc == True:threading.Thread(target = lambda: self.openf(c, run_), name = "openfiledialog").start()
		else:
			if run_ == "webopen":threading.Thread(target = lambda: self.openf(c, run_), name = "openfiledialog").start()
			else:
				sc = self.savecheck()
				if sc == False or sc == True:threading.Thread(target = lambda: self.openf(c, run_), name = "openfiledialog").start()

	def savefile(self, event = None):
		nowdata = str(self.txt.get("1.0","end-1c"))
		if nowfile != "":
			with open(nowfile, "w", encoding = encode) as f:f.write(nowdata)
			self.titlechange_()
		else:self.saveas(encode, True)

	def saveas(self, enc, yn, event=None):
		global nowfile
		nowdata = str(self.txt.get("1.0","end-1c"))
		rootsaveas = tk.Toplevel()
		rootsaveas.attributes("-topmost", True)
		rootsaveas.withdraw()
		typ = [("TextFile", "*.txt"), ("Python", "*.py *.pyw"), ("All Files", "*.*"), ("No Extension", "*.")]
		savefilepath = filedialog.asksaveasfilename(title = lang["saveas"][self.langvar.get()], defaultextension = ".txt", filetypes = typ)
		rootsaveas.destroy()
		if savefilepath != "":
			if nowfile != "" and yn == True:
				with open(savefilepath, "w", encoding = encode) as f:f.write(nowdata.encode(enc).decode(encode))
			else:
				with open(savefilepath, "w", encoding = enc) as f:f.write(nowdata.encode(enc).decode(enc))
			if yn:
				if nowfile != "" and os.path.isfile(f"{nowfile}.lock"):os.remove(f"{nowfile}.lock")
				nowfile = savefilepath
				self.txt.edit_reset()
			else:return savefilepath
			self.titlechange_()
			return True
		else:
			self.titlechange_()
			return False
	
	def runpy(self, c, event = None):
		def thread(c):
			global runcheck, procid
			self.sbar.configure(background=theme["statusbar"]["1"], foreground=theme["statusbar"]["1fg"])
			if c:runcheck = 2
			else:runcheck = 1
			#run = subprocess.Popen(["start", setjs["path"]["python"], "-Xfrozen_modules=off", nowfile], shell=True, cwd = nowdir)
			self.pnlfgrid.set(True)
			self.panelgrid("menu")
			self.panelframe.termtxt.insert("end", f"{setjs["path"]["python"]} -Xfrozen_modules=off {nowfile}\n")
			self.panelframe.start_command(event=None)
			sleep(0.5)
			while panel.runcheck != 0:
				sleep(0)
				pass
			#TODO
			runcheck = 0
			try:
				self.sbartxt.set(encode)
				self.sbar.configure(background=theme["statusbar"]["0"], foreground=theme["statusbar"]["0fg"])
				self.runmenu.entryconfig(0, state = "normal")
				self.runmenu.entryconfig(1, state = "normal")
			except:pass
		global nowdir
		if self.txt.get("1.0", "end") == "\n":self.openfile(c, "Py", False)
		elif nowfile != "":
			self.savefile()
			self.runmenu.entryconfig(0, state = "disable")
			self.runmenu.entryconfig(1, state = "disable")
			nowdir = os.path.dirname(nowfile)
			threading.Thread(target = lambda: thread(c), name = "RunPython").start()
		else:
			self.saveas(encode, True)
			if nowfile != "":self.runpy(c)

	def closesavecheck(self):
		global geoli
		geoli = [root.geometry().split("+")[0], root.state(), root.attributes('-fullscreen')]
		fc = self.filecheck()
		if fc == None or fc == True:root.destroy()
		elif fc == False:
			sc = self.savecheck()
			if sc == False or sc == True:root.destroy()

	#def killrun():
	#	if runcheck != 0:
	#		if procid != 0:run.send_signal(sig.CTRL_C_EVENT)#TODO

	def clear(self):
		jsonsave()
		fc = self.filecheck()
		if fc == None or fc == True:
			root.destroy()
			print(os.path.join(launchfile, "launch.exe"))

			if os.path.splitext(selfname)[1] == ".exe":
				if nowfile != "":app.newwinexeprocess(launchfile, os.path.join(launchfile, "launch.exe"), [nowfile])
				else:app.newwinexeprocess(launchfile, os.path.join(launchfile, "launch.exe"), [])		
			elif os.path.splitext(selfname)[1] == ".py" or os.path.splitext(selfname)[1] == ".pyw":
				if nowfile != "":subprocess.call(["pyw", selfname, nowfile], start_new_session=True)
				else:subprocess.call(["pyw", selfname], start_new_session=True)

	def fullsc(self, bind, event = None):
		fullsc = self.fullvar.get()
		if not(bind):
			if fullsc == 0:root.attributes('-fullscreen', False)
			elif fullsc == 1:root.attributes('-fullscreen', True)
		elif bind:
			if fullsc == 0:
				self.fullvar.set(1)
				root.attributes('-fullscreen', True)
			elif fullsc == 1:
				self.fullvar.set(0)
				root.attributes('-fullscreen', False)
	
	def rightclick(self, e):
		try:self.editmenu.post(e.x_root, e.y_root)
		except:pass
	
	def wrapset(self):
		jsonload()
		if self.wrapvar.get() == 0:
			self.txt.configure(wrap=tk.NONE)
			setjs["gui"]["wrap"] = 0
		elif self.wrapvar.get() == 1:
			if setjs["gui"]["wrap2"] == "word":self.txt.configure(wrap=tk.WORD)
			elif setjs["gui"]["wrap2"] == "char":self.txt.configure(wrap=tk.CHAR)
			setjs["gui"]["wrap"] = 1
		jsonsave()

class SyntaxHighlightText(tk.Text):
	#Syntax highlighting text widget.
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		#self.text = []

		self.tag_list = list(DefaultTheme["syntax"].keys())
		
		self.extension_to_lexer = lexers
		self.lexer_classes = {}
		for extension, lexer_name in self.extension_to_lexer.items():
			module_name = "pygments.lexers"
			module = importlib.import_module(module_name)
			lexer_class = getattr(module, lexer_name)
			self.lexer_classes[extension] = type(lexer_name, (lexer_class,), {"__module__": module_name})

		self.highlightcolorset()

		self.bind_class('Text', '<KeyRelease>', self.on_key_release)
		self._highlight_job = None

	def highlightcolorset(self):
		for i in self.tag_list:self.tag_configure(f"Token.{i}", foreground=theme["syntax"][i])
		self.tag_configure("find", background=theme["text"]["sback"])
	
	def highlight(self):
		global highlighting
		highlighting += 1
		if setjs["gui"]["syntax"] == 0 or highlighting > 2:
			highlighting -= 1
			return
		if not os.path.splitext(nowfile)[1] in self.extension_to_lexer.keys():
			highlighting -= 1
			return
		while highlighting >= 2:sleep(1)
		
		#Highlight syntax.
		text = self.get('1.0', 'end')
		
		self.mark_set("range_start", "1.0")
		self.tag_delete("all")
		
		try:lexer = self.lexer_classes[os.path.splitext(nowfile)[1]]()
		except:
			highlighting -= 1
			return
		loop = asyncio.new_event_loop()
		asyncio.set_event_loop(loop)
		for token, content in lex(text, lexer):
			self.mark_set("range_end", "range_start + %dc" % len(content))
			loop.run_until_complete(self.highlighting(token))
		highlighting -= 1

	async def highlighting(self, token):
		self.tag_add(str(token), "range_start", "range_end")
		self.mark_set("range_start", "range_end")

	def th(self):
		if not os.path.splitext(nowfile)[1] in blacklist:
			threading.Thread(target=self.highlight, name="Highlight", daemon=True).start()

	def on_key_release(self, event=None):
		if self._highlight_job:
			self.after_cancel(self._highlight_job)
		try:
			if setjs["gui"]["syntax"]["syntax"] == 1:
				self._highlight_job = self.after(2000, self.th)
		except:pass

def jsoncheck():#TODO jsonchecker
	if setjs["version"] != version:
		setjs["version"] = version
	jsonsave()

def jsonload():
	global setjs
	try:
		settxt = open(f"{assetdir}/settings.json", "r", encoding = "utf-8")
		setjs = json.load(settxt)
		settxt.close()
	except Exception as e:
		msg.showerror(title=str(e.__class__.__name__), message=e)
		setup.setting(assetdir, setjsdata)
		settxt.close()
		jsonload()

def jsonsave():
	with open(f"{assetdir}/settings.json", "w", encoding="utf-8") as f:json.dump(setjs, f, indent=4)

def loadlangs():
	if len(langsli)>2:
		temp = langsli[2:]
		for i in temp:
			for j in lang.keys():
				try:
					lang[j].append(langs[i]["lang"][j])
				except:pass
			langmsg.append(langs[i]["messagetext"]["langmsg"])
			msgisf.append(langs[i]["messagetext"]["msgisf"])
			font_set.append(langs[i]["messagetext"]["font_set"])

def addon():
	global themes, addonsjson, addons, langsli, themesli, langfont
	jsontemp = glob.glob(f"{assetdir}/Addons/*.json")
	for i in jsontemp:
		try:
			with open(i, "r", encoding="utf-8") as temp:
				addonsjson.append(json.load(temp))
				addons.append(i)
		except:pass
	for i in addonsjson:
		try:
			if i["type"] == "theme":
				themes[i["name"]] = i["theme"]
				themesli.append(i)
			elif i["type"] == "lang":
				langs[i["name"]] = i
				langsli.append(i["name"])
		except:pass
	loadlangs()

def image_config(image_path, output_path, r, g, b):
	image = Image.open(image_path)
	image = image.convert("RGBA")
	data = image.getdata()

	new_data = []
	for item in data:
		if item[:3] == (255, 255, 255):
			new_data.append((r, g, b, item[3]))
		else:
			new_data.append(item)

	image.putdata(new_data)
	image.save(output_path, "PNG")

def iconload():
	for i in iconsdatali:
		with open(f"{assetdir}/__Cache__/icons/{i}", "wb") as iconfile:iconfile.write(bytes.fromhex(zlib.decompress(base64.b85decode(iconsjson[i])).decode()))
	if "#" in theme["menu"]["fg"]:rgb = c.hex_to_rgb(theme["menu"]["fg"])
	else:rgb = c.name_to_rgb(theme["menu"]["fg"])
	for i in iconsdatali:image_config(f"{assetdir}/__Cache__/icons/{i}", f"{assetdir}/Content/icons/{i}", rgb.red, rgb.green, rgb.blue)

def themeload():
	global theme
	try:
		with open(f"{assetdir}/Content/Theme.json", "r", encoding="utf-8") as f:theme = json.load(f)
		print(themesli)
		#themecheck()#TODO
	except:
		with open(f"{assetdir}/Content/Theme.json", "w", encoding="utf-8") as f:json.dump(DefaultTheme, f, indent=4)
		themeload()

def themecheck():
	global themes, addons, addonsjson
	check = [theme] + [x for x in themes.values()]
	checkfile = [f"{assetdir}/Content/Theme.json"] + themesli
	for h in range(len(check)):
		value = list(check[h]["syntax"].values())
		key = list(check[h]["syntax"].keys())
		for i in [x for x in list(DefaultTheme["syntax"].keys()) if x not in key]:check[h]["syntax"][i] = DefaultTheme["syntax"][i]
		for i in value:
			try:
				if "#" in i:c.hex_to_rgb(i)
				else:c.name_to_rgb(i)
			except:
				try:check[h]["syntax"][key[value.index(i)]] = DefaultTheme["syntax"][key[value.index(i)]]
				except:del check[h]["syntax"][key[value.index(i)]]
		value = list(check[h]["menu"].values())
		key = list(check[h]["menu"].keys())
		for i in [x for x in list(DefaultTheme["menu"].keys()) if x not in key]:check[h["menu"]][i] = DefaultTheme["menu"][i]
		for i in value:
			try:
				if "#" in i:c.hex_to_rgb(i)
				else:c.name_to_rgb(i)
			except:
				try:check[h]["menu"][key[value.index(i)]] = DefaultTheme["menu"][key[value.index(i)]]
				except:del check[h]["menu"][key[value.index(i)]]
		value = list(check[h]["text"].values())
		key = list(check[h]["text"].keys())
		for i in [x for x in list(DefaultTheme["text"].keys()) if x not in key]:check[h]["text"][i] = DefaultTheme["text"][i]
		for i in value:
			try:
				if "#" in i:c.hex_to_rgb(i)
				else:c.name_to_rgb(i)
			except:
				try:check[h]["text"][key[value.index(i)]] = DefaultTheme["text"][key[value.index(i)]]
				except:del check[h]["text"][key[value.index(i)]]
		try:
			if "#" in check[h]["statusbar"]["0"]:c.hex_to_rgb(check[h]["statusbar"]["0"])
			else:c.name_to_rgb(check[h]["statusbar"]["0"])
		except:check[h]["statusbar"]["0"] = DefaultTheme["statusbar"]["0"]
		try:
			if "#" in check[h]["statusbar"]["1"]:c.hex_to_rgb(check[h]["statusbar"]["1"])
			else:c.name_to_rgb(check[h]["statusbar"]["1"])
		except:check[h]["statusbar"]["1"] = DefaultTheme["statusbar"]["1"]
		try:
			if "#" in check[h]["statusbar"]["0fg"]:c.hex_to_rgb(check[h]["statusbar"]["0fg"])
			else:c.name_to_rgb(check[h]["statusbar"]["0fg"])
		except:check[h]["statusbar"]["0fg"] = DefaultTheme["statusbar"]["0fg"]
		try:
			if "#" in check[h]["statusbar"]["1fg"]:c.hex_to_rgb(check[h]["statusbar"]["1fg"])
			else:c.name_to_rgb(check[h]["statusbar"]["1fg"])
		except:check[h]["statusbar"]["1fg"] = DefaultTheme["statusbar"]["1fg"]
		try:
			if "#" in check[h]["link"]["0"]:c.hex_to_rgb(check[h]["link"]["0"])
			else:c.name_to_rgb(check[h]["link"]["0"])
		except:check[h]["link"]["0"] = DefaultTheme["link"]["0"]
		try:
			if "#" in check[h]["link"]["1"]:c.hex_to_rgb(check[h]["link"]["1"])
			else:c.name_to_rgb(check[h]["link"]["1"])
		except:check[h]["link"]["1"] = DefaultTheme["link"]["1"]
		if h == 0:
			with open(checkfile[h], "w", encoding="utf-8") as themef:json.dump(check[h], themef, indent=4)
		else:
			addonsjson[h-1]["theme"] = check[h]
			with open(checkfile[h], "w", encoding="utf-8") as themef:json.dump(addonsjson[h-1], themef, indent=4)

def reset():
	setup.setting(assetdir, setjsdata)
	with open(f"{assetdir}/Content/Theme.json", "w", encoding="utf-8") as themef:json.dump(DefaultTheme, themef, indent=4)
	app.closesavecheck(self=app)
	app.newwindow(self=app)

def geosave():
	if geoli[1] == "zoomed":geoli[0] = "1140x520"
	with open(f"{assetdir}/Content/geometry.txt", "w", encoding="utf-8") as f:f.write(f"{geoli[0]}\n{geoli[1]}\n{geoli[2]}")

def getpyversion():
	global pyversion
	#try:
	PYV = subprocess.run([setjs["path"]["python"], '-V'], capture_output=True, text=True, startupinfo=si)
	pyversion = PYV.stdout.strip()
	#except:pass

def clean_up():
	if nowfile != "" and os.path.isfile(f"{nowfile}.lock"):os.remove(f"{nowfile}.lock")
	geosave()
	print("Cleanup was successfully completed.")
def sig_handler():sys.exit(1)

pyversion = "Python"
sig.signal(sig.SIGTERM, sig_handler)
lang = appdata.lang
langmsg = appdata.langmsg
msgisf = ["The file could not be opened because the file was not found.\nCreate File?", 
"ファイルが見つからなかったため、ファイルを開くことができませんでした。\nファイルを作成しますか？"]
font_set = [["Family", "Style", "Size", "default", "Custom setting"], ["ファミリ", "スタイル", "サイズ", "デフォルト", "カスタム設定"]]

si = subprocess.STARTUPINFO()
si.dwFlags = subprocess.STARTF_USESHOWWINDOW
user = os.getlogin()

selfdir = os.getcwd()
selfname = os.path.abspath(sys.argv[0])

args = sys.argv[1:]
if "--multiprocessing-fork" in args:args.remove("--multiprocessing-fork")

insdir = ""
for i in os.path.dirname(selfname).replace("\\", "/").split("/")[0:-2]:
	insdir += f"{i}/"
insdir = os.path.abspath(insdir[:-1])
launchfile = os.path.abspath(os.path.join(insdir, "Application"))

if OS=="Windows":
	assetdir = os.path.join(insdir, "assets")
	os.chdir(f"C:/Users/{user}")
else:
	assetdir = f"{insdir}/assets"
	os.chdir(f"/home/{user}")

root = tk.Tk()
family_li = sorted(list(font.families()))

if OS=="Windows":Default_family = str(family_li.index("Segoe UI"))
else:Default_family = str(family_li.index("FreeSans"))

pypath = '{"python": "' + str(os.path.join(insdir, "ThirdParty", "python312-32", "python.exe")).replace("\\", "/") + '"}'
setjsdata = '{"version": "' + str(version) + '", "AutoSave":0, "gui": {"lang": 0, "wrap": 0, "wrap2": "word", "syntax": {"syntax": 1, "threads": 5}, "encode": "utf-8"}, "path": ' + pypath + ', "Font": {"Family": ' + Default_family + ', "Style": 0, "Size": "14"}, "update": true}'

setup.main(assetdir, setjsdata)

with open(f"{assetdir}/Content/geometry.txt", "r", encoding="utf-8") as temp:
	geoli = temp.readlines()
	geoli = [x.replace("\n", "") for x in geoli]
with open(f"{assetdir}/Content/Highlight-Blacklist.txt", "r", encoding="utf-8") as temp:blacklist = temp.readlines()
blacklist = [x.replace("\n", "") for x in blacklist]
with open(f"{assetdir}/Content/lexers.json", "r", encoding="utf-8") as temp:
	lexers = json.load(temp)

iconsjson = appdata.iconsjson

jsonload()
jsoncheck()

threading.Thread(target=getpyversion, daemon=True).start()
ctypes.windll.shcore.SetProcessDpiAwareness(1)

encode = setjs["gui"]["encode"]

argfile = ""
argdata = ""

for i in [x for x in args if x.startswith("--")]:
	if i == "--version":
		print(f"{version[0]}")
		sys.exit()
	if i == "--last-session":
		try:
			with open(f"{assetdir}/__Cache__/last-session.json", "r", encoding="utf-8") as temp:
				lastjson = json.load(temp)
			argfile = lastjson["File"]
			with open(assetdir + "/__Cache__/" + lastjson["Data"], "r", encoding="utf-8") as temp:
				argdata = temp.read()
		except:
			argfile = ""
			argdata = ""
		args.remove(i)

for i in [x for x in args if not(x.startswith("--"))]:
	if i == "-V":
		print(f"{version[0]}")
		sys.exit()
	if "parent_pid" in i:args.remove(i)
	if "pipe_handle" in i:args.remove(i)
if len(args) == 1 and argfile == "":
	argfile = args[0]
elif len(args) > 1:
	threading.Thread(target=lambda: msg.showwarning(title="arg warning", message="引数が複数指定されています。"), daemon=True).start()

nowdata = ""
nowfile = ""
runcheck = 0
highlighting = 0
procid = 0
styles = ["Regular", "Italic", "Bold", "Bold Italic"]

DefaultTheme = appdata.DefaultTheme
DarkTheme = appdata.DarkTheme
if not os.path.isfile(f"{assetdir}/Content/Theme.json"):
	with open(f"{assetdir}/Content/Theme.json", "w", encoding="utf-8") as themef:json.dump(DefaultTheme, themef, indent=4)
addonsjson = []
addons = []
themes = {}
themesli = []
langs = {}
langsli = ["English", "日本語"]
langfont = ""
addon()
if not setjs["gui"]["lang"] in langsli:
	setjs["gui"]["lang"] = "English"
	jsonsave()
themeload()

iconsdatali = ['undo.png', 'find.png', 'cut.png', 'save.png', 'paste.png', 'open.png', 'replace.png', 'copy.png', 'saveas.png', 'newfile.png']

iconload()

def start():
	global app
	try:
		app = txtedit(fps_limit=60, master = root)
		app.mainloop()
		sleep(0.5)
	except Exception as e:
		try:root.destroy()
		except:pass
		try:
			regenate = False
			restartyn = True
			if "unknown color name" in str(e):
				with open(f"{assetdir}/Content/Theme.json", "w", encoding="utf-8") as themef:json.dump(DefaultTheme, themef, indent=4)
			#elif e.__class__.__name__ == "ValueError":
			#	pass#TODO
			else:
				restartli = ["Do you want to restart?", "再起動しますか？"]#TODO
				restartyn = msg.askretrycancel(title = langmsg[langsli.index(setjs["gui"]["lang"])][8], message = langmsg[langsli.index(setjs["gui"]["lang"])][9] + f"\nError Code>>>{str(e.__class__.__name__)}", detail=f"{str(e)}\n" + restartli[langsli.index(setjs["gui"]["lang"])], icon=msg.ERROR)
				restartli = ["Do you want to regenerate the settings.json?", "設定ファイルを再生成しますか？"]
				regenate = msg.askyesno(message=restartli[langsli.index(setjs["gui"]["lang"])])
		except Exception as e:
			msg.showerror(title=str(e.__class__.__name__), message=e)
			setup.setting(assetdir, setjsdata)
			restartyn = False
			regenate = False
		if regenate:setup.setting(assetdir, setjsdata)
		if restartyn:
			if os.path.splitext(selfname)[1] == ".exe":p.Process(target = app.newwinexeprocess, args=(selfname,[],)).start()
			elif os.path.splitext(selfname)[1] == ".py" or os.path.splitext(selfname)[1] == ".pyw":p.Process(target = lambda: subprocess.call(["pyw", selfname], start_new_session=True), args=(selfname,[],)).start()
	finally:
		sig.signal(sig.SIGTERM, sig.SIG_IGN)
		sig.signal(sig.SIGINT, sig.SIG_IGN)
		clean_up()
		sig.signal(sig.SIGTERM, sig.SIG_DFL)
		sig.signal(sig.SIGINT, sig.SIG_DFL)
if __name__ == "__main__":
	start()