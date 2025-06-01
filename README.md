# 小红书工具箱 (RedBookToolbox)

一个包含多种实用工具的Python项目，专为小红书内容创作者设计，提供文件处理、图片转换、批量操作等功能。

## 项目简介

本工具箱包含多个独立的Python脚本，每个脚本都针对特定的文件处理需求而设计。所有脚本都经过Claude4优化，具有更好的错误处理、用户体验和代码质量。

## 功能模块

### 1. 文件夹管理工具
- **Build_folder_Claude4.py** - 批量创建编号文件夹
- **Auto_build_and_copy_Claude4.py** - 自动创建文件夹并复制素材
- **Copy_files_Claude4.py** - 智能文件复制工具

### 2. 文件重命名工具
- **Rename_files_Claude4.py** - 递归批量重命名文件

### 3. 图片处理工具
- **Webp_video_to_img_Claude4.py** - 视频转WebP动图（Claude4优化版）
- **Webp_video_to_img_Gemini2.5pro.py** - 视频转WebP动图（Gemini版）
- **Webp_resize_Claude4.py** - WebP文件重新生成工具（Claude4优化版）
- **Webp_resize_Gemini2.5pro.py** - WebP文件重新生成工具（Gemini版）

### 4. 文件处理工具
- **Unzip_Claude4.py** - 批量解压缩工具
- **Md5_renew_Claude4.py** - MD5值修改工具
- **Excel_renew_Claude4.py** - Excel文件批量处理工具

## 环境要求

- Python 3.7+
- 依赖库：
  - `openpyxl` (用于Excel处理)
  - `pathlib` (Python 3.4+内置)
  - `FFmpeg` (用于视频处理，需单独安装)

## 安装依赖

```bash
pip install openpyxl
```

对于视频处理功能，还需要安装FFmpeg：
- Windows: 下载FFmpeg并添加到系统PATH
- macOS: `brew install ffmpeg`
- Linux: `sudo apt-get install ffmpeg`

## 使用说明

每个脚本都是独立运行的，直接执行即可：

```bash
python Build_folder_Claude4.py
```

所有脚本都会提示用户输入必要的参数（如文件夹路径、处理选项等），无需修改代码。

## 功能特性

### Claude4优化版本特性
- ✅ 完善的类型提示
- ✅ 增强的错误处理
- ✅ 详细的进度显示
- ✅ 用户友好的交互界面
- ✅ 支持用户中断操作（Ctrl+C）
- ✅ 详细的统计信息和报告
- ✅ Python 3.7兼容性

### 安全特性
- 🔒 操作前确认机制
- 🔒 文件冲突智能处理
- 🔒 详细的操作日志
- 🔒 异常情况优雅处理

## 注意事项

1. **数据备份**：所有涉及文件修改的操作都建议先备份原始数据
2. **权限要求**：确保对目标文件夹有读写权限
3. **路径输入**：支持拖拽文件夹到命令行窗口获取路径
4. **中断操作**：可随时使用Ctrl+C安全退出程序

## 版本对比

项目中包含了Claude4和Gemini2.5pro两个版本的部分工具，用户可以根据需要选择：

- **Claude4版本**：功能更完整，用户体验更好，错误处理更完善
- **Gemini版本**：代码结构相对简单，适合快速批量处理

## 贡献

欢迎提交Issue和Pull Request来改进这个工具箱。

## 许可证

MIT License

---

**开发者**: Claude4 AI Assistant  
**项目类型**: Python工具集  
**适用场景**: 小红书内容创作、文件批量处理、图片视频转换