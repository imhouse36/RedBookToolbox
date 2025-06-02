#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import subprocess
import pathlib  # 导入 pathlib 模块
import signal
import threading
import platform

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

# 全局变量用于跟踪当前运行的进程
current_ffmpeg_process = None
process_lock = threading.Lock()

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

def signal_handler(signum, frame):
    """处理中断信号，终止当前运行的FFmpeg进程"""
    global current_ffmpeg_process
    print("\n\n⚠️ 收到中断信号，正在终止当前进程...")
    
    with process_lock:
        if current_ffmpeg_process and current_ffmpeg_process.poll() is None:
            try:
                print("正在终止FFmpeg进程...")
                current_ffmpeg_process.terminate()
                # 等待进程终止，如果超时则强制杀死
                try:
                    current_ffmpeg_process.wait(timeout=5)
                    print("FFmpeg进程已成功终止")
                except subprocess.TimeoutExpired:
                    print("FFmpeg进程未在5秒内终止，强制杀死进程")
                    current_ffmpeg_process.kill()
                    current_ffmpeg_process.wait()
                    print("FFmpeg进程已被强制终止")
            except Exception as e:
                print(f"终止FFmpeg进程时发生错误: {e}")
    
    print("操作已被用户中断")
    sys.exit(0)

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

    print(f"\n开始在目录 '{root_dir_path}' 及其子目录中查找视频文件并转换为 WebP (仅前 {CONVERSION_DURATION_SECONDS} 秒)...", flush=True)
    
    # 首先统计总文件数
    for dirpath_str, _, filenames in os.walk(root_dir_path):
        current_dir_path = pathlib.Path(dirpath_str)
        for filename in filenames:
            input_file_path = current_dir_path / filename
            if input_file_path.suffix.lower() in VIDEO_EXTENSIONS and input_file_path.is_file():
                total_found += 1
    
    if total_found == 0:
        print(f"在目录 '{root_dir_path}' 中未找到任何支持的视频文件。", flush=True)
        return
    
    print(f"找到 {total_found} 个视频文件待处理。", flush=True)
    print(f"覆盖模式: {overwrite_mode}", flush=True)
    print("-" * 60, flush=True)
    
    current_file = 0
    
    for dirpath_str, _, filenames in os.walk(root_dir_path):
        current_dir_path = pathlib.Path(dirpath_str)
        for filename in filenames:
            input_file_path = current_dir_path / filename

            if input_file_path.suffix.lower() in VIDEO_EXTENSIONS and input_file_path.is_file():
                current_file += 1
                output_file_path = input_file_path.with_suffix(".webp")

                print(f"\n[{current_file}/{total_found}] 处理视频文件: {input_file_path}", flush=True)

                # 根据覆盖模式决定是否处理
                if not should_process_file(output_file_path, overwrite_mode, input_file_path):
                    skipped_count += 1
                    continue

                command = [
                    ffmpeg_exe_path,
                    "-y",  # 覆盖输出文件而不询问
                    "-i", str(input_file_path),
                    "-t", str(CONVERSION_DURATION_SECONDS),
                ]
                command.extend(WEBP_CONVERSION_OPTIONS)
                command.append(str(output_file_path))

                print(f"    执行命令: {' '.join(command)}", flush=True)

                try:
                    # 使用Popen来获取进程对象，以便可以在信号处理中终止
                    with process_lock:
                        current_ffmpeg_process = subprocess.Popen(command, stdout=subprocess.PIPE, 
                                                                 stderr=subprocess.PIPE, text=True,
                                                                 encoding='utf-8', errors='replace')
                    
                    try:
                        stdout, stderr = current_ffmpeg_process.communicate(timeout=FFMPEG_TIMEOUT_SECONDS)
                        returncode = current_ffmpeg_process.returncode
                    finally:
                        with process_lock:
                            current_ffmpeg_process = None

                    if returncode == 0:
                        print(f"    ✓ 成功转换 (前 {CONVERSION_DURATION_SECONDS} 秒): {output_file_path.name}", flush=True)
                        converted_count += 1
                        try:
                            original_size_bytes = input_file_path.stat().st_size
                            webp_size_bytes = output_file_path.stat().st_size
                            print(f"      原文件大小: {get_human_readable_size(original_size_bytes)}", flush=True)
                            print(f"      WebP({CONVERSION_DURATION_SECONDS}s)文件大小: {get_human_readable_size(webp_size_bytes)}", flush=True)
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
                        print(f"    ✗ 错误: FFmpeg 转换失败 (返回码: {returncode})")
                        if stdout: 
                            print(f"      FFmpeg 输出 (stdout):\n{stdout.strip()}")
                        if stderr: 
                            print(f"      FFmpeg 错误 (stderr):\n{stderr.strip()}")
                        failed_count += 1
                        if output_file_path.exists():
                            try:
                                output_file_path.unlink()
                                print(f"      已删除不完整的输出文件: {output_file_path}")
                            except OSError as e_del:
                                print(f"      删除不完整的输出文件失败: {e_del}")
                except subprocess.TimeoutExpired:
                    print(f"    ✗ 错误: FFmpeg 转换超时 ({FFMPEG_TIMEOUT_SECONDS}s): {input_file_path.name}")
                    # 终止超时的进程
                    with process_lock:
                        if current_ffmpeg_process and current_ffmpeg_process.poll() is None:
                            current_ffmpeg_process.terminate()
                            try:
                                current_ffmpeg_process.wait(timeout=5)
                            except subprocess.TimeoutExpired:
                                current_ffmpeg_process.kill()
                                current_ffmpeg_process.wait()
                        current_ffmpeg_process = None
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


