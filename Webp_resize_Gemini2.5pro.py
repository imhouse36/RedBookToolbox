# -*- coding: utf-8 -*-
# 脚本功能:
# 本脚本用于处理超过设定大小阈值的 WebP 文件。
# 对于超过阈值的 WebP 文件，脚本会尝试查找对应的原始视频文件，
# 并使用 FFmpeg 重新生成新的 WebP 文件来替换原有的大文件。
#
# 工作流程:
#   1. 提示用户输入根目录路径和文件大小阈值。
#   2. 递归扫描根目录下所有 WebP 文件。
#   3. 筛选出超过大小阈值的 WebP 文件。
#   4. 对每个超过阈值的 WebP 文件：
#      a. 查找同目录下同名的视频文件
#      b. 如果找到视频文件，使用 FFmpeg 重新生成 WebP
#      c. 替换原有的大 WebP 文件
#   5. 输出处理结果和统计信息。
#
# 达成的结果:
# - 超过阈值的 WebP 文件将被重新生成的较小文件替换。
# - 保持原有的文件名和目录结构不变。
# - 控制台会输出详细的处理状态和最终的统计报告。
#
# 注意事项:
# - 需要安装 FFmpeg 并确保其在系统 PATH 中可用。
# - 支持的视频格式：mp4, avi, mov, mkv, flv, wmv, m4v, 3gp, webm。
# - 只有当找到对应的视频文件时，才会重新生成 WebP 文件。
# - 请确保对目标文件夹及其文件有读写权限。

import pathlib
import subprocess
import time
import sys
from typing import List, Tuple, Dict, Optional

# 支持的视频格式常量
VIDEO_EXTENSIONS = ('.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.m4v', '.3gp', '.webm')

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

def get_size_threshold_from_user() -> int:
    """
    提示用户输入文件大小阈值（KB）。

    返回:
        int: 文件大小阈值（字节）。
    """
    while True:
        try:
            size_kb = input("请输入 WebP 文件大小阈值（KB，默认 500KB）: ").strip()
            if not size_kb:
                size_kb = "500"
            
            size_kb_int = int(size_kb)
            if size_kb_int <= 0:
                print("错误：阈值必须大于 0。")
                continue
            
            size_bytes = size_kb_int * 1024
            print(f"设置阈值为: {size_kb_int} KB ({size_bytes} 字节)")
            return size_bytes
            
        except ValueError:
            print("错误：请输入有效的数字。")
        except KeyboardInterrupt:
            print("\n用户取消操作。")
            sys.exit(0)

def find_webp_files(root_path: pathlib.Path) -> List[pathlib.Path]:
    """
    递归查找根目录下所有 WebP 文件。

    参数:
        root_path (pathlib.Path): 根目录路径。

    返回:
        List[pathlib.Path]: WebP 文件路径列表。
    """
    print(f"\n--- 扫描 WebP 文件 '{root_path}' ---")
    
    try:
        webp_files = list(root_path.rglob('*.webp'))
        total_size = sum(f.stat().st_size for f in webp_files)
        
        print(f"找到 {len(webp_files)} 个 WebP 文件")
        if webp_files:
            print(f"WebP 文件总大小: {total_size / (1024*1024):.2f} MB")
        
        return webp_files
        
    except OSError as e:
        print(f"错误：无法扫描文件夹 '{root_path}': {e}")
        return []

def filter_large_webp_files(webp_files: List[pathlib.Path], size_threshold: int) -> List[Tuple[pathlib.Path, int]]:
    """
    筛选出超过大小阈值的 WebP 文件。

    参数:
        webp_files (List[pathlib.Path]): WebP 文件路径列表。
        size_threshold (int): 大小阈值（字节）。

    返回:
        List[Tuple[pathlib.Path, int]]: 超过阈值的文件路径和大小的元组列表。
    """
    large_files = []
    total_large_size = 0
    
    for webp_file in webp_files:
        try:
            file_size = webp_file.stat().st_size
            if file_size > size_threshold:
                large_files.append((webp_file, file_size))
                total_large_size += file_size
        except OSError as e:
            print(f"警告：无法获取文件大小 '{webp_file}': {e}")
    
    print(f"\n发现 {len(large_files)} 个超过阈值的 WebP 文件")
    if large_files:
        print(f"超过阈值的文件总大小: {total_large_size / (1024*1024):.2f} MB")
        print(f"平均文件大小: {(total_large_size / len(large_files)) / 1024:.2f} KB")
    
    return large_files

