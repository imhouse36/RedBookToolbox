import os
import subprocess
import shutil

# ==============================================================================
# 脚本功能核心备注 (Script Core Functionality Notes)
# ==============================================================================
#
# 脚本名称 (Script Name):
#   zip_webp.py (备注：此文件名可能不完全反映其当前功能，
#                其核心功能是从原始视频重新生成 WebP 文件)
#
# 主要目的 (Main Purpose):
#   本脚本用于批量处理指定根目录及其子目录下的 WebP 文件。
#   如果一个 WebP 文件的大小超过用户设定的阈值，脚本会尝试找到其对应的原始视频文件，
#   并从该原始视频文件重新生成一个新的 WebP 文件 (通常是截取视频前几秒并应用新的帧率)，
#   用以替换掉原来的、可能存在问题或过大的 WebP 文件。
#
# 工作流程 (Workflow):
#   1. 提示用户输入一个包含 WebP 文件（以及对应原始视频文件）的根目录路径。
#   2. 提示用户输入 WebP 文件的大小阈值 (MB) 和重新生成时使用的新目标帧率 (fps)。
#   3. 验证用户输入的路径是否为有效文件夹。
#   4. 检查 FFmpeg 是否已安装并配置。
#   5. 递归遍历指定根目录及其所有子目录。
#   6. 查找所有 .webp 文件。
#   7. 对每个找到的 .webp 文件：
#      a. 检查其大小是否超过用户设定的阈值。
#      b. 如果超过阈值：
#         i.   根据 .webp 文件的名称（去除 .webp 后缀）推断原始视频的基础文件名。
#              (例如，从 "IMG_123.JPG.webp" 得到 "IMG_123.JPG"作为基础名)
#         ii.  在同一目录下，使用 `ORIGINAL_VIDEO_EXTENSIONS` 列表尝试查找对应的原始视频文件
#              (例如，查找 "IMG_123.JPG.mp4", "IMG_123.JPG.mov" 等)。
#         iii. 如果找到原始视频文件：
#              - 使用 FFmpeg 从原始视频文件截取指定时长 (如前3秒)。
#              - 应用预设的 `BASE_WEBP_CONVERSION_OPTIONS_FROM_VIDEO` 和用户指定的新帧率，
#                将截取的片段转换为新的 .webp 文件。
#              - 新生成的 .webp 文件将直接覆盖掉旧的（有问题的/过大的）.webp 文件。
#         iv.  如果未找到原始视频文件，则跳过该 .webp 文件。
#   8. 用户确认后开始处理 (有备份警告)。
#   9. 报告重新生成成功、失败、因大小跳过、因未找到源文件而跳过的 WebP 文件数量。
#
# 配置项 (Key Configurations):
#   - `FFMPEG_PATH`: FFmpeg 可执行文件的路径。
#   - `ORIGINAL_VIDEO_EXTENSIONS`: 用于查找原始视频文件的扩展名列表。
#   - `BASE_WEBP_CONVERSION_OPTIONS_FROM_VIDEO`: 从视频重新生成 WebP 时的基础 FFmpeg 参数。
#   - `VIDEO_DURATION_FOR_WEBP`: 从原始视频截取的时长。
#
# 注意事项 (Important Notes):
#   - 依赖 FFmpeg：确保 FFmpeg 已正确安装。
#   - 文件覆盖：脚本会直接覆盖旧的 .webp 文件，强烈建议备份数据。
#   - 原始视频文件命名：脚本假设原始视频文件名与 .webp 文件名（去除 .webp 后缀）部分相同，
#     例如 "ABC.XYZ.webp" 对应的原始视频可能是 "ABC.XYZ.mp4"。
#   - 错误处理：包含对 FFmpeg 执行错误和超时的基本处理。
#
# ==============================================================================


# --- 配置 ---
FFMPEG_PATH = "ffmpeg"  # 如果不在PATH中，请指定完整路径

# 原始视频文件可能的扩展名列表 (请根据您的实际情况调整)
# 脚本会按此顺序查找原始视频文件
ORIGINAL_VIDEO_EXTENSIONS = ['.mp4', '.mov', '.mkv', '.avi', '.wmv', '.flv', '.webm', '.mpeg', '.mpg']

# WebP转换参数基础 (帧率和时长会动态设置)
BASE_WEBP_CONVERSION_OPTIONS_FROM_VIDEO = [
    "-c:v", "libwebp",
    "-lossless", "0",  # 0 表示有损，1 表示无损
    "-q:v", "75",  # 有损压缩质量 (0-100，越高越好)
    "-loop", "0",  # 0 表示无限循环
    "-an",  # 通常WebP不含音频
]
# 从原始视频截取的时长，例如只取前3秒
VIDEO_DURATION_FOR_WEBP = "3"
# --- /配置 ---

def get_human_readable_size(size_bytes):
    """将字节大小转换为人类可读的格式 (B, KB, MB, GB)"""
    if size_bytes is None:
        return "N/A"
    if size_bytes == 0:
        return "0 B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = 0
    size_bytes = float(size_bytes)
    while size_bytes >= 1024 and i < len(size_name) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.2f} {size_name[i]}"