import argparse # 导入 argparse 模块

def main():
    """主函数，执行脚本的核心逻辑"""
    global CONVERSION_DURATION_SECONDS # 在函数开始就声明全局变量
    
    # 注册信号处理程序
    signal.signal(signal.SIGINT, signal_handler)
    if platform.system() == "Windows":
        signal.signal(signal.SIGBREAK, signal_handler) # Windows下的Ctrl+Break

    parser = argparse.ArgumentParser(description="将视频文件批量转换为WebP格式。")
    parser.add_argument("root_folder", type=str, help="包含视频文件的根目录路径")
    parser.add_argument("--overwrite", type=str, choices=['skip', 'replace_all', 'ask'], default='ask', 
                        help="处理已存在的WebP文件的方式: 'skip', 'replace_all', 'ask' (默认)")
    parser.add_argument("--duration", type=str, default=CONVERSION_DURATION_SECONDS, 
                        help=f"从视频截取的时长（秒），默认为 {CONVERSION_DURATION_SECONDS}")

    # 检查是否从服务器环境运行（通过特定环境变量判断，或者没有输入参数时）
    # 在服务器环境中，参数由 server.py 传递
    # 在直接运行时，如果没有提供参数，则进入交互模式
    args = None
    
    # 如果在服务器模式下或者有命令行参数，尝试解析参数
    server_mode = 'WEBP_TOOL_SERVER_MODE' in os.environ
    has_args = len(sys.argv) > 1
    
    if server_mode or has_args:
        try:
            args = parser.parse_args()
            print("通过命令行参数运行...")
        except SystemExit: # argparse 在参数错误时会调用 sys.exit()
            print("命令行参数解析失败，尝试进入交互模式或检查参数...")
            # 如果是服务器调用，不应该进入交互模式，而是报错退出
            if server_mode:
                 print("错误：服务器模式下命令行参数解析失败。请检查服务器传递的参数。")
                 sys.exit(1)
            # 否则，可能是用户直接运行但参数错了，可以尝试交互
            args = None

    if args and args.root_folder:
        root_folder_str = args.root_folder
        overwrite_mode = args.overwrite
        CONVERSION_DURATION_SECONDS = args.duration
        print(f"根目录: {root_folder_str}", flush=True)
        print(f"覆盖模式: {overwrite_mode}", flush=True)
        print(f"转换时长: {CONVERSION_DURATION_SECONDS}秒", flush=True)
        root_folder = pathlib.Path(root_folder_str)
        if not root_folder.is_dir():
            print(f"错误：通过参数提供的路径 '{root_folder_str}' 不是一个有效的文件夹。", flush=True)
            sys.exit(1)
    else:
        print("欢迎使用视频批量转WebP工具！(交互模式)")
        print("=========================================")
        if not check_ffmpeg_availability(FFMPEG_PATH):
            sys.exit(1)
        root_folder = get_valid_folder_path_from_user()
        overwrite_mode = get_overwrite_preference() # 获取覆盖偏好
        # 交互模式下也可以考虑让用户输入时长
        try:
            duration_input = input(f"请输入转换时长（秒，默认为 {CONVERSION_DURATION_SECONDS}，直接回车使用默认值）: ").strip()
            if duration_input:
                CONVERSION_DURATION_SECONDS = duration_input
        except EOFError: # 如果是在非交互环境（如服务器重定向了stdin但未提供输入）
            print("无法读取时长输入，使用默认值。")
            pass # 使用默认时长

    if not check_ffmpeg_availability(FFMPEG_PATH):
        sys.exit(1)

    convert_videos_to_webp_recursive(root_folder, FFMPEG_PATH, overwrite_mode)


if __name__ == "__main__":
    main()