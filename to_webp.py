import os
import subprocess

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
#      a. 提取视频的前3秒内容。
#      b. 使用 FFmpeg 和预设的 `WEBP_CONVERSION_OPTIONS` (可配置) 将这3秒的片段转换为 .webp 文件。
#      c. 生成的 .webp 文件将与原始视频文件同名 (扩展名改为 .webp) 并保存在同一目录下。
#      d. 如果目标 .webp 文件已存在，它将被覆盖。
#   7. 报告转换成功和失败的文件数量，并显示原始文件和转换后 WebP 文件的大小及比例。
#
# 配置项 (Key Configurations):
#   - `VIDEO_EXTENSIONS`: 定义了脚本会识别和处理的视频文件扩展名。
#   - `FFMPEG_PATH`: FFmpeg 可执行文件的路径。
#   - `WEBP_CONVERSION_OPTIONS`: FFmpeg 用于 WebP 转换的参数，如编码器、质量、循环、音频去除等。
#   - 转换时长固定为视频的前3秒。
#
# 注意事项 (Important Notes):
#   - 依赖 FFmpeg：确保 FFmpeg 已正确安装并在系统路径中，或在脚本中指定了完整路径。
#   - 文件覆盖：如果同名的 .webp 文件已存在，它将被新生成的 .webp 文件覆盖。
#   - 错误处理：脚本包含对 FFmpeg 执行错误和超时的基本处理。
#   - 输出文件：生成的 WebP 文件通常不包含音频，并且默认是无限循环的动画。
#
# ==============================================================================


# --- 配置 ---
VIDEO_EXTENSIONS = ('.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mpeg', '.mpg')
FFMPEG_PATH = "ffmpeg"  # 如果不在PATH中，请指定完整路径

# WebP转换参数 (可以根据需要调整)
# -c:v libwebp: 使用libwebp编码器
# -lossless 0: 0表示有损压缩, 1表示无损压缩 (无损文件会大很多)
# -q:v 75:     质量因子 (对于有损libwebp, 0-100, 越高越好但文件越大, 75是不错的折中)
# -loop 0:     循环次数 (0表示无限循环, 适用于GIF转WebP或短视频转动画WebP)
# -an:         去除音频 (WebP通常不含音频)
# -vf "fps=15,scale=iw/2:-1": 可选的滤镜，例如设置帧率为15fps，并将宽度减半
#                              如果视频本身帧率合适，可以不用fps。
#                              scale=iw:ih 表示保持原分辨率。
WEBP_CONVERSION_OPTIONS = [
    "-c:v", "libwebp",
    "-lossless", "0",  # 0 表示有损，1 表示无损
    "-q:v", "75",  # 有损压缩质量 (0-100，越高越好)
    "-loop", "0",  # 0 表示无限循环
    "-an",  # 不含音频
    # "-vf", "fps=10",
    # "-vf", "fps=15,scale=iw/2:-1", # 可选：设置帧率和缩放比例
    # 对于3秒的片段，您可能希望保留原始帧率/缩放比例
    # 或者使用更低的帧率以进一步减小文件大小。
    # 例如，"-vf", "fps=10"
]
# --- /配置 ---

def get_human_readable_size(size_bytes):
    """将字节大小转换为人类可读的格式 (KB, MB, GB)"""
    if size_bytes == 0:
        return "0 B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = 0
    while size_bytes >= 1024 and i < len(size_name) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.2f} {size_name[i]}"


def get_valid_folder_path_from_user():
    """提示用户输入一个文件夹路径，并验证其有效性。"""
    while True:
        folder_path = input("请输入要处理的视频文件所在的根目录路径: ").strip()
        if folder_path.startswith('"') and folder_path.endswith('"'):
            folder_path = folder_path[1:-1]
        elif folder_path.startswith("'") and folder_path.endswith("'"):
            folder_path = folder_path[1:-1]

        if os.path.isdir(folder_path):
            return folder_path
        else:
            print(f"错误：路径 '{folder_path}' 不是一个有效的文件夹，或文件夹不存在。请重新输入。")


def check_ffmpeg_availability(ffmpeg_path):
    """检查FFmpeg是否可用"""
    try:
        subprocess.run([ffmpeg_path, "-version"], capture_output=True, check=True, text=True)
        print(f"FFmpeg 在 '{ffmpeg_path}' 找到并可用。\n")
        return True
    except FileNotFoundError:
        print(f"错误: FFmpeg 可执行文件在 '{ffmpeg_path}' 未找到。")
        print("请确保FFmpeg已安装并添加到系统PATH，或者在脚本中正确配置 FFMPEG_PATH。")
        return False
    except subprocess.CalledProcessError as e:
        print(f"错误: 执行 FFmpeg 时出错: {e}")
        print("FFmpeg 可能安装不正确。")
        return False