def get_valid_folder_path_from_user(prompt_message):
    """提示用户输入一个文件夹路径，并验证其有效性。"""
    while True:
        folder_path = input(prompt_message).strip()
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
        subprocess.run([ffmpeg_path, "-version"], capture_output=True, check=True, text=True, encoding='utf-8')
        print(f"FFmpeg 在 '{ffmpeg_path}' 找到并可用。\n")
        return True
    except FileNotFoundError:
        print(f"错误: FFmpeg 可执行文件在 '{ffmpeg_path}' 未找到。")
        print("请确保FFmpeg已安装并添加到系统PATH，或者在脚本中正确配置 FFMPEG_PATH。")
        return False
    except subprocess.CalledProcessError as e:
        print(f"错误: 执行 FFmpeg 时出错: {e}")
        print(f"FFmpeg 输出: {e.stdout}")
        print(f"FFmpeg 错误: {e.stderr}")
        print("FFmpeg 可能安装不正确。")
        return False
    except Exception as e_gen:
        print(f"检查 FFmpeg 可用性时发生未知错误: {e_gen}")
        return False


def get_regeneration_parameters():
    """获取用户输入的大小阈值 X (MB) 和新帧率 Y (fps)"""
    while True:
        try:
            size_threshold_mb_str = input(
                "请输入文件大小阈值 X (MB)，超过此大小的 WebP 文件将被尝试从其原始视频重新生成: ").strip()
            size_threshold_mb = float(size_threshold_mb_str)
            if size_threshold_mb <= 0:
                print("错误：大小阈值必须为正数。")
                continue
            break
        except ValueError:
            print("错误：请输入一个有效的数字作为大小阈值。")

    while True:
        try:
            new_fps_str = input("请输入重新生成 WebP 时使用的新目标帧率 Y (fps): ").strip()
            new_fps = int(new_fps_str)
            if new_fps <= 0:
                print("错误：帧率必须为正整数。")
                continue
            break
        except ValueError:
            print("错误：请输入一个有效的整数作为帧率。")
    return size_threshold_mb * 1024 * 1024, new_fps


def find_original_video_file(webp_dir, base_name_for_lookup):
    """
    根据 WebP 文件的基本名称和目录，查找可能的原始视频文件。
    返回找到的原始视频文件的完整路径，如果找不到则返回 None。
    """
    for video_ext in ORIGINAL_VIDEO_EXTENSIONS:
        potential_video_path = os.path.join(webp_dir, base_name_for_lookup + video_ext)
        if os.path.isfile(potential_video_path):
            return potential_video_path
    return None


