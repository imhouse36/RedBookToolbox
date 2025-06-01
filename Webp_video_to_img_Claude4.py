# -*- coding: utf-8 -*-
# 脚本功能:
# 本脚本用于将指定根目录及其子目录下的视频文件批量转换为动画 WebP 格式。
# 支持多种视频格式，并提供三种文件覆盖模式供用户选择。
# 转换后的 WebP 文件将保存在与原视频文件相同的目录中。
#
# 工作流程:
#   1. 提示用户输入根目录路径和覆盖模式。
#   2. 递归扫描根目录下所有支持的视频文件。
#   3. 根据用户选择的覆盖模式筛选需要处理的文件。
#   4. 对每个视频文件：
#      a. 使用 FFmpeg 转换为 WebP 格式
#      b. 设置适当的质量和尺寸参数
#      c. 保存到相同目录
#   5. 输出处理结果和统计信息。
#
# 达成的结果:
# - 视频文件将被转换为高质量的动画 WebP 文件。
# - 保持原有的目录结构不变。
# - 根据覆盖模式处理已存在的 WebP 文件。
# - 控制台会输出详细的处理状态和最终的统计报告。
#
# 注意事项:
# - 需要安装 FFmpeg 并确保其在系统 PATH 中可用。
# - 支持的视频格式：mp4, avi, mov, mkv, flv, wmv, m4v, 3gp, webm。
# - 转换质量设置为 80，输出尺寸为宽度 320px，可根据需要调整。
# - 请确保对目标文件夹及其文件有读写权限。

import pathlib
import subprocess
import time
import sys
from typing import List, Tuple, Dict

# 支持的视频格式常量
VIDEO_EXTENSIONS = ('.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.m4v', '.3gp', '.webm')

# 覆盖模式常量
OVERWRITE_MODES = {
    '1': 'skip',      # 跳过已存在的文件
    '2': 'overwrite', # 覆盖已存在的文件
    '3': 'ask'        # 每次询问用户
}

def get_valid_folder_path_from_user(prompt_message: str) -> pathlib.Path:
    """
    提示用户输入一个文件夹路径，并持续请求直到输入一个已存在的有效文件夹路径。

    参数:
        prompt_message (str): 显示给用户的提示信息。

    返回:
        pathlib.Path: 用户输入的有效文件夹路径对象。
    """
    while True:
        try:
            folder_path_str = input(prompt_message).strip()
            if not folder_path_str:
                print("错误：未输入路径。请重新输入。")
                continue
            
            folder_path = pathlib.Path(folder_path_str)
            
            if folder_path.exists() and folder_path.is_dir():
                return folder_path
            else:
                print(f"错误：路径 '{folder_path}' 不存在或不是一个文件夹。请重新输入。")
        except KeyboardInterrupt:
            print("\n用户取消操作。")
            sys.exit(0)

def get_overwrite_mode_from_user() -> str:
    """
    提示用户选择文件覆盖模式。

    返回:
        str: 覆盖模式（'skip', 'overwrite', 'ask'）。
    """
    print("\n请选择文件覆盖模式:")
    print("1. 跳过已存在的 WebP 文件")
    print("2. 覆盖已存在的 WebP 文件")
    print("3. 每次询问是否覆盖")
    
    while True:
        try:
            choice = input("请输入选择 (1-3): ").strip()
            if choice in OVERWRITE_MODES:
                mode = OVERWRITE_MODES[choice]
                print(f"已选择: {choice} - {get_mode_description(mode)}")
                return mode
            else:
                print("错误：请输入 1、2 或 3。")
        except KeyboardInterrupt:
            print("\n用户取消操作。")
            sys.exit(0)

def get_mode_description(mode: str) -> str:
    """
    获取覆盖模式的描述。

    参数:
        mode (str): 覆盖模式。

    返回:
        str: 模式描述。
    """
    descriptions = {
        'skip': '跳过已存在的文件',
        'overwrite': '覆盖已存在的文件',
        'ask': '每次询问是否覆盖'
    }
    return descriptions.get(mode, '未知模式')

