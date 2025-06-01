#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import subprocess
import pathlib  # 导入 pathlib 模块

# ==============================================================================
# 脚本功能核心备注 (Script Core Functionality Notes)
# ==============================================================================
#
# 脚本名称 (Script Name):
#   Webp_video_to_img.py
#
# 主要目的 (Main Purpose):
#   本脚本用于将指定根目录及其子目录下的视频文件批量转换为动画 WebP 格式。
#
# 工作流程 (Workflow):
#   1. 提示用户输入一个包含视频文件的根目录路径。
#   2. 验证用户输入的路径是否为有效文件夹。
#   3. 检查 FFmpeg 是否已安装并配置在系统路径中，或在脚本中正确指定了路径。
#   4. 询问用户是否要一键替换所有已存在的WebP文件。
#   5. 递归遍历指定根目录及其所有子目录。
#   6. 查找所有符合 `VIDEO_EXTENSIONS` 定义的视频文件。
#   7. 对每个找到的视频文件：
#      a. 检查是否已存在同名WebP文件，根据用户选择决定是否跳过或覆盖。
#      b. 提取视频的前 `CONVERSION_DURATION_SECONDS` 秒内容。
#      c. 使用 FFmpeg 和预设的 `WEBP_CONVERSION_OPTIONS` (可配置) 将这段时间的片段转换为 .webp 文件。
#      d. 生成的 .webp 文件将与原始视频文件同名 (扩展名改为 .webp) 并保存在同一目录下。
#   8. 报告转换成功和失败的文件数量，并显示原始文件和转换后 WebP 文件的大小及比例。
#
# 配置项 (Key Configurations):
#   - `VIDEO_EXTENSIONS`: 定义了脚本会识别和处理的视频文件扩展名。
#   - `FFMPEG_PATH`: FFmpeg 可执行文件的路径。
#   - `WEBP_CONVERSION_OPTIONS`: FFmpeg 用于 WebP 转换的参数。
#   - `CONVERSION_DURATION_SECONDS`: 从视频截取的时长。
#
# 注意事项 (Important Notes):
#   - 依赖 FFmpeg：确保 FFmpeg 已正确安装。
#   - 文件覆盖：用户可选择是否覆盖已存在的 .webp 文件。
#   - 错误处理：脚本包含对 FFmpeg 执行错误和超时的基本处理。
#   - 输出文件：生成的 WebP 文件通常不包含音频，并且默认是无限循环的动画。
#
# ==============================================================================


# --- 配置 ---
VIDEO_EXTENSIONS = ('.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mpeg', '.mpg')
FFMPEG_PATH = "ffmpeg"  # 如果不在PATH中，请指定完整路径
CONVERSION_DURATION_SECONDS = "3"  # 从视频截取的时长（秒）
FFMPEG_TIMEOUT_SECONDS = 120  # FFmpeg 执行超时时间

# WebP转换参数 (与原文保持一致的压缩效率)
WEBP_CONVERSION_OPTIONS = [
    "-c:v", "libwebp",
    "-lossless", "0",
    "-q:v", "75",
    "-loop", "0",
    "-an",
    # "-vf", "fps=10", # 示例：如果需要固定帧率，可以取消注释或修改
]


# --- /配置 ---

def get_human_readable_size(size_bytes: int) -> str:
    """将字节大小转换为人类可读的格式 (KB, MB, GB)"""
    if size_bytes == 0:
        return "0 B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = 0
    size_bytes_float = float(size_bytes)  # 确保进行浮点数除法
    while size_bytes_float >= 1024 and i < len(size_name) - 1:
        size_bytes_float /= 1024.0
        i += 1
    return f"{size_bytes_float:.2f} {size_name[i]}"


def get_valid_folder_path_from_user() -> pathlib.Path:
    """提示用户输入一个文件夹路径，并验证其有效性。"""
    while True:
        folder_path_str = input("请输入要处理的视频文件所在的根目录路径: ").strip()
        if folder_path_str.startswith('"') and folder_path_str.endswith('"'):
            folder_path_str = folder_path_str[1:-1]
        elif folder_path_str.startswith("'") and folder_path_str.endswith("'"):
            folder_path_str = folder_path_str[1:-1]

        folder_path_obj = pathlib.Path(folder_path_str)
        if folder_path_obj.is_dir():
            return folder_path_obj
        else:
            print(f"错误：路径 '{folder_path_str}' 不是一个有效的文件夹，或文件夹不存在。请重新输入。")


