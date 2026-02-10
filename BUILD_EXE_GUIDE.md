# 打包成单文件 EXE 指南

## 🎯 快速打包

### 方法 1: 使用自动化脚本（推荐）

```bash
# 运行打包脚本（自动处理所有步骤）
python build_exe.py
```

脚本会自动：
- ✅ 检查并安装 PyInstaller
- ✅ 清理旧构建文件
- ✅ 构建单文件 EXE
- ✅ 创建便携版压缩包
- ✅ 生成使用说明

### 方法 2: 手动命令

```bash
# 1. 安装 PyInstaller
pip install pyinstaller

# 2. 构建单文件 EXE
pyinstaller --onefile --windowed --name=TodoApp --icon=todo_app/app_icon.ico --add-data="todo_app/app_icon.ico;." --add-data="todo_app/app_logo.png;." --hidden-import=tkcalendar --hidden-import=pywinstyles todo_app/todo_app.py

# 3. 生成的 EXE 位于: dist/TodoApp.exe
```

## 📦 构建结果

构建完成后会生成：

```
release/
├── TodoApp.exe                                    # 单文件可执行程序
├── README_便携版.txt                              # 使用说明
└── TodoApp_v1.0.0_Portable_Windows.zip           # 发布压缩包
```

## 🔧 PyInstaller 参数说明

| 参数 | 说明 |
|------|------|
| `--onefile` | 打包成单个 EXE 文件（所有依赖都在里面） |
| `--windowed` | 无控制台窗口（GUI 应用） |
| `--name=TodoApp` | 输出文件名 |
| `--icon=xxx.ico` | 应用程序图标 |
| `--add-data` | 包含额外文件（图标、图片等） |
| `--hidden-import` | 包含隐式导入的模块 |
| `--exclude-module` | 排除不需要的模块（减小体积） |
| `--noconfirm` | 覆盖已有文件不提示 |

## 📊 文件大小对比

| 打包方式 | 大小 | 优点 | 缺点 |
|----------|------|------|------|
| **PyInstaller --onefile** | ~15-20 MB | 真正单文件，易分发 | 首次启动稍慢 |
| **cx_Freeze** | ~30-40 MB | 启动快 | 多文件，需打包目录 |

## 🚀 使用打包好的 EXE

### 用户使用步骤：

1. **解压** `TodoApp_v1.0.0_Portable_Windows.zip`
2. **双击** `TodoApp.exe` 启动
3. **首次运行**会在同目录创建 `todo_app/` 文件夹
4. **数据保存**在本地，完全私密

### 数据文件位置：
```
TodoApp.exe 所在目录/
└── todo_app/
    ├── tasks.json      # 任务数据
    └── config.json     # 应用配置
```

## 🔍 故障排查

### 问题 1: 提示缺少 DLL
**解决**：确保目标电脑安装了 Visual C++ Redistributable
- 下载: https://aka.ms/vs/17/release/vc_redist.x64.exe

### 问题 2: 杀毒软件误报
**解决**：这是 PyInstaller 的常见问题，属于误报
- 将 EXE 添加到白名单
- 或者在构建前使用代码签名证书

### 问题 3: EXE 体积太大
**优化方法**：
```bash
# 使用 UPX 压缩（需要额外下载 UPX）
pyinstaller --onefile --upx-dir=upx_dir ...

# 排除更多不需要的模块
pyinstaller --exclude-module=matplotlib --exclude-module=numpy ...
```

### 问题 4: 首次启动慢
**原因**：单文件 EXE 需要解压到临时目录
**解决**：
- 使用 `--onedir` 代替 `--onefile`（多文件模式）
- 或者接受首次启动延迟（后续启动会快）

## 📝 可选依赖说明

应用有两个可选依赖，不影响核心功能：

```bash
pip install tkcalendar    # 图形化日期选择器（否则使用文本输入）
pip install pywinstyles   # Windows 标题栏主题（否则使用默认样式）
```

这些依赖会被自动打包到 EXE 中（如果已安装）。

## 🎨 自定义打包

### 修改图标
替换 `todo_app/app_icon.ico` 为您的图标文件

### 修改版本信息
创建 `version_info.txt`：
```
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'Your Company'),
        StringStruct(u'FileDescription', u'Todo App'),
        StringStruct(u'FileVersion', u'1.0.0'),
        StringStruct(u'ProductName', u'TodoApp'),
        StringStruct(u'ProductVersion', u'1.0.0')])
    ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
```

然后添加参数：`--version-file=version_info.txt`

## 🔒 安全建议

1. **代码签名**：购买代码签名证书，避免杀毒软件误报
2. **校验和**：发布时提供 SHA256 校验和
3. **来源说明**：在 README 中说明构建环境

## 📋 构建清单

打包前检查：

- [ ] 已测试所有功能正常运行
- [ ] 已更新版本号（`__init__.py`, `setup.py`, `pyproject.toml`）
- [ ] 已更新 CHANGELOG.md
- [ ] 图标和图片文件存在
- [ ] 可选依赖已安装（tkcalendar, pywinstyles）
- [ ] 已在干净环境测试（虚拟机）

打包后检查：

- [ ] EXE 可以双击运行
- [ ] 所有功能正常（子任务、日期、颜色等）
- [ ] 暗色模式切换正常
- [ ] 可以保存和加载任务
- [ ] 在其他电脑上测试（无 Python 环境）

## 🚢 发布流程

1. **构建 EXE**
   ```bash
   python build_exe.py
   ```

2. **测试**
   - 在干净系统测试
   - 检查所有功能
   - 记录文件大小

3. **创建 GitHub Release**
   - 版本号: v1.0.0
   - 上传 ZIP 文件
   - 复制 CHANGELOG 作为说明

4. **更新 README**
   - 更新下载链接
   - 更新文件大小
   - 更新版本号

## 💡 提示

- 使用 **虚拟环境**可以获得更小的 EXE 体积
- 定期清理 `build/` 和 `dist/` 目录
- 保存 `.spec` 文件以便重复构建
- 在多个 Windows 版本上测试（Win10/11）

---

**推荐使用方法 1（自动化脚本）**，它会处理所有细节并生成发布包。