def find_video_files(root_path: pathlib.Path) -> List[pathlib.Path]:
    """
    递归查找根目录下所有支持的视频文件。

    参数:
        root_path (pathlib.Path): 根目录路径。

    返回:
        List[pathlib.Path]: 视频文件路径列表。
    """
    print(f"\n--- 扫描视频文件 '{root_path}' ---")
    
    try:
        video_files = []
        format_count = {}
        total_size = 0
        
        for ext in VIDEO_EXTENSIONS:
            files = list(root_path.rglob(f'*{ext}'))
            video_files.extend(files)
            
            if files:
                format_count[ext] = len(files)
                for f in files:
                    total_size += f.stat().st_size
        
        print(f"找到 {len(video_files)} 个视频文件")
        
        if video_files:
            print("视频格式统计:")
            for ext, count in sorted(format_count.items()):
                print(f"  {ext}: {count} 个")
            
            print(f"视频文件总大小: {total_size / (1024*1024):.2f} MB")
        
        return video_files
        
    except OSError as e:
        print(f"错误：无法扫描文件夹 '{root_path}': {e}")
        return []

def filter_videos_by_overwrite_mode(video_files: List[pathlib.Path], overwrite_mode: str) -> List[pathlib.Path]:
    """
    根据覆盖模式筛选需要处理的视频文件。

    参数:
        video_files (List[pathlib.Path]): 视频文件路径列表。
        overwrite_mode (str): 覆盖模式。

    返回:
        List[pathlib.Path]: 需要处理的视频文件路径列表。
    """
    if overwrite_mode == 'overwrite':
        return video_files
    
    filtered_files = []
    existing_webp_count = 0
    
    for video_file in video_files:
        webp_path = video_file.with_suffix('.webp')
        
        if webp_path.exists():
            existing_webp_count += 1
            if overwrite_mode == 'skip':
                continue
            # 对于 'ask' 模式，在处理时再询问
        
        filtered_files.append(video_file)
    
    if existing_webp_count > 0:
        print(f"\n发现 {existing_webp_count} 个已存在的 WebP 文件")
        if overwrite_mode == 'skip':
            print(f"根据设置，将跳过这些文件")
        elif overwrite_mode == 'ask':
            print(f"根据设置，将逐个询问是否覆盖")
    
    print(f"待处理视频文件数量: {len(filtered_files)}")
    
    return filtered_files

def check_ffmpeg_availability() -> bool:
    """
    检查 FFmpeg 是否可用。

    返回:
        bool: FFmpeg 是否可用。
    """
    try:
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        return False

def convert_video_to_webp(video_path: pathlib.Path, webp_path: pathlib.Path) -> bool:
    """
    使用 FFmpeg 将视频文件转换为 WebP 格式。

    参数:
        video_path (pathlib.Path): 视频文件路径。
        webp_path (pathlib.Path): 目标 WebP 文件路径。

    返回:
        bool: 转换是否成功。
    """
    try:
        # 创建临时文件名
        temp_webp_path = webp_path.with_suffix('.webp.tmp')
        
        # FFmpeg 命令：视频转 WebP
        cmd = [
            'ffmpeg',
            '-i', str(video_path),
            '-vf', 'fps=10,scale=320:-1:flags=lanczos',  # 10fps, 宽度320px
            '-c:v', 'libwebp',
            '-quality', '80',
            '-preset', 'default',
            '-loop', '0',
            '-y',  # 覆盖输出文件
            str(temp_webp_path)
        ]
        
        # 执行 FFmpeg 命令
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5分钟超时
        )
        
        if result.returncode == 0 and temp_webp_path.exists():
            # 检查生成的文件大小
            new_size = temp_webp_path.stat().st_size
            original_size = video_path.stat().st_size
            
            if new_size > 0:
                # 移动临时文件到最终位置
                if webp_path.exists():
                    webp_path.unlink()  # 删除已存在的文件
                temp_webp_path.rename(webp_path)
                
                size_ratio = (new_size / original_size) * 100
                
                print(f"    ✓ 转换成功")
                print(f"      原视频: {original_size / (1024*1024):.2f} MB")
                print(f"      WebP: {new_size / (1024*1024):.2f} MB")
                print(f"      压缩比: {size_ratio:.1f}%")
                
                return True
            else:
                print(f"    ✗ 生成的文件为空")
                if temp_webp_path.exists():
                    temp_webp_path.unlink()
                return False
        else:
            print(f"    ✗ FFmpeg 执行失败")
            if result.stderr:
                error_msg = result.stderr.strip()[:200]
                print(f"      错误信息: {error_msg}")
            if temp_webp_path.exists():
                temp_webp_path.unlink()
            return False
            
    except subprocess.TimeoutExpired:
        print(f"    ✗ FFmpeg 执行超时")
        if 'temp_webp_path' in locals() and temp_webp_path.exists():
            temp_webp_path.unlink()
        return False
    except Exception as e:
        print(f"    ✗ 转换失败: {e}")
        if 'temp_webp_path' in locals() and temp_webp_path.exists():
            temp_webp_path.unlink()
        return False

