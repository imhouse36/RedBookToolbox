# 小红书工具箱 (RedBookToolbox)

一个包含多种实用工具的Python项目，专为小红书内容创作者设计，提供文件处理、图片转换、批量操作等功能。

## 项目简介

本工具箱包含多个独立的Python脚本，每个脚本都针对特定的文件处理需求而设计。所有脚本都经过Claude4优化，具有更好的错误处理、用户体验和代码质量。

## 功能模块

### 1. 文件夹管理工具
- **Claude/Build_folder.py** - 批量创建编号文件夹，在指定目录下创建用户指定数量的编号子文件夹
- **Claude/Auto_build_and_copy.py** - 自动创建编号文件夹并从素材库随机复制图片到各个文件夹
- **Claude/Copy_files.py** - 智能文件复制工具，将素材文件夹的图片随机分配到发布文件夹的各个子目录

### 2. 文件重命名工具
- **Claude/Rename_files.py** - 递归批量重命名文件，按"文件夹名_编号.扩展名"格式重命名所有文件

### 3. 图片与视频处理工具
- **Claude/Webp_video_to_img.py** - 视频转WebP动图，批量将视频文件转换为WebP动画格式
- **Gemini/Webp_video_to_img_Gemini2.5pro.py** - 视频转WebP动图（Gemini优化版）
- **Claude/Webp_resize.py** - WebP文件重新生成工具，从原始视频重新生成超过阈值的WebP文件
- **Gemini/Webp_resize_Gemini2.5pro.py** - WebP文件重新生成工具（Gemini优化版）

### 4. 文件处理工具
- **Claude/Unzip.py** - 批量解压缩工具，自动解压指定文件夹内的所有ZIP压缩文件
- **Claude/Md5_renew.py** - MD5值修改工具，通过在图片文件末尾添加随机字节改变MD5值
- **Claude/Excel_renew.py** - Excel文件批量处理工具，清空Excel文件的K2单元格和第一个工作表的C列内容

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

### 方式一：Web界面（推荐）

1. **启动Web服务器**：
   - 双击运行 `start_server.bat` 文件
   - 或在命令行中运行：`python environment/server.py`

2. **打开Web界面**：
   - 在浏览器中访问：`http://localhost:8000`
   - 选择需要使用的工具
   - 填写相应参数后点击执行
   - 实时查看执行进度和结果

### 方式二：命令行执行

每个脚本都是独立运行的，直接执行即可：

```bash
# 执行Claude优化版本的脚本
python Claude/Build_folder.py

# 或执行Gemini优化版本的脚本（如果有的话）
python Gemini/Webp_video_to_img_Gemini2.5pro.py
```

所有脚本都会提示用户输入必要的参数（如文件夹路径、处理选项等），无需修改代码。

## 功能特性

### Web界面特性
- 🌐 现代化的Web用户界面
- 📱 响应式设计，支持各种屏幕尺寸
- ⚡ 实时显示脚本执行进度
- 🎯 直观的参数输入和验证
- 📊 详细的执行结果展示
- 🔄 支持同时管理多个工具
- 💻 无需命令行操作，降低使用门槛

### 脚本优化特性
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

## 技术说明

### Web界面技术栈
- **前端**：HTML5 + CSS3 + JavaScript (原生)
- **后端**：Python HTTP服务器
- **通信**：RESTful API + 流式数据传输
- **兼容性**：支持所有现代浏览器
- **架构**：前后端分离，模块化设计

### 文件结构
```
小红书工具箱/
├── Claude/                    # Claude优化版本工具脚本
│   ├── Auto_build_and_copy.py    # 自动创建并复制工具
│   ├── Build_folder.py           # 批量创建文件夹工具
│   ├── Copy_files.py             # 智能文件复制工具
│   ├── Excel_renew.py            # Excel文件处理工具
│   ├── Md5_renew.py              # MD5值修改工具
│   ├── Rename_files.py           # 批量重命名工具
│   ├── Unzip.py                  # 批量解压缩工具
│   ├── Webp_resize.py            # WebP重新生成工具
│   └── Webp_video_to_img.py      # 视频转WebP工具
├── Gemini/                   # Gemini优化版本工具脚本
│   ├── Webp_resize_Gemini2.5pro.py      # WebP重新生成工具(Gemini版)
│   └── Webp_video_to_img_Gemini2.5pro.py # 视频转WebP工具(Gemini版)
├── environment/              # Web环境文件夹
│   ├── server.py                 # Web服务器后端
│   ├── script.js                 # 前端JavaScript逻辑
│   └── styles.css                # 前端CSS样式
├── index.html            # Web界面主页
├── start_server.bat      # 一键启动脚本
└── README.md             # 项目说明文档
```

## 注意事项

### Web界面使用注意事项
1. **服务器启动**：使用Web界面前需要先启动后端服务器
2. **浏览器兼容**：建议使用Chrome、Firefox、Edge等现代浏览器
3. **网络访问**：服务器默认运行在localhost:8000，仅本机访问
4. **实时输出**：支持实时查看脚本执行进度，无需等待完成
5. **参数验证**：Web界面会自动验证输入参数的有效性

### 通用注意事项
1. **数据备份**：所有涉及文件修改的操作都建议先备份原始数据
2. **权限要求**：确保对目标文件夹有读写权限
3. **路径输入**：支持拖拽文件夹到命令行窗口获取路径
4. **中断操作**：可随时使用Ctrl+C安全退出程序

## 版本对比

项目中包含了标准版本和Gemini2.5pro优化版本的部分工具，用户可以根据需要选择：

- **标准版本**：功能完整，用户体验好，错误处理完善，适合日常使用
- **Gemini版本**：代码结构优化，处理效率更高，适合大批量文件处理

## 贡献

欢迎提交Issue和Pull Request来改进这个工具箱。

## 许可证

MIT License

---

**开发者**: Claude4 AI Assistant  
**项目类型**: Python工具集  
**适用场景**: 小红书内容创作、文件批量处理、图片视频转换