def regenerate_webp_from_source_video(root_dir, ffmpeg_exe_path, size_threshold_bytes, new_fps):
    """
    在指定目录及其子目录中查找 WebP 文件，
    如果文件大小超过阈值，则尝试从其对应的原始视频文件重新生成 WebP。
    """
    regenerated_count = 0
    failed_count = 0
    skipped_count = 0
    no_source_found_count = 0
    processed_webp_files = 0

    print(f"\n开始在目录 '{root_dir}' 及其子目录中扫描 WebP 文件以尝试重新生成...")
    print(f"大小阈值: {get_human_readable_size(size_threshold_bytes)} (超过此大小的 WebP 会被尝试替换)")
    print(f"新帧率 (用于重新生成): {new_fps} fps")
    print(f"将从原始视频截取前 {VIDEO_DURATION_FOR_WEBP} 秒。")
    print(f"尝试查找的原始视频扩展名: {', '.join(ORIGINAL_VIDEO_EXTENSIONS)}")
    print("-" * 30)

    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.lower().endswith(".webp"):
                processed_webp_files += 1
                problematic_webp_path = os.path.join(dirpath, filename)

                try:
                    original_webp_size_bytes = os.path.getsize(problematic_webp_path)
                except OSError as e:
                    print(f"\n错误: 无法获取文件 '{problematic_webp_path}' 的大小: {e}, 跳过。")
                    failed_count += 1
                    continue

                print(f"\n发现 WebP 文件: {problematic_webp_path}")
                print(f"  当前 WebP 大小: {get_human_readable_size(original_webp_size_bytes)}")

                if original_webp_size_bytes <= size_threshold_bytes:
                    print(f"  文件大小未超过阈值 {get_human_readable_size(size_threshold_bytes)}，跳过重新生成。")
                    skipped_count += 1
                    continue

                base_for_lookup, _ = os.path.splitext(filename)
                print(f"  将使用基础名 '{base_for_lookup}' 查找原始视频。")

                source_video_path = find_original_video_file(dirpath, base_for_lookup)

                if not source_video_path:
                    print(f"  错误: 未能找到与基础名 '{base_for_lookup}' 对应的原始视频文件。跳过重新生成。")
                    no_source_found_count += 1
                    continue

                print(f"  找到对应的原始视频文件: {source_video_path}")

                output_webp_path = problematic_webp_path

                command = [
                    ffmpeg_exe_path,
                    "-y",
                    "-i", source_video_path,
                    "-t", VIDEO_DURATION_FOR_WEBP,
                ]

                current_conversion_options = list(BASE_WEBP_CONVERSION_OPTIONS_FROM_VIDEO)

                temp_options_excluding_vf = []
                existing_vf_value = ""
                skip_next_for_vf_value = False

                for i in range(len(current_conversion_options)):
                    if skip_next_for_vf_value:
                        skip_next_for_vf_value = False
                        continue

                    if current_conversion_options[i] == "-vf":
                        if i + 1 < len(current_conversion_options):
                            existing_vf_value = current_conversion_options[i + 1]
                            skip_next_for_vf_value = True
                    else:
                        temp_options_excluding_vf.append(current_conversion_options[i])

                new_vf_filters = []
                if existing_vf_value:
                    for filt in existing_vf_value.split(','):
                        if not filt.strip().startswith("fps="):
                            new_vf_filters.append(filt.strip())

                new_vf_filters.append(f"fps={new_fps}")

                final_vf_string = ",".join(filter(None, new_vf_filters))

                command.extend(temp_options_excluding_vf)
                if final_vf_string:
                    command.extend(["-vf", final_vf_string])

                command.append(output_webp_path)

                print(f"  执行命令从原始视频重新生成 WebP: {' '.join(command)}")

                try:
                    process = subprocess.run(command, capture_output=True, text=True, check=False,
                                             encoding='utf-8', errors='replace', timeout=180)

                    if process.returncode == 0:
                        if not os.path.exists(output_webp_path) or os.path.getsize(output_webp_path) == 0:
                            print(f"  错误: FFmpeg 声称成功，但新生成的 WebP 文件 '{output_webp_path}' 未找到或为空。")
                            print(f"    FFmpeg 输出 (stdout):\n{process.stdout or '无'}")
                            print(f"    FFmpeg 错误 (stderr):\n{process.stderr or '无'}")
                            failed_count += 1
                            continue

                        new_webp_size_bytes = os.path.getsize(output_webp_path)
                        print(f"  成功从原始视频重新生成 WebP: {output_webp_path}")
                        print(f"    原问题 WebP 大小: {get_human_readable_size(original_webp_size_bytes)}")
                        print(f"    新生成 WebP 大小: {get_human_readable_size(new_webp_size_bytes)}")

                        size_change_percentage = 0
                        if original_webp_size_bytes > 0:
                            size_change_percentage = ((
                                                                  new_webp_size_bytes - original_webp_size_bytes) / original_webp_size_bytes) * 100
                            print(f"    新 WebP 相对于旧 WebP 的大小改变: {size_change_percentage:.2f}%")
                        elif new_webp_size_bytes > 0:
                            print(f"    新 WebP 相对于旧 WebP 的大小改变: N/A (旧 WebP 大小为0)")
                        else:
                            print(f"    新 WebP 相对于旧 WebP 的大小改变: N/A (新旧 WebP 大小均为0)")
                        regenerated_count += 1
                    else:
                        print(f"  错误: FFmpeg 从原始视频重新生成 WebP 失败 (返回码: {process.returncode})")
                        print(f"    FFmpeg 输出 (stdout):\n{process.stdout or '无'}")
                        print(f"    FFmpeg 错误 (stderr):\n{process.stderr or '无'}")
                        failed_count += 1

                except subprocess.TimeoutExpired:
                    print(f"  错误: FFmpeg 从原始视频重新生成 WebP 超时: {source_video_path}")
                    failed_count += 1
                except Exception as e:
                    print(f"  执行 FFmpeg 从原始视频重新生成 WebP 时发生意外错误: {e}")
                    failed_count += 1

    print("\n--- 从原始视频重新生成 WebP 完成 ---")
    if processed_webp_files == 0:
        print("未在指定目录中找到任何 .webp 文件进行处理。")
    else:
        print(f"总共扫描 .webp 文件: {processed_webp_files}")
        print(f"成功重新生成: {regenerated_count} 个 WebP 文件")
        print(f"因大小未超阈值而跳过: {skipped_count} 个文件")
        print(f"因未找到对应原始视频而跳过: {no_source_found_count} 个文件")
        print(f"重新生成失败: {failed_count} 个文件")


if __name__ == "__main__":
    print("WebP 文件批量重新生成脚本 (从原始视频)")
    print("======================================")

    if not check_ffmpeg_availability(FFMPEG_PATH):
        input("\nFFmpeg 未正确配置。按 Enter 键退出...")
    else:
        target_root_directory = get_valid_folder_path_from_user("请输入包含问题 WebP 文件的根目录路径: ")
        size_threshold, target_fps = get_regeneration_parameters()

        print("\n警告：此脚本将尝试覆盖原始的 .webp 文件。")
        confirm = input("在继续之前，请确保您已备份重要数据。输入 'yes' 继续: ").strip().lower()
        if confirm == 'yes':
            regenerate_webp_from_source_video(target_root_directory, FFMPEG_PATH, size_threshold, target_fps)
        else:
            print("操作已取消。")

        input("\n所有操作已完成 (或已取消)。按 Enter 键退出...")