def should_process_file(video_path: pathlib.Path, webp_path: pathlib.Path, overwrite_mode: str) -> bool:
    """
    根据覆盖模式判断是否应该处理文件。

    参数:
        video_path (pathlib.Path): 视频文件路径。
        webp_path (pathlib.Path): WebP 文件路径。
        overwrite_mode (str): 覆盖模式。

    返回:
        bool: 是否应该处理文件。
    """
    if not webp_path.exists():
        return True
    
    if overwrite_mode == 'overwrite':
        return True
    elif overwrite_mode == 'skip':
        print(f"    跳过（WebP 文件已存在）")
        return False
    elif overwrite_mode == 'ask':
        while True:
            try:
                choice = input(f"    WebP 文件已存在，是否覆盖？(y/N): ").strip().lower()
                if choice in ['y', 'yes', '是']:
                    return True
                elif choice in ['n', 'no', '否', '']:
                    print(f"    跳过文件")
                    return False
                else:
                    print("    请输入 y 或 n")
            except KeyboardInterrupt:
                print("\n用户取消操作。")
                return False
    
    return False

def process_video_files(video_files: List[pathlib.Path], overwrite_mode: str) -> Dict[str, int]:
    """
    批量处理视频文件，转换为 WebP 格式。

    参数:
        video_files (List[pathlib.Path]): 视频文件路径列表。
        overwrite_mode (str): 覆盖模式。

    返回:
        Dict[str, int]: 包含统计信息的字典。
    """
    print(f"\n--- 开始批量转换视频为 WebP ---")
    
    success_count = 0
    skipped_count = 0
    failed_count = 0
    total_files = len(video_files)
    
    for i, video_file in enumerate(video_files, 1):
        progress = (i / total_files) * 100
        file_size = video_file.stat().st_size / (1024*1024)  # MB
        
        print(f"\n  [进度: {progress:.1f}%] 处理文件: {video_file.name} ({file_size:.2f} MB)")
        
        # 确定输出 WebP 文件路径
        webp_path = video_file.with_suffix('.webp')
        
        # 检查是否应该处理此文件
        if not should_process_file(video_file, webp_path, overwrite_mode):
            skipped_count += 1
            continue
        
        # 转换视频为 WebP
        if convert_video_to_webp(video_file, webp_path):
            success_count += 1
        else:
            failed_count += 1
    
    return {
        'success_count': success_count,
        'skipped_count': skipped_count,
        'failed_count': failed_count,
        'total_files': total_files
    }

