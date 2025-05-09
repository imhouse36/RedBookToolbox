import os  # os.walk 仍可使用，或被 pathlib.Path.rglob 替代
import subprocess
import pathlib  # 导入 pathlib 模块

# ==============================================================================
# 脚本功能核心备注 (Script Core Functionality Notes)
# ==============================================================================
#
# 脚本名称 (Script Name):
#   to_webp.py
#
# 主要目的 (Main Purpose):
#   本脚本用于将指定根目录及其子目录下的视频文件批量转换为动画 WebP 格式。
#
# 工作流程 (Workflow):
#   1. 提示用户输入一个包含视频文件的根目录路径。
#   2. 验证用户输入的路径是否为有效文件夹。
#   3. 检查 FFmpeg 是否已安装并配置在系统路径中，或在脚本中正确指定了路径。
#   4. 递归遍历指定根目录及其所有子目录。
#   5. 查找所有符合 `VIDEO_EXTENSIONS` 定义的视频文件。
#   6. 对每个找到的视频文件：
#      a. 提取视频的前 `CONVERSION_DURATION_SECONDS` 秒内容。
#      b. 使用 FFmpeg 和预设的 `WEBP_CONVERSION_OPTIONS` (可配置) 将这段时间的片段转换为 .webp 文件。
#      c. 生成的 .webp 文件将与原始视频文件同名 (扩展名改为 .webp) 并保存在同一目录下。
#      d. 如果目标 .webp 文件已存在，它将被覆盖。
#   7. 报告转换成功和失败的文件数量，并显示原始文件和转换后 WebP 文件的大小及比例。
#
# 配置项 (Key Configurations):
#   - `VIDEO_EXTENSIONS`: 定义了脚本会识别和处理的视频文件扩展名。
#   - `FFMPEG_PATH`: FFmpeg 可执行文件的路径。
#   - `WEBP_CONVERSION_OPTIONS`: FFmpeg 用于 WebP 转换的参数。
#   - `CONVERSION_DURATION_SECONDS`: 从视频截取的时长。
#
# 注意事项 (Important Notes):
#   - 依赖 FFmpeg：确保 FFmpeg 已正确安装。
#   - 文件覆盖：如果同名的 .webp 文件已存在，它将被新生成的 .webp 文件覆盖。
#   - 错误处理：脚本包含对 FFmpeg 执行错误和超时的基本处理。
#   - 输出文件：生成的 WebP 文件通常不包含音频，并且默认是无限循环的动画。
#
# ==============================================================================


# --- 配置 ---
VIDEO_EXTENSIONS = ('.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mpeg', '.mpg')
FFMPEG_PATH = "ffmpeg"  # 如果不在PATH中，请指定完整路径
CONVERSION_DURATION_SECONDS = "3"  # 从视频截取的时长（秒）
FFMPEG_TIMEOUT_SECONDS = 120  # FFmpeg 执行超时时间

# WebP转换参数 (可以根据需要调整)
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