def find_corresponding_video(webp_path: pathlib.Path) -> Optional[pathlib.Path]:
    """
    查找与 WebP 文件对应的视频文件。

    参数:
        webp_path (pathlib.Path): WebP 文件路径。

    返回:
        Optional[pathlib.Path]: 对应的视频文件路径，如果未找到则返回 None。
    """
    # 获取不带扩展名的文件名
    base_name = webp_path.stem
    parent_dir = webp_path.parent
    
    # 在同一目录下查找同名的视频文件
    for ext in VIDEO_EXTENSIONS:
        video_path = parent_dir / f"{base_name}{ext}"
        if video_path.exists():
            return video_path
    
    return None

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

def regenerate_webp_from_video(video_path: pathlib.Path, webp_path: pathlib.Path) -> bool:
    """
    使用 FFmpeg 从视频文件重新生成 WebP 文件。

    参数:
        video_path (pathlib.Path): 视频文件路径。
        webp_path (pathlib.Path): 目标 WebP 文件路径。

    返回:
        bool: 重新生成是否成功。
    """
    try:
        # 创建临时文件名
        temp_webp_path = webp_path.with_suffix('.webp.tmp')
        
        # FFmpeg 命令：视频转 WebP，使用更高的压缩设置
        cmd = [
            'ffmpeg',
            '-i', str(video_path),
            '-vf', 'fps=8,scale=280:-1:flags=lanczos',  # 降低帧率和尺寸
            '-c:v', 'libwebp',
            '-quality', '70',  # 降低质量以减小文件大小
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
            original_size = webp_path.stat().st_size
            
            if new_size > 0 and new_size < original_size:
                # 备份原文件
                backup_path = webp_path.with_suffix('.webp.backup')
                if backup_path.exists():
                    backup_path.unlink()
                webp_path.rename(backup_path)
                
                # 移动新文件到目标位置
                temp_webp_path.rename(webp_path)
                
                # 删除备份文件
                backup_path.unlink()
                
                size_reduction = ((original_size - new_size) / original_size) * 100
                
                print(f"    ✓ 重新生成成功")
                print(f"      原文件: {original_size / 1024:.2f} KB")
                print(f"      新文件: {new_size / 1024:.2f} KB")
                print(f"      减小: {size_reduction:.1f}%")
                
                return True
            else:
                print(f"    ✗ 新文件大小不理想")
                if new_size >= original_size:
                    print(f"      新文件 ({new_size / 1024:.2f} KB) 不小于原文件 ({original_size / 1024:.2f} KB)")
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
        print(f"    ✗ 重新生成失败: {e}")
        if 'temp_webp_path' in locals() and temp_webp_path.exists():
            temp_webp_path.unlink()
        return False

def process_large_webp_files(large_files: List[Tuple[pathlib.Path, int]], size_threshold: int) -> Dict[str, int]:
    """
    处理超过阈值的 WebP 文件。

    参数:
        large_files (List[Tuple[pathlib.Path, int]]): 超过阈值的文件路径和大小的元组列表。
        size_threshold (int): 大小阈值（字节）。

    返回:
        Dict[str, int]: 包含统计信息的字典。
    """
    print(f"\n--- 开始处理超过阈值的 WebP 文件 ---")
    
    success_count = 0
    no_video_count = 0
    failed_count = 0
    total_files = len(large_files)
    total_size_saved = 0
    
    for i, (webp_file, file_size) in enumerate(large_files, 1):
        progress = (i / total_files) * 100
        file_size_kb = file_size / 1024
        
        print(f"\n  [进度: {progress:.1f}%] 处理文件: {webp_file.name} ({file_size_kb:.2f} KB)")
        
        # 查找对应的视频文件
        video_file = find_corresponding_video(webp_file)
        
        if video_file is None:
            print(f"    ⚠ 未找到对应的视频文件")
            no_video_count += 1
            continue
        
        print(f"    找到对应视频: {video_file.name}")
        
        # 记录原始大小
        original_size = file_size
        
        # 重新生成 WebP 文件
        if regenerate_webp_from_video(video_file, webp_file):
            # 计算节省的空间
            new_size = webp_file.stat().st_size
            size_saved = original_size - new_size
            total_size_saved += size_saved
            success_count += 1
        else:
            failed_count += 1
    
    return {
        'success_count': success_count,
        'no_video_count': no_video_count,
        'failed_count': failed_count,
        'total_files': total_files,
        'total_size_saved': total_size_saved
    }

def main():
    """
    主函数：控制程序的执行流程。
    """
    print("WebP 文件大小优化工具")
    print("功能：重新生成超过阈值的 WebP 文件以减小文件大小")
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
        
        # 2. 获取用户输入：文件大小阈值
        size_threshold = get_size_threshold_from_user()
        
        # 3. 查找所有 WebP 文件
        webp_files = find_webp_files(root_path)
        
        if not webp_files:
            print("\n未找到任何 WebP 文件。")
            return
        
        # 4. 筛选超过阈值的文件
        large_files = filter_large_webp_files(webp_files, size_threshold)
        
        if not large_files:
            print(f"\n没有超过 {size_threshold / 1024:.0f} KB 阈值的 WebP 文件。")
            return
        
        print(f"\n配置确认:")
        print(f"- 根目录: {root_path}")
        print(f"- 大小阈值: {size_threshold / 1024:.0f} KB")
        print(f"- 总 WebP 文件数: {len(webp_files)}")
        print(f"- 超过阈值文件数: {len(large_files)}")
        print(f"- 支持的视频格式: {', '.join(VIDEO_EXTENSIONS)}")
        print(f"- 优化设置: 帧率8fps，宽度280px，质量70")
        
        # 警告提示
        print("\n⚠️  重要提示:")
        print("- 只有找到对应视频文件的 WebP 文件才会被重新生成")
        print("- 重新生成过程可能需要较长时间，请耐心等待")
        print("- 原始 WebP 文件将被新生成的文件替换")
        print("- 新文件将使用更高的压缩设置以减小文件大小")
        
        # 确认处理
        confirm = input("\n确认开始处理？(y/N): ").strip().lower()
        if confirm not in ['y', 'yes', '是']:
            print("用户取消操作。")
            return
        
        # 5. 执行批量处理
        stats = process_large_webp_files(large_files, size_threshold)
        
        # 6. 输出统计信息
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"\n{'='*60}")
        print("WebP 文件优化完成统计报告:")
        print(f"{'='*60}")
        print(f"成功优化文件数量: {stats['success_count']}")
        print(f"未找到视频文件数量: {stats['no_video_count']}")
        print(f"优化失败文件数量: {stats['failed_count']}")
        print(f"总处理文件数量: {stats['total_files']}")
        print(f"总执行时间: {execution_time:.2f} 秒")
        
        if stats['success_count'] > 0:
            print(f"平均处理速度: {stats['success_count']/execution_time:.2f} 文件/秒")
            print(f"总节省空间: {stats['total_size_saved'] / (1024*1024):.2f} MB")
            print(f"平均每文件节省: {stats['total_size_saved'] / (1024 * stats['success_count']):.2f} KB")
        
        processed_files = stats['success_count'] + stats['failed_count']
        if processed_files > 0:
            success_rate = (stats['success_count'] / processed_files) * 100
            print(f"优化成功率: {success_rate:.1f}%")
        
        print(f"{'='*60}")
        
        if stats['no_video_count'] > 0:
            print(f"\n信息：{stats['no_video_count']} 个文件未找到对应的视频文件")
            print("这些文件无法重新生成，建议手动检查或使用其他工具优化。")
        
        if stats['failed_count'] > 0:
            print(f"\n注意：{stats['failed_count']} 个文件优化失败，可能原因：")
            print("- 视频文件损坏或格式不支持")
            print("- FFmpeg 处理过程中出错")
            print("- 文件权限不足")
            print("- 磁盘空间不足")
            print("- 新生成的文件大小不理想")
            print("建议检查失败的文件并重试。")
        
        if stats['success_count'] > 0:
            print(f"\n✓ 成功优化 {stats['success_count']} 个 WebP 文件")
            print(f"总共节省了 {stats['total_size_saved'] / (1024*1024):.2f} MB 的存储空间")
            print("优化后的文件具有更小的文件大小，同时保持良好的视觉效果。")
        
        print("\n程序执行完毕。")
        
    except KeyboardInterrupt:
        print("\n\n用户中断程序执行。")
    except Exception as e:
        print(f"\n程序执行过程中发生意外错误: {e}")
        print("请检查输入参数和文件权限后重试。")

if __name__ == "__main__":
    main()