def main():
    """
    主函数：控制程序的执行流程。
    """
    print("视频转 WebP 批量转换工具")
    print("功能：将视频文件批量转换为动画 WebP 格式")
    print("=" * 50)
    
    # 记录脚本开始时间
    start_time = time.time()
    
    try:
        # 检查 FFmpeg 可用性
        print("检查 FFmpeg 可用性...")
        if not check_ffmpeg_availability():
            print("错误：未找到 FFmpeg 或 FFmpeg 不可用。")
            print("请确保已安装 FFmpeg 并将其添加到系统 PATH 中。")
            print("下载地址：https://ffmpeg.org/download.html")
            return
        print("✓ FFmpeg 可用")
        
        # 1. 获取用户输入：根目录路径
        root_path = get_valid_folder_path_from_user(
            "请输入要处理的根目录路径: "
        )
        
        # 2. 获取用户输入：覆盖模式
        overwrite_mode = get_overwrite_mode_from_user()
        
        # 3. 查找所有视频文件
        video_files = find_video_files(root_path)
        
        if not video_files:
            print("\n未找到任何支持的视频文件。")
            print(f"支持的格式: {', '.join(VIDEO_EXTENSIONS)}")
            return
        
        # 4. 根据覆盖模式筛选文件
        filtered_video_files = filter_videos_by_overwrite_mode(video_files, overwrite_mode)
        
        if not filtered_video_files:
            print("\n没有需要处理的视频文件。")
            return
        
        print(f"\n配置确认:")
        print(f"- 根目录: {root_path}")
        print(f"- 覆盖模式: {get_mode_description(overwrite_mode)}")
        print(f"- 待处理文件数: {len(filtered_video_files)}")
        print(f"- 支持的视频格式: {', '.join(VIDEO_EXTENSIONS)}")
        print(f"- WebP 质量设置: 80")
        print(f"- 输出尺寸: 宽度320px，高度自适应")
        print(f"- 帧率: 10fps")
        
        # 警告提示
        print("\n⚠️  重要提示:")
        print("- 转换过程可能需要较长时间，请耐心等待")
        print("- 生成的 WebP 文件将保存在与原视频相同的目录中")
        print("- 转换质量设置为高质量，文件大小适中")
        if overwrite_mode == 'overwrite':
            print("- 已存在的 WebP 文件将被覆盖")
        
        # 确认处理
        confirm = input("\n确认开始处理？(y/N): ").strip().lower()
        if confirm not in ['y', 'yes', '是']:
            print("用户取消操作。")
            return
        
        # 5. 执行批量处理
        stats = process_video_files(filtered_video_files, overwrite_mode)
        
        # 6. 输出统计信息
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"\n{'='*60}")
        print("视频转 WebP 完成统计报告:")
        print(f"{'='*60}")
        print(f"成功转换文件数量: {stats['success_count']}")
        print(f"跳过的文件数量: {stats['skipped_count']}")
        print(f"转换失败文件数量: {stats['failed_count']}")
        print(f"总处理文件数量: {stats['total_files']}")
        print(f"总执行时间: {execution_time:.2f} 秒")
        
        if stats['success_count'] > 0:
            print(f"平均转换速度: {stats['success_count']/execution_time:.2f} 文件/秒")
        
        processed_files = stats['success_count'] + stats['failed_count']
        if processed_files > 0:
            success_rate = (stats['success_count'] / processed_files) * 100
            print(f"转换成功率: {success_rate:.1f}%")
        
        print(f"{'='*60}")
        
        if stats['skipped_count'] > 0:
            print(f"\n信息：跳过了 {stats['skipped_count']} 个文件")
            if overwrite_mode == 'skip':
                print("这些文件对应的 WebP 文件已存在。")
            elif overwrite_mode == 'ask':
                print("这些文件是用户选择跳过的。")
        
        if stats['failed_count'] > 0:
            print(f"\n注意：{stats['failed_count']} 个文件转换失败，可能原因：")
            print("- 视频文件损坏或格式不支持")
            print("- FFmpeg 处理过程中出错")
            print("- 文件权限不足")
            print("- 磁盘空间不足")
            print("建议检查失败的文件并重试。")
        
        if stats['success_count'] > 0:
            print(f"\n✓ 成功转换 {stats['success_count']} 个视频文件为 WebP 格式")
            print("所有生成的 WebP 文件已保存在与原视频相同的目录中。")
            print("WebP 文件具有更小的文件大小和良好的动画效果。")
        
        print("\n程序执行完毕。")
        
    except KeyboardInterrupt:
        print("\n\n用户中断程序执行。")
    except Exception as e:
        print(f"\n程序执行过程中发生意外错误: {e}")
        print("请检查输入参数和文件权限后重试。")

if __name__ == "__main__":
    main()