def convert_videos_to_webp_recursive(root_dir, ffmpeg_exe_path):
    """
    递归地将指定目录及其子目录下的视频文件转换为WebP (仅前3秒)，并显示文件大小。
    如果目标WebP文件已存在，则会覆盖它。
    """
    converted_count = 0
    failed_count = 0
    # skipped_count 变量已移除

    print(f"开始在目录 '{root_dir}' 及其子目录中查找视频文件并转换为 WebP (仅前3秒)...")
    print("如果目标 WebP 文件已存在，它将被覆盖。")

    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            base, ext = os.path.splitext(filename)
            if ext.lower() in VIDEO_EXTENSIONS:
                input_file_path = os.path.join(dirpath, filename)
                output_file_path = os.path.join(dirpath, base + ".webp")

                print(f"\n  发现视频文件: {input_file_path}")

                if os.path.exists(output_file_path):
                    print(f"    目标文件 '{output_file_path}' 已存在，将进行覆盖。")

                command = [
                    ffmpeg_exe_path,
                    "-y",
                    "-i", input_file_path,
                    "-t", "3",
                ]
                command.extend(WEBP_CONVERSION_OPTIONS)
                command.append(output_file_path)

                print(f"    执行命令: {' '.join(command)}")

                try:
                    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                               encoding='utf-8', errors='replace')
                    stdout, stderr = process.communicate(timeout=120)

                    if process.returncode == 0:
                        print(f"    成功转换 (前3秒): {output_file_path}")
                        converted_count += 1
                        try:
                            original_size_bytes = os.path.getsize(input_file_path)
                            webp_size_bytes = os.path.getsize(output_file_path)
                            print(f"      原文件大小: {get_human_readable_size(original_size_bytes)}")
                            print(f"      WebP(3s)文件大小: {get_human_readable_size(webp_size_bytes)}")
                            ratio = 0
                            if original_size_bytes > 0:
                                ratio = (webp_size_bytes / original_size_bytes) * 100
                                print(f"      WebP(3s)大小为原文件的: {ratio:.2f}%")
                            elif webp_size_bytes > 0:
                                print(f"      WebP(3s)大小为原文件的: N/A (原文件大小为0)")
                            else:
                                print(f"      WebP(3s)大小为原文件的: N/A (原文件和WebP文件大小均为0)")

                        except OSError as e:
                            print(f"      无法获取转换后文件大小: {e}")
                    else:
                        print(f"    错误: FFmpeg 转换失败 (返回码: {process.returncode})")
                        print(f"      FFmpeg 输出 (stdout):\n{stdout}")
                        print(f"      FFmpeg 错误 (stderr):\n{stderr}")
                        failed_count += 1
                        if os.path.exists(output_file_path):
                            try:
                                os.remove(output_file_path)
                                print(f"      已删除不完整的输出文件: {output_file_path}")
                            except OSError as e_del:
                                print(f"      删除不完整的输出文件失败: {e_del}")
                except subprocess.TimeoutExpired:
                    process.kill()
                    stdout, stderr = process.communicate()
                    print(f"    错误: FFmpeg 转换超时: {input_file_path}")
                    print(f"      FFmpeg 输出 (stdout):\n{stdout}")
                    print(f"      FFmpeg 错误 (stderr):\n{stderr}")
                    failed_count += 1
                    if os.path.exists(output_file_path):
                        try:
                            os.remove(output_file_path)
                            print(f"      已删除因超时产生的不完整输出文件: {output_file_path}")
                        except OSError as e_del:
                            print(f"      删除因超时产生的不完整输出文件失败: {e_del}")
                except Exception as e:
                    print(f"    执行 FFmpeg 时发生意外错误: {e}")
                    failed_count += 1

    print("\n--- 转换完成 ---")
    print(f"成功转换 (前3秒): {converted_count} 个文件")
    print(f"转换失败: {failed_count} 个文件")


if __name__ == "__main__":
    if not check_ffmpeg_availability(FFMPEG_PATH):
        input("\nFFmpeg 未正确配置。按 Enter 键退出...")
    else:
        target_root_directory = get_valid_folder_path_from_user()
        if target_root_directory:
            convert_videos_to_webp_recursive(target_root_directory, FFMPEG_PATH)
        input("\n所有操作已完成。按 Enter 键退出...")