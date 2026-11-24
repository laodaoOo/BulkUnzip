# 第三方组件

BulkUnzip 自身以 GPL-3.0-only 发布（见 `LICENSE`），运行时还包含以下第三方组件。

## PySide6 / Qt

- 用途：图形界面。
- 许可：LGPL-3.0（Qt 6 / PySide6 的默认开源许可）。
- 原文：`licenses/LGPL-3.0.txt`。
- 项目主页：https://www.qt.io/qt-for-python 、https://www.qt.io/licensing

发布的可执行文件由 PyInstaller 打包 PySide6 生成；如需替换或重新链接 Qt 库，可在源码环境用相同版本的 PySide6 重新构建。

## 归档工具（不随程序分发）

- **7-Zip**（`7z.exe`）：解压 zip / 7z。LGPL / BSD 混合许可，由使用者自行安装。
- **WinRAR**（`Rar.exe`）：解压 rar。商业软件，由使用者自行安装并遵守其许可。

程序只调用系统中已安装的上述命令行工具，不包含它们的二进制文件。
