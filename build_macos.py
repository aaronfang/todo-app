"""Build a launchable macOS .app bundle with PyInstaller."""

from __future__ import annotations

import subprocess
import sys
import plistlib
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def main() -> None:
    if sys.platform != "darwin":
        raise SystemExit("This build script must be run on macOS.")

    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",
        "--name",
        "To-Do",
        "--osx-bundle-identifier",
        "com.todoapp.desktop",
        "--icon",
        str(ROOT / "todo_app" / "app_logo.png"),
        "--paths",
        str(ROOT / "todo_app"),
        "--hidden-import",
        "edge_hide",
        "--collect-all",
        "tkcalendar",
        str(ROOT / "todo_app" / "todo_app.py"),
    ]
    subprocess.run(command, cwd=ROOT, check=True)

    app = ROOT / "dist" / "To-Do.app"
    info_plist = app / "Contents" / "Info.plist"
    with info_plist.open("rb") as stream:
        metadata = plistlib.load(stream)
    metadata.update({
        "CFBundleShortVersionString": "1.0.1",
        "CFBundleVersion": "1",
        "LSApplicationCategoryType": "public.app-category.productivity",
    })
    with info_plist.open("wb") as stream:
        plistlib.dump(metadata, stream)

    subprocess.run(["codesign", "--force", "--deep", "--sign", "-", str(app)], check=True)
    print(f"Built {app}")


if __name__ == "__main__":
    main()
