pyinstaller main.py -i=pycode.ico
pause
@echo off
del /q main.spec
rd /s /q build
pyw exe.pyw
rd /s /q dist