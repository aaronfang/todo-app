"""
Todo App 单文件 EXE 打包脚本
使用 PyInstaller 创建独立可执行文件

使用方法:
    python build_exe.py
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

# 设置 UTF-8 输出
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, 'strict')

def check_pyinstaller():
    """检查并安装 PyInstaller"""
    try:
        import PyInstaller
        print(f"[OK] PyInstaller 已安装: {PyInstaller.__version__}")
        return True
    except ImportError:
        print("[!] PyInstaller 未安装")
        print("\n正在安装 PyInstaller...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
            print("[OK] PyInstaller 安装成功")
            return True
        except:
            print("[ERROR] PyInstaller 安装失败")
            print("\n请手动安装: pip install pyinstaller")
            return False

def check_dependencies():
    """检查可选依赖"""
    print("\n检查可选依赖:")
    
    try:
        import tkcalendar
        print(f"[OK] tkcalendar 已安装")
    except ImportError:
        print("[WARN] tkcalendar 未安装 (可选，用于日期选择器)")
        print("  安装: pip install tkcalendar")
    
    try:
        import pywinstyles
        print(f"[OK] pywinstyles 已安装")
    except ImportError:
        print("[WARN] pywinstyles 未安装 (可选，用于 Windows 标题栏主题)")
        print("  安装: pip install pywinstyles")

def clean_build():
    """清理旧的构建文件"""
    print("\n清理旧构建文件...")
    dirs_to_clean = ['build', 'dist']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"[OK] 已删除 {dir_name}/")
    
    # 删除 spec 文件
    spec_files = list(Path('.').glob('*.spec'))
    for spec in spec_files:
        spec.unlink()
        print(f"[OK] 已删除 {spec}")

def build_exe():
    """使用 PyInstaller 构建单文件 EXE"""
    print("\n开始构建单文件 EXE...")
    print("=" * 60)
    
    # PyInstaller 命令
    cmd = [
        'pyinstaller',
        '--onefile',                                    # 单文件模式
        '--windowed',                                   # 无控制台窗口
        '--name=TodoApp',                               # 输出文件名
        '--icon=todo_app/app_icon.ico',                # 应用图标
        '--paths=todo_app',                             # 查找同目录模块
        '--add-data=todo_app/app_icon.ico;.',          # 包含图标
        '--add-data=todo_app/app_logo.png;.',          # 包含 Logo
        '--add-data=todo_app/default_templates.json;.', # 包含默认模板
        '--hidden-import=tkinter',                      # 确保包含 tkinter
        '--hidden-import=tkinter.ttk',                  # 确保包含 ttk
        '--hidden-import=edge_hide',                    # 确保包含贴边隐藏模块
        '--hidden-import=tkcalendar',                   # 可选依赖
        '--hidden-import=pywinstyles',                  # 可选依赖
        '--collect-all=tkcalendar',                     # 收集 tkcalendar 所有文件
        '--exclude-module=unittest',                    # 排除不需要的模块
        '--exclude-module=test',
        '--exclude-module=setuptools',
        '--exclude-module=pip',
        '--noconfirm',                                  # 覆盖已有文件
        'todo_app/todo_app.py'                         # 主程序
    ]
    
    try:
        # 执行构建
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print("✗ 构建失败:")
        print(e.stderr)
        return False

def create_portable_package():
    """创建便携版压缩包"""
    print("\n创建便携版压缩包...")
    
    exe_path = Path('dist/TodoApp.exe')
    if not exe_path.exists():
        print(f"✗ 找不到 {exe_path}")
        return False
    
    # 获取文件大小
    size_mb = exe_path.stat().st_size / (1024 * 1024)
    print(f"✓ EXE 文件大小: {size_mb:.2f} MB")
    
    # 创建发布目录
    release_dir = Path('release')
    release_dir.mkdir(exist_ok=True)
    
    # 复制 EXE 到发布目录
    target_exe = release_dir / 'TodoApp.exe'
    shutil.copy2(exe_path, target_exe)
    print(f"✓ 已复制到 {target_exe}")
    
    # 创建 README
    readme_content = """# Todo App v1.0.1 - 便携版

