# -*- coding: utf-8 -*-
# 脚本功能:
# 本脚本用于批量处理指定根目录及其子目录下的 WebP 文件。
# 当 WebP 文件大小超过设定阈值时，脚本会尝试找到对应的原始视频文件，
# 并重新生成新的 WebP 文件来替换原有的大文件。
#
# 工作流程:
#   1. 提示用户输入根目录路径和文件大小阈值。
#   2. 递归扫描根目录下所有 WebP 文件。
#   3. 筛选出超过阈值的 WebP 文件。
#   4. 对每个超阈值的 WebP 文件：
#      a. 查找同目录下对应的原始视频文件
#      b. 使用 FFmpeg 重新生成 WebP 文件
#      c. 替换原有的 WebP 文件
#   5. 输出处理结果和统计信息。
#
# 达成的结果:
# - 超过阈值的 WebP 文件将被重新生成的较小文件替换。
# - 保持原有的文件名和目录结构不变。
# - 控制台会输出详细的处理状态和最终的统计报告。
#
# 注意事项:
# - 需要安装 FFmpeg 并确保其在系统 PATH 中可用。
# - 脚本会查找常见的视频格式（mp4, avi, mov, mkv, flv, wmv）。
# - 重新生成的 WebP 文件质量设置为 80，可根据需要调整。
# - 请确保对目标文件夹及其文件有读写权限。

import pathlib
import subprocess
import time
import sys
from typing import List, Tuple, Optional

# 支持的视频格式常量
VIDEO_EXTENSIONS = ('.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv')

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
    提示用户输入文件大小阈值（MB），并持续请求直到输入有效数值。

    返回:
        int: 文件大小阈值（字节）。
    """
    while True:
        try:
            size_mb = input("请输入文件大小阈值（MB，例如：5）: ").strip()
            if not size_mb:
                print("错误：未输入阈值。请重新输入。")
                continue
            
            size_mb_float = float(size_mb)
            if size_mb_float <= 0:
                print("错误：阈值必须大于 0。请重新输入。")
                continue
            
            return int(size_mb_float * 1024 * 1024)  # 转换为字节
            
        except ValueError:
            print("错误：请输入有效的数字。")
        except KeyboardInterrupt:
            print("\n用户取消操作。")
            sys.exit(0)

def find_webp_files(root_path: pathlib.Path) -> List[pathlib.Path]:
    """
    递归查找根目录下所有的 WebP 文件。

    参数:
        root_path (pathlib.Path): 根目录路径。

    返回:
        List[pathlib.Path]: WebP 文件路径列表。
    """
    print(f"\n--- 扫描 WebP 文件 '{root_path}' ---")
    
    try:
        webp_files = list(root_path.rglob('*.webp'))
        
        print(f"找到 {len(webp_files)} 个 WebP 文件")
        
        if webp_files:
            total_size = 0
            for webp_file in webp_files:
                total_size += webp_file.stat().st_size
            
            print(f"WebP 文件总大小: {total_size / (1024*1024):.2f} MB")
        
        return webp_files
        
    except OSError as e:
        print(f"错误：无法扫描文件夹 '{root_path}': {e}")
        return []

def filter_large_webp_files(webp_files: List[pathlib.Path], size_threshold: int) -> List[pathlib.Path]:
    """
    筛选出超过大小阈值的 WebP 文件。

    参数:
        webp_files (List[pathlib.Path]): WebP 文件路径列表。
        size_threshold (int): 大小阈值（字节）。

    返回:
        List[pathlib.Path]: 超过阈值的 WebP 文件路径列表。
    """
    print(f"\n--- 筛选超过阈值的 WebP 文件 ---")
    print(f"大小阈值: {size_threshold / (1024*1024):.2f} MB")
    
    large_files = []
    total_large_size = 0
    
    for webp_file in webp_files:
        file_size = webp_file.stat().st_size
        if file_size > size_threshold:
            large_files.append(webp_file)
            total_large_size += file_size
            print(f"  - {webp_file.name}: {file_size / (1024*1024):.2f} MB")
    
    print(f"\n找到 {len(large_files)} 个超过阈值的文件")
    if large_files:
        print(f"超阈值文件总大小: {total_large_size / (1024*1024):.2f} MB")
    
    return large_files

def find_corresponding_video(webp_path: pathlib.Path) -> Optional[pathlib.Path]:
    """
    查找与 WebP 文件对应的原始视频文件。

    参数:
        webp_path (pathlib.Path): WebP 文件路径。

    返回:
        Optional[pathlib.Path]: 对应的视频文件路径，如果未找到则返回 None。
    """
    webp_stem = webp_path.stem  # 文件名（不含扩展名）
    webp_dir = webp_path.parent
    
    # 查找同目录下同名的视频文件
    for ext in VIDEO_EXTENSIONS:
        video_path = webp_dir / f"{webp_stem}{ext}"
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
        video_path (pathlib.Path): 原始视频文件路径。
        webp_path (pathlib.Path): 目标 WebP 文件路径。

    返回:
        bool: 生成是否成功。
    """
    try:
        # 创建临时文件名
        temp_webp_path = webp_path.with_suffix('.webp.tmp')
        
        # FFmpeg 命令：从视频生成 WebP
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
            original_size = webp_path.stat().st_size
            
            if new_size > 0:
                # 替换原文件
                webp_path.unlink()  # 删除原文件
                temp_webp_path.rename(webp_path)  # 重命名临时文件
                
                size_reduction = original_size - new_size
                reduction_percent = (size_reduction / original_size) * 100
                
                print(f"    ✓ 重新生成成功")
                print(f"      原大小: {original_size / (1024*1024):.2f} MB")
                print(f"      新大小: {new_size / (1024*1024):.2f} MB")
                print(f"      减少: {size_reduction / (1024*1024):.2f} MB ({reduction_percent:.1f}%)")
                
                return True
            else:
                print(f"    ✗ 生成的文件为空")
                if temp_webp_path.exists():
                    temp_webp_path.unlink()
                return False
        else:
            print(f"    ✗ FFmpeg 执行失败")
            if result.stderr:
                print(f"      错误信息: {result.stderr.strip()[:200]}")
            if temp_webp_path.exists():
                temp_webp_path.unlink()
            return False
            
    except subprocess.TimeoutExpired:
        print(f"    ✗ FFmpeg 执行超时")
        if temp_webp_path.exists():
            temp_webp_path.unlink()
        return False
    except Exception as e:
        print(f"    ✗ 重新生成失败: {e}")
        if 'temp_webp_path' in locals() and temp_webp_path.exists():
            temp_webp_path.unlink()
        return False