def check_ffmpeg_availability(ffmpeg_exe_path: str) -> bool:
    """检查FFmpeg是否可用"""
    try:
        # 使用 subprocess.run 替代 Popen 进行简单的版本检查
        result = subprocess.run([ffmpeg_exe_path, "-version"], capture_output=True, check=True, text=True,
                                encoding='utf-8', errors='replace')
        print(f"FFmpeg 在 '{ffmpeg_exe_path}' 找到并可用。\n")
        # print(result.stdout[:100]) # 可选：打印部分版本信息
        return True
    except FileNotFoundError:
        print(f"错误: FFmpeg 可执行文件在 '{ffmpeg_exe_path}' 未找到。")
        print("请确保FFmpeg已安装并添加到系统PATH，或者在脚本中正确配置 FFMPEG_PATH。")
        return False
    except subprocess.CalledProcessError as e:
        print(f"错误: 执行 FFmpeg -version 时出错 (返回码: {e.returncode}):")
        print(f"  Stdout: {e.stdout}")
        print(f"  Stderr: {e.stderr}")
        print("FFmpeg 可能安装不正确。")
        return False
    except Exception as e_gen:  # 捕获其他可能的异常，如编码问题
        print(f"检查FFmpeg可用性时发生意外错误: {e_gen}")
        return False


def get_overwrite_preference() -> str:
    """询问用户对已存在WebP文件的处理偏好"""
    print("\n检测到可能存在已转换的WebP文件。")
    print("请选择处理方式：")
    print("1. 跳过已存在的WebP文件 (s)")
    print("2. 一键全部替换覆盖所有WebP文件 (r)")
    print("3. 逐个询问是否覆盖 (a)")
    
    while True:
        choice = input("请输入选择 (1/s, 2/r, 3/a): ").strip().lower()
        if choice in ['1', 's', 'skip']:
            return 'skip'
        elif choice in ['2', 'r', 'replace', 'replace_all']:
            return 'replace_all'
        elif choice in ['3', 'a', 'ask']:
            return 'ask'
        else:
            print("无效输入，请重新选择。")


def should_process_file(output_file_path: pathlib.Path, overwrite_mode: str, input_file_path: pathlib.Path) -> bool:
    """根据覆盖模式和文件存在状态决定是否处理文件"""
    if not output_file_path.exists():
        return True
    
    if overwrite_mode == 'skip':
        print(f"    跳过: WebP文件已存在 '{output_file_path}'")
        return False
    elif overwrite_mode == 'replace_all':
        print(f"    覆盖: WebP文件已存在，将进行替换 '{output_file_path}'")
        return True
    elif overwrite_mode == 'ask':
        while True:
            response = input(f"    WebP文件已存在 '{output_file_path.name}'，是否覆盖？ (y/n): ").strip().lower()
            if response in ['y', 'yes', '是']:
                print(f"    用户选择覆盖: '{output_file_path}'")
                return True
            elif response in ['n', 'no', '否']:
                print(f"    用户选择跳过: '{output_file_path}'")
                return False
            else:
                print("    请输入 y/yes/是 或 n/no/否")
    
    return False