## 📦 使用说明

这是 Todo App 的便携版本，无需安装，双击即可运行。

### 🚀 快速开始

1. 双击 `TodoApp.exe` 启动应用
2. 首次运行会在同目录创建 `todo_app/` 文件夹存储数据
3. 所有任务数据保存在本地，完全私密

### 💾 数据存储

- `todo_app/tasks.json` - 您的任务数据
- `todo_app/config.json` - 应用设置（暗色模式、字体大小等）
- `todo_app/templates.json` - 用户模板数据

模板也可以在“模板管理”中导出为 JSON，再在另一台电脑导入。

### ⌨️ 快捷键

**任务管理**
- Ctrl+S - 添加子任务
- Ctrl+D - 标记完成
- Ctrl+U - 标记紧急
- Ctrl+J - 标记取消
- Ctrl+E - 编辑任务
- Ctrl+Del - 删除任务
- Ctrl+A - 全选

**视图**
- Ctrl+R - 切换暗色模式
- Ctrl+Plus/Minus - 调整字体大小
- Ctrl+0 - 重置字体
- Ctrl+H - 关于

### ✨ 主要功能

- ✅ 子任务 - 无限层级，智能自动完成
- 📅 截止日期 - 超期提醒
- 🔥 紧急标记 - 红色高亮
- 🎨 自定义颜色 - 12种预设
- 📂 分组管理 - 使用 `---标题` 创建分组
- ✔️ 已完成区域 - 可折叠
- 🌓 暗色模式 - 护眼主题
- 🖱️ 拖拽排序 - 鼠标重排任务

### 🔒 隐私保护

- 100% 本地存储，无云同步
- 无需网络连接
- 无第三方追踪
- 开源 GPL v3 许可

### 📞 支持

- 源代码: https://github.com/jltk/todo-app
- 问题反馈: GitHub Issues
- 许可证: GNU General Public License v3.0

---

**版本**: v1.0.1
**构建日期**: 2026-08-04
**原作者**: Jens Lettkemann
**增强版**: Aaron
"""
    
    readme_file = release_dir / 'README_便携版.txt'
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print(f"✓ 已创建 {readme_file}")
    
    # 创建压缩包
    try:
        import zipfile
        
        zip_name = f'TodoApp_v1.0.1_Portable_Windows.zip'
        zip_path = Path('release') / zip_name
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(target_exe, 'TodoApp.exe')
            zipf.write(readme_file, 'README_便携版.txt')
        
        zip_size_mb = zip_path.stat().st_size / (1024 * 1024)
        print(f"✓ 已创建压缩包: {zip_name} ({zip_size_mb:.2f} MB)")
        return True
        
    except Exception as e:
        print(f"⚠ 无法创建压缩包: {e}")
        print("  您可以手动压缩 release/ 目录")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("Todo App v1.0.1 - 单文件 EXE 构建脚本")
    print("=" * 60)
    
    # 检查环境
    if not check_pyinstaller():
        return
    
    check_dependencies()
    
    # 询问是否清理
    print("\n" + "=" * 60)
    response = input("是否清理旧构建文件? (Y/n): ").strip().lower()
    if response in ['', 'y', 'yes']:
        clean_build()
    
    # 构建
    print("\n" + "=" * 60)
    if not build_exe():
        print("\n✗ 构建失败!")
        return
    
    print("\n" + "=" * 60)
    print("✓ 构建成功!")
    print("=" * 60)
    
    # 创建发布包
    if create_portable_package():
        print("\n" + "=" * 60)
        print("🎉 打包完成!")
        print("=" * 60)
        print("\n📦 发布文件:")
        print("  - release/TodoApp.exe")
        print("  - release/TodoApp_v1.0.1_Portable_Windows.zip")
        print("\n📝 使用说明:")
        print("  - 解压 ZIP 文件")
        print("  - 双击 TodoApp.exe 运行")
        print("  - 无需安装，数据保存在同目录")
    else:
        print("\n✓ EXE 文件位置: dist/TodoApp.exe")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n已取消构建")
    except Exception as e:
        print(f"\n✗ 发生错误: {e}")
        import traceback
        traceback.print_exc()