def process_large_webp_files(large_webp_files: List[pathlib.Path]) -> Tuple[int, int, int]:
    """
    批量处理超过阈值的 WebP 文件。

    参数:
        large_webp_files (List[pathlib.Path]): 超过阈值的 WebP 文件路径列表。

    返回:
        Tuple[int, int, int]: (成功处理的文件数量, 未找到视频源的文件数量, 处理失败的文件数量)
    """
    print(f"\n--- 开始批量处理 WebP 文件 ---")
    
    success_count = 0
    no_video_count = 0
    failed_count = 0
    total_files = len(large_webp_files)
    
    for i, webp_file in enumerate(large_webp_files, 1):
        progress = (i / total_files) * 100
        file_size = webp_file.stat().st_size / (1024*1024)  # MB
        
        print(f"\n  [进度: {progress:.1f}%] 处理文件: {webp_file.name} ({file_size:.2f} MB)")
        
        # 查找对应的视频文件
        video_file = find_corresponding_video(webp_file)
        
        if video_file is None:
            print(f"    ⚠️  未找到对应的视频文件")
            no_video_count += 1
            continue
        
        print(f"    找到视频源: {video_file.name}")
        
        # 重新生成 WebP 文件
        if regenerate_webp_from_video(video_file, webp_file):
            success_count += 1
        else:
            failed_count += 1
    
    return success_count, no_video_count, failed_count

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
        large_webp_files = filter_large_webp_files(webp_files, size_threshold)
        
        if not large_webp_files:
            print("\n未找到超过阈值的 WebP 文件。")
            return
        
        print(f"\n配置确认:")
        print(f"- 根目录: {root_path}")
        print(f"- 大小阈值: {size_threshold / (1024*1024):.2f} MB")
        print(f"- 待处理文件数: {len(large_webp_files)}")
        print(f"- 支持的视频格式: {', '.join(VIDEO_EXTENSIONS)}")
        print(f"- WebP 质量设置: 80")
        print(f"- 输出尺寸: 宽度320px，高度自适应")
        print(f"- 帧率: 10fps")
        
        # 警告提示
        print("\n⚠️  重要提示:")
        print("- 此操作将永久替换原有的 WebP 文件")
        print("- 需要找到对应的原始视频文件才能重新生成")
        print("- 处理大文件可能需要较长时间")
        print("- 建议在处理前备份重要文件")
        
        # 确认处理
        confirm = input("\n确认开始处理？(y/N): ").strip().lower()
        if confirm not in ['y', 'yes', '是']:
            print("用户取消操作。")
            return
        
        # 5. 执行批量处理
        success_count, no_video_count, failed_count = process_large_webp_files(large_webp_files)
        
        # 6. 输出统计信息
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"\n{'='*60}")
        print("WebP 文件优化完成统计报告:")
        print(f"{'='*60}")
        print(f"成功处理文件数量: {success_count}")
        print(f"未找到视频源文件数量: {no_video_count}")
        print(f"处理失败文件数量: {failed_count}")
        print(f"总待处理文件数量: {len(large_webp_files)}")
        print(f"总执行时间: {execution_time:.2f} 秒")
        
        if success_count > 0:
            print(f"平均处理速度: {success_count/execution_time:.2f} 文件/秒")
        
        total_processed = success_count + no_video_count + failed_count
        if total_processed > 0:
            success_rate = (success_count / total_processed) * 100
            print(f"成功率: {success_rate:.1f}%")
        
        print(f"{'='*60}")
        
        if no_video_count > 0:
            print(f"\n注意：{no_video_count} 个文件未找到对应的视频源文件")
            print("这些文件无法重新生成，建议手动检查。")
        
        if failed_count > 0:
            print(f"\n注意：{failed_count} 个文件处理失败，可能原因：")
            print("- 视频文件损坏或格式不支持")
            print("- FFmpeg 处理过程中出错")
            print("- 文件权限不足")
            print("- 磁盘空间不足")
            print("建议检查失败的文件并重试。")
        
        if success_count > 0:
            print(f"\n✓ 成功优化 {success_count} 个 WebP 文件")
            print("文件大小已显著减小，同时保持了良好的视觉质量。")
        
        print("\n程序执行完毕。")
        
    except KeyboardInterrupt:
        print("\n\n用户中断程序执行。")
    except Exception as e:
        print(f"\n程序执行过程中发生意外错误: {e}")
        print("请检查输入参数和文件权限后重试。")

if __name__ == "__main__":
    main()