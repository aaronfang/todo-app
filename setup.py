import sys
from cx_Freeze import setup, Executable

build_exe_options = {
    "packages": ["tkinter", "json", "pathlib"],
    "includes": ["edge_hide"],
    "excludes": ["unittest", "email", "html", "http", "xml"],
    "include_files": [
        ("todo_app/app_icon.ico", "app_icon.ico"),
        ("todo_app/app_logo.png", "app_logo.png"),
        ("todo_app/default_templates.json", "default_templates.json"),
    ],
}

base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name="TodoApp",
    version="1.0.1",
    description="A feature-rich Todo application with python Tkinter GUI",
    options={"build_exe": build_exe_options},
    executables=[Executable("todo_app/todo_app.py", base=base, icon="todo_app/app_icon.ico")],
)
