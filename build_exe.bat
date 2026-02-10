@echo off
chcp 65001 >nul
echo ========================================
echo   Todo App v1.0.0 - 单文件 EXE 构建器
echo ========================================
echo.

echo 正在运行打包脚本...
echo.

python build_exe.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo   ✓ 构建成功!
    echo ========================================
    echo.
    echo 📦 发布文件位于: release\
    echo    - TodoApp.exe
    echo    - TodoApp_v1.0.0_Portable_Windows.zip
    echo.
) else (
    echo.
    echo ========================================
    echo   ✗ 构建失败
    echo ========================================
    echo.
    echo 请检查错误信息
    echo.
)

pause
