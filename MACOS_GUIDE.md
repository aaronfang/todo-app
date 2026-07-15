# macOS 运行与设计说明

## 本地运行

建议使用 python.org 或 Homebrew 提供、且包含 Tk 8.6 的 Python 3.9+：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m todo_app.todo_app
```

## 打包为 `.app`

```bash
python -m pip install -r requirements-macos.txt
python build_macos.py
open dist/To-Do.app
```

脚本会生成 `dist/To-Do.app` 并进行 ad-hoc 签名，适合本机使用。若要分发给其他用户，仍需 Apple Developer ID 签名及 notarization。打包后的任务和配置保存在 `~/Library/Application Support/TodoApp/`，不会写入只读的应用包。

## macOS 交互设计

- 使用 Aqua 原生按钮、系统标题栏和 SF Pro Text。
- 常用操作使用 `Command` 快捷键，同时保留原来的 `Control` 快捷键。
- “显示 → 贴边自动隐藏”控制贴边行为；默认只支持左右边缘。
- 窗口贴边后，在鼠标离开或窗口失焦时延迟收起，保留 8px 热区；移入热区后展开。
- 顶部边缘不自动隐藏，以免和菜单栏、刘海屏安全区域及全屏控件冲突。
- 支持多显示器，以及位于主屏左侧或上方、使用负坐标的外接屏幕。