def convert_videos_to_webp_recursive(root_dir_path: pathlib.Path, ffmpeg_exe_path: str, overwrite_mode: str):
    """
    递归地将指定目录及其子目录下的视频文件转换为WebP，并显示文件大小。
    根据用户选择的覆盖模式处理已存在的WebP文件。
    """
    converted_count = 0
    failed_count = 0
    skipped_count = 0
    total_found = 0

    print(f"\n开始在目录 '{root_dir_path}' 及其子目录中查找视频文件并转换为 WebP (仅前 {CONVERSION_DURATION_SECONDS} 秒)...")
    
    # 首先统计总文件数
    for dirpath_str, _, filenames in os.walk(root_dir_path):
        current_dir_path = pathlib.Path(dirpath_str)
        for filename in filenames:
            input_file_path = current_dir_path / filename
            if input_file_path.suffix.lower() in VIDEO_EXTENSIONS and input_file_path.is_file():
                total_found += 1
    
    if total_found == 0:
        print(f"在目录 '{root_dir_path}' 中未找到任何支持的视频文件。")
        return
    
    print(f"找到 {total_found} 个视频文件待处理。")
    print(f"覆盖模式: {overwrite_mode}")
    print("-" * 60)
    
    current_file = 0
    
    for dirpath_str, _, filenames in os.walk(root_dir_path):
        current_dir_path = pathlib.Path(dirpath_str)
        for filename in filenames:
            input_file_path = current_dir_path / filename

            if input_file_path.suffix.lower() in VIDEO_EXTENSIONS and input_file_path.is_file():
                current_file += 1
                output_file_path = input_file_path.with_suffix(".webp")

                print(f"\n[{current_file}/{total_found}] 处理视频文件: {input_file_path}")

                # 根据覆盖模式决定是否处理
                if not should_process_file(output_file_path, overwrite_mode, input_file_path):
                    skipped_count += 1
                    continue

                command = [
                    ffmpeg_exe_path,
                    "-y",  # 覆盖输出文件而不询问
                    "-i", str(input_file_path),
                    "-t", CONVERSION_DURATION_SECONDS,
                ]
                command.extend(WEBP_CONVERSION_OPTIONS)
                command.append(str(output_file_path))

                print(f"    执行命令: {' '.join(command)}")

                try:
                    result = subprocess.run(command, capture_output=True, text=True, check=False,
                                            encoding='utf-8', errors='replace', timeout=FFMPEG_TIMEOUT_SECONDS)

                    if result.returncode == 0:
                        print(f"    ✓ 成功转换 (前 {CONVERSION_DURATION_SECONDS} 秒): {output_file_path.name}")
                        converted_count += 1
                        try:
                            original_size_bytes = input_file_path.stat().st_size
                            webp_size_bytes = output_file_path.stat().st_size
                            print(f"      原文件大小: {get_human_readable_size(original_size_bytes)}")
                            print(f"      WebP({CONVERSION_DURATION_SECONDS}s)文件大小: {get_human_readable_size(webp_size_bytes)}")
                            ratio = 0.0
                            if original_size_bytes > 0:
                                ratio = (webp_size_bytes / original_size_bytes) * 100
                                print(f"      WebP({CONVERSION_DURATION_SECONDS}s)大小为原文件的: {ratio:.2f}%")
                            elif webp_size_bytes > 0:
                                print(f"      WebP({CONVERSION_DURATION_SECONDS}s)大小为原文件的: N/A (原文件大小为0)")
                            else:
                                print(f"      WebP({CONVERSION_DURATION_SECONDS}s)大小为原文件的: N/A (原文件和WebP文件大小均为0)")
                        except OSError as e_stat:
                            print(f"      无法获取转换后文件大小: {e_stat}")
                    else:
                        print(f"    ✗ 错误: FFmpeg 转换失败 (返回码: {result.returncode})")
                        if result.stdout: 
                            print(f"      FFmpeg 输出 (stdout):\n{result.stdout.strip()}")
                        if result.stderr: 
                            print(f"      FFmpeg 错误 (stderr):\n{result.stderr.strip()}")
                        failed_count += 1
                        if output_file_path.exists():
                            try:
                                output_file_path.unlink()
                                print(f"      已删除不完整的输出文件: {output_file_path}")
                            except OSError as e_del:
                                print(f"      删除不完整的输出文件失败: {e_del}")
                except subprocess.TimeoutExpired as e_timeout:
                    print(f"    ✗ 错误: FFmpeg 转换超时 ({FFMPEG_TIMEOUT_SECONDS}s): {input_file_path.name}")
                    if e_timeout.stdout: 
                        print(f"      FFmpeg 输出 (stdout):\n{e_timeout.stdout.decode('utf-8', 'replace').strip()}")
                    if e_timeout.stderr: 
                        print(f"      FFmpeg 错误 (stderr):\n{e_timeout.stderr.decode('utf-8', 'replace').strip()}")
                    failed_count += 1
                    if output_file_path.exists():
                        try:
                            output_file_path.unlink()
                            print(f"      已删除因超时产生的不完整输出文件: {output_file_path}")
                        except OSError as e_del:
                            print(f"      删除因超时产生的不完整输出文件失败: {e_del}")
                except Exception as e_general:
                    print(f"    ✗ 错误: 转换 '{input_file_path.name}' 时发生意外错误: {e_general}")
                    failed_count += 1
                    if output_file_path.exists():
                        try:
                            output_file_path.unlink()
                            print(f"      已删除因意外错误产生的不完整输出文件: {output_file_path}")
                        except OSError as e_del:
                            print(f"      删除因意外错误产生的不完整输出文件失败: {e_del}")

    print("\n" + "=" * 60)
    print("--- 转换完成统计 ---")
    print(f"找到视频文件总数: {total_found} 个")
    print(f"成功转换 (前 {CONVERSION_DURATION_SECONDS} 秒): {converted_count} 个文件")
    print(f"跳过已存在文件: {skipped_count} 个文件")
    print(f"转换失败: {failed_count} 个文件")
    
    if total_found > 0:
        success_rate = (converted_count / total_found) * 100
        print(f"转换成功率: {success_rate:.1f}%")
    print("=" * 60)


def main():
    """主函数"""
    print("视频转WebP工具 - 批量转换器")
    print("=" * 60)
    print("支持格式: " + ", ".join(VIDEO_EXTENSIONS))
    print(f"转换时长: 前 {CONVERSION_DURATION_SECONDS} 秒")
    print(f"压缩参数: 质量75，有损压缩，无限循环")
    print("=" * 60)
    
    # 检查FFmpeg
    if not check_ffmpeg_availability(FFMPEG_PATH):
        print("\n无法继续执行，请确保FFmpeg正确安装后重试。")
        input("按 Enter 键退出...")
        return
    
    # 获取目标目录
    target_directory = get_valid_folder_path_from_user()
    if target_directory is None:
        print("\n操作已取消。")
        input("按 Enter 键退出...")
        return
    
    # 获取覆盖偏好
    overwrite_mode = get_overwrite_preference()
    
    # 开始转换
    try:
        convert_videos_to_webp_recursive(target_directory, FFMPEG_PATH, overwrite_mode)
    except KeyboardInterrupt:
        print("\n\n用户中断操作。")
    except Exception as e:
        print(f"\n\n程序执行过程中发生错误: {e}")
    finally:
        input("\n按 Enter 键退出...")


if __name__ == "__main__":
    main()                            