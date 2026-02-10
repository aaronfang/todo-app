# 🚀 快速打包 - 三步搞定！

## 📋 前置要求

- ✅ Python 3.9+ 已安装
- ✅ 网络连接（首次需下载 PyInstaller）

## 🎯 方法一：自动化打包（推荐）

### Windows 用户

**双击运行批处理文件：**
```
build_exe.bat
```

或者在命令行：
```bash
python build_exe.py
```

### 一键搞定！
脚本会自动：
1. 检查并安装 PyInstaller
2. 构建单文件 EXE
3. 创建发布压缩包
4. 生成使用说明

## 📦 构建完成后

```
release/
├── TodoApp.exe                                  # ← 这就是可分发的程序！
├── README_便携版.txt                            # 用户使用说明
└── TodoApp_v1.0.0_Portable_Windows.zip         # ← 可直接发布！
```

## 🎁 分发给用户

1. 上传 `TodoApp_v1.0.0_Portable_Windows.zip` 到 GitHub Release
2. 用户下载解压后，双击 `TodoApp.exe` 即可使用
3. **无需安装 Python**，开箱即用！

---

## 🔧 方法二：手动命令（适合高级用户）

```bash
# 1. 安装 PyInstaller
pip install pyinstaller

# 2. 一键构建
pyinstaller --onefile --windowed --name=TodoApp --icon=todo_app/app_icon.ico --add-data="todo_app/app_icon.ico;." --add-data="todo_app/app_logo.png;." --hidden-import=tkcalendar --hidden-import=pywinstyles todo_app/todo_app.py

# 3. 完成！EXE 位于: dist/TodoApp.exe
```

---

## 📊 预期结果

- **EXE 大小**: ~15-20 MB
- **构建时间**: 1-3 分钟
- **兼容性**: Windows 7/8/10/11 (64位)

## ⚠️ 常见问题

### Q: 提示找不到 Python？
**A:** 确保 Python 已添加到 PATH 环境变量

### Q: 杀毒软件报警？
**A:** 这是误报，PyInstaller 打包的程序常被误判，添加到白名单即可

### Q: EXE 启动慢？
**A:** 首次启动需要解压到临时目录，正常现象，后续启动会快

### Q: 提示缺少 DLL？
**A:** 安装 Visual C++ Redistributable: https://aka.ms/vs/17/release/vc_redist.x64.exe

---

## 📚 详细文档

更多高级选项和故障排查，请阅读：
- `BUILD_EXE_GUIDE.md` - 完整打包指南

---

**推荐使用方法一（自动化脚本），一键打包，省时省力！**

有问题？查看 `BUILD_EXE_GUIDE.md` 获取帮助。