def convert_videos_to_webp_recursive(root_dir_path: pathlib.Path, ffmpeg_exe_path: str):
    """
    递归地将指定目录及其子目录下的视频文件转换为WebP，并显示文件大小。
    如果目标WebP文件已存在，则会覆盖它。
    """
    converted_count = 0
    failed_count = 0

    print(
        f"开始在目录 '{root_dir_path}' 及其子目录中查找视频文件并转换为 WebP (仅前 {CONVERSION_DURATION_SECONDS} 秒)...")
    print("如果目标 WebP 文件已存在，它将被覆盖。")

    for dirpath_str, _, filenames in os.walk(root_dir_path):  # os.walk 仍适用
        current_dir_path = pathlib.Path(dirpath_str)
        for filename in filenames:
            input_file_path = current_dir_path / filename

            if input_file_path.suffix.lower() in VIDEO_EXTENSIONS and input_file_path.is_file():
                output_file_path = input_file_path.with_suffix(".webp")  # 更简洁地替换扩展名

                print(f"\n  发现视频文件: {input_file_path}")

                if output_file_path.exists():
                    print(f"    目标文件 '{output_file_path}' 已存在，将进行覆盖。")

                command = [
                    ffmpeg_exe_path,
                    "-y",  # 覆盖输出文件而不询问
                    "-i", str(input_file_path),  # FFmpeg 通常期望字符串路径
                    "-t", CONVERSION_DURATION_SECONDS,
                ]
                command.extend(WEBP_CONVERSION_OPTIONS)
                command.append(str(output_file_path))

                print(f"    执行命令: {' '.join(command)}")

                try:
                    # 使用 subprocess.run
                    result = subprocess.run(command, capture_output=True, text=True, check=False,  # check=False 手动检查返回码
                                            encoding='utf-8', errors='replace', timeout=FFMPEG_TIMEOUT_SECONDS)

                    if result.returncode == 0:
                        print(f"    成功转换 (前 {CONVERSION_DURATION_SECONDS} 秒): {output_file_path}")
                        converted_count += 1
                        try:
                            original_size_bytes = input_file_path.stat().st_size
                            webp_size_bytes = output_file_path.stat().st_size
                            print(f"      原文件大小: {get_human_readable_size(original_size_bytes)}")
                            print(
                                f"      WebP({CONVERSION_DURATION_SECONDS}s)文件大小: {get_human_readable_size(webp_size_bytes)}")
                            ratio = 0.0
                            if original_size_bytes > 0:
                                ratio = (webp_size_bytes / original_size_bytes) * 100
                                print(f"      WebP({CONVERSION_DURATION_SECONDS}s)大小为原文件的: {ratio:.2f}%")
                            elif webp_size_bytes > 0:
                                print(f"      WebP({CONVERSION_DURATION_SECONDS}s)大小为原文件的: N/A (原文件大小为0)")
                            else:
                                print(
                                    f"      WebP({CONVERSION_DURATION_SECONDS}s)大小为原文件的: N/A (原文件和WebP文件大小均为0)")
                        except OSError as e_stat:  # os.stat 或 Path.stat 可能抛出OSError
                            print(f"      无法获取转换后文件大小: {e_stat}")
                    else:
                        print(f"    错误: FFmpeg 转换失败 (返回码: {result.returncode})")
                        if result.stdout: print(f"      FFmpeg 输出 (stdout):\n{result.stdout.strip()}")
                        if result.stderr: print(f"      FFmpeg 错误 (stderr):\n{result.stderr.strip()}")
                        failed_count += 1
                        if output_file_path.exists():  # 检查文件是否存在再删除
                            try:
                                output_file_path.unlink()  # 使用 Path.unlink() 删除文件
                                print(f"      已删除不完整的输出文件: {output_file_path}")
                            except OSError as e_del:
                                print(f"      删除不完整的输出文件失败: {e_del}")
                except subprocess.TimeoutExpired as e_timeout:
                    print(f"    错误: FFmpeg 转换超时 ({FFMPEG_TIMEOUT_SECONDS}s): {input_file_path}")
                    if e_timeout.stdout: print(
                        f"      FFmpeg 输出 (stdout):\n{e_timeout.stdout.decode('utf-8', 'replace').strip()}")
                    if e_timeout.stderr: print(
                        f"      FFmpeg 错误 (stderr):\n{e_timeout.stderr.decode('utf-8', 'replace').strip()}")
                    failed_count += 1
                    if output_file_path.exists():  # 检查文件是否存在再删除
                        try:
                            output_file_path.unlink()
                            print(f"      已删除因超时产生的不完整输出文件: {output_file_path}")
                        except OSError as e_del:
                            print(f"      删除因超时产生的不完整输出文件失败: {e_del}")
                except Exception as e_general:
                    print(f"    执行 FFmpeg 时发生意外错误: {e_general}")
                    failed_count += 1

    print("\n--- 转换完成 ---")
    print(f"成功转换 (前 {CONVERSION_DURATION_SECONDS} 秒): {converted_count} 个文件")
    print(f"转换失败: {failed_count} 个文件")


if __name__ == "__main__":
    if not check_ffmpeg_availability(FFMPEG_PATH):
        input("\nFFmpeg 未正确配置。按 Enter 键退出...")
    else:
        target_root_directory_path = get_valid_folder_path_from_user()
        if target_root_directory_path:
            convert_videos_to_webp_recursive(target_root_directory_path, FFMPEG_PATH)
        input("\n所有操作已完成。按 Enter 键退出...")