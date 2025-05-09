import os
import subprocess
import shutil  # 虽然未使用，但保留原导入
import pathlib
import time  # 从其他脚本看，可能需要暂停，但此脚本中当前未使用
from typing import Union, Tuple, List, Optional  # 导入 Union, Tuple, List, Optional

# ==============================================================================
# 脚本功能核心备注 (Script Core Functionality Notes)
# ==============================================================================
#
# 脚本建议名称 (Suggested Script Name):
#   regenerate_problematic_webp.py (或 optimize_large_webp.py)
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
FFMPEG_PATH = "ffmpeg"
ORIGINAL_VIDEO_EXTENSIONS = ['.mp4', '.mov', '.mkv', '.avi', '.wmv', '.flv', '.webm', '.mpeg', '.mpg']
BASE_WEBP_CONVERSION_OPTIONS_FROM_VIDEO = [
    "-c:v", "libwebp",
    "-lossless", "0",
    "-q:v", "75",
    "-loop", "0",
    "-an",
]
VIDEO_DURATION_FOR_WEBP = "3"  # 秒
FFMPEG_TIMEOUT_SECONDS = 180


# --- /配置 ---

def get_human_readable_size(size_bytes: Optional[int]) -> str:  # 使用 Optional[int] 替代 int | None
    """将字节大小转换为人类可读的格式 (B, KB, MB, GB)"""
    if size_bytes is None:
        return "N/A"
    if size_bytes == 0:
        return "0 B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = 0
    size_bytes_float = float(size_bytes)
    while size_bytes_float >= 1024 and i < len(size_name) - 1:
        size_bytes_float /= 1024.0
        i += 1
    return f"{size_bytes_float:.2f} {size_name[i]}"


def get_valid_folder_path_from_user(prompt_message: str) -> pathlib.Path:
    """提示用户输入一个文件夹路径，并验证其有效性。"""
    while True:
        folder_path_str = input(prompt_message).strip()
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
        result = subprocess.run([ffmpeg_exe_path, "-version"], capture_output=True, check=True, text=True,
                                encoding='utf-8', errors='replace')
        print(f"FFmpeg 在 '{ffmpeg_exe_path}' 找到并可用。\n")
        return True
    except FileNotFoundError:
        print(f"错误: FFmpeg 可执行文件在 '{ffmpeg_exe_path}' 未找到。")
        print("请确保FFmpeg已安装并添加到系统PATH，或者在脚本中正确配置 FFMPEG_PATH。")
        return False
    except subprocess.CalledProcessError as e:
        print(f"错误: 执行 FFmpeg -version 时出错 (返回码: {e.returncode}):")
        if e.stdout: print(f"  Stdout: {e.stdout.strip()}")
        if e.stderr: print(f"  Stderr: {e.stderr.strip()}")
        print("FFmpeg 可能安装不正确。")
        return False
    except Exception as e_gen:
        print(f"检查 FFmpeg 可用性时发生未知错误: {e_gen}")
        return False


def get_regeneration_parameters() -> Tuple[float, int]:  # 使用 Tuple
    """获取用户输入的大小阈值 X (MB) 和新帧率 Y (fps)"""
    size_threshold_bytes = 0.0
    new_fps_val = 0
    while True:
        try:
            size_threshold_mb_str = input(
                "请输入文件大小阈值 X (MB)，超过此大小的 WebP 文件将被尝试从其原始视频重新生成: ").strip()
            size_threshold_mb = float(size_threshold_mb_str)
            if size_threshold_mb <= 0:
                print("错误：大小阈值必须为正数。")
                continue
            size_threshold_bytes = size_threshold_mb * 1024 * 1024
            break
        except ValueError:
            print("错误：请输入一个有效的数字作为大小阈值。")

    while True:
        try:
            new_fps_str = input("请输入重新生成 WebP 时使用的新目标帧率 Y (fps): ").strip()
            new_fps_val = int(new_fps_str)
            if new_fps_val <= 0:
                print("错误：帧率必须为正整数。")
                continue
            break
        except ValueError:
            print("错误：请输入一个有效的整数作为帧率。")
    return size_threshold_bytes, new_fps_val


def find_original_video_file(webp_dir_path: pathlib.Path, base_name_for_lookup: str) -> Optional[
    pathlib.Path]:  # 使用 Optional
    """
    根据 WebP 文件的基本名称和目录，查找可能的原始视频文件。
    返回找到的原始视频文件的 Path 对象，如果找不到则返回 None。
    """
    for video_ext in ORIGINAL_VIDEO_EXTENSIONS:
        potential_video_path = webp_dir_path / (base_name_for_lookup + video_ext)
        if potential_video_path.is_file():
            return potential_video_path
    return None


def build_ffmpeg_command_for_regeneration(ffmpeg_exe_path: str,
                                          source_video_path: pathlib.Path,
                                          output_webp_path: pathlib.Path,
                                          target_fps: int) -> List[str]:  # 使用 List
    """构建用于从视频重新生成WebP的FFmpeg命令列表。"""
    command = [
        ffmpeg_exe_path,
        "-y",
        "-i", str(source_video_path),
        "-t", VIDEO_DURATION_FOR_WEBP,
    ]

    command.extend(BASE_WEBP_CONVERSION_OPTIONS_FROM_VIDEO)

    # 简化 -vf 处理：总是添加 fps 滤镜，如果 BASE_WEBP_CONVERSION_OPTIONS_FROM_VIDEO
    # 中已有 -vf，则新的 fps 会被追加。如果想更精确控制，需要解析或调整 BASE_OPTIONS。
    # 一个简单且常见的方法是确保 BASE_WEBP_CONVERSION_OPTIONS_FROM_VIDEO 不包含 fps，然后在这里添加。

    existing_vf_filters = []
    temp_command = []
    vf_value_next = False

    # 提取现有的-vf（如果有）并移除它，以便我们可以重新构建它
    for i, opt in enumerate(command):
        if opt == "-vf":
            if i + 1 < len(command):
                existing_vf_filters.extend(f.strip() for f in command[i + 1].split(',') if f.strip())
            vf_value_next = True  # 标记下一个元素是-vf的值，即使它已经被处理
            continue  # 跳过 "-vf" 本身
        if vf_value_next:
            vf_value_next = False  # 跳过-vf的值
            continue
        temp_command.append(opt)  # 保留其他选项

    command = temp_command

    # 从现有滤镜中移除任何旧的fps设置（如果存在）
    final_filters = [f for f in existing_vf_filters if not f.startswith("fps=")]

    # 添加新的fps设置
    final_filters.append(f"fps={target_fps}")

    if final_filters:
        command.extend(["-vf", ",".join(final_filters)])

    command.append(str(output_webp_path))
    return command


def regenerate_webp_from_source_video(root_dir_path: pathlib.Path, ffmpeg_exe_path: str,
                                      size_threshold_bytes: float, new_fps: int):
    """
    在指定目录及其子目录中查找 WebP 文件，
    如果文件大小超过阈值，则尝试从其对应的原始视频文件重新生成 WebP。
    """
    regenerated_count = 0
    failed_count = 0
    skipped_size_count = 0
    no_source_found_count = 0
    processed_webp_files = 0

    print(f"\n开始在目录 '{root_dir_path}' 及其子目录中扫描 WebP 文件以尝试重新生成...")
    print(f"大小阈值: {get_human_readable_size(int(size_threshold_bytes))} (超过此大小的 WebP 会被尝试替换)")
    print(f"新帧率 (用于重新生成): {new_fps} fps")
    print(f"将从原始视频截取前 {VIDEO_DURATION_FOR_WEBP} 秒。")
    print(f"尝试查找的原始视频扩展名: {', '.join(ORIGINAL_VIDEO_EXTENSIONS)}")
    print("-" * 30)

    for dirpath_str, _, filenames in os.walk(root_dir_path):
        current_dir_path = pathlib.Path(dirpath_str)
        for filename in filenames:
            problematic_webp_path = current_dir_path / filename
            if problematic_webp_path.suffix.lower() == ".webp" and problematic_webp_path.is_file():
                processed_webp_files += 1

                try:
                    original_webp_size_bytes = problematic_webp_path.stat().st_size
                except OSError as e_stat:
                    print(f"\n错误: 无法获取文件 '{problematic_webp_path}' 的大小: {e_stat}, 跳过。")
                    failed_count += 1
                    continue

                print(f"\n发现 WebP 文件: {problematic_webp_path}")
                print(f"  当前 WebP 大小: {get_human_readable_size(original_webp_size_bytes)}")

                if original_webp_size_bytes <= size_threshold_bytes:
                    print(f"  文件大小未超过阈值 {get_human_readable_size(int(size_threshold_bytes))}，跳过重新生成。")
                    skipped_size_count += 1
                    continue

                base_for_lookup = problematic_webp_path.stem
                print(f"  将使用基础名 '{base_for_lookup}' 查找原始视频。")

                source_video_path = find_original_video_file(current_dir_path, base_for_lookup)

                if not source_video_path:
                    print(f"  错误: 未能找到与基础名 '{base_for_lookup}' 对应的原始视频文件。跳过重新生成。")
                    no_source_found_count += 1
                    continue

                print(f"  找到对应的原始视频文件: {source_video_path}")

                output_webp_path = problematic_webp_path

                command_list = build_ffmpeg_command_for_regeneration(
                    ffmpeg_exe_path, source_video_path, output_webp_path, new_fps
                )

                print(f"  执行命令从原始视频重新生成 WebP: {' '.join(command_list)}")

                try:
                    result = subprocess.run(command_list, capture_output=True, text=True, check=False,
                                            encoding='utf-8', errors='replace', timeout=FFMPEG_TIMEOUT_SECONDS)

                    if result.returncode == 0:
                        # 再次检查文件是否存在且非空，因为FFmpeg有时即使返回0也可能没有成功写入
                        if not output_webp_path.exists() or output_webp_path.stat().st_size == 0:
                            print(f"  错误: FFmpeg 声称成功，但新生成的 WebP 文件 '{output_webp_path}' 未找到或为空。")
                            if result.stdout: print(f"    FFmpeg 输出 (stdout):\n{result.stdout.strip()}")
                            if result.stderr: print(f"    FFmpeg 错误 (stderr):\n{result.stderr.strip()}")
                            failed_count += 1
                            continue

                        new_webp_size_bytes = output_webp_path.stat().st_size
                        print(f"  成功从原始视频重新生成 WebP: {output_webp_path}")
                        print(f"    原问题 WebP 大小: {get_human_readable_size(original_webp_size_bytes)}")
                        print(f"    新生成 WebP 大小: {get_human_readable_size(new_webp_size_bytes)}")

                        size_change_percentage = 0.0
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
                        print(f"  错误: FFmpeg 从原始视频重新生成 WebP 失败 (返回码: {result.returncode})")
                        if result.stdout: print(f"    FFmpeg 输出 (stdout):\n{result.stdout.strip()}")
                        if result.stderr: print(f"    FFmpeg 错误 (stderr):\n{result.stderr.strip()}")
                        failed_count += 1

                except subprocess.TimeoutExpired as e_timeout:
                    print(
                        f"  错误: FFmpeg 从原始视频重新生成 WebP 超时 ({FFMPEG_TIMEOUT_SECONDS}s): {source_video_path}")
                    # subprocess.TimeoutExpired.stdout/stderr are bytes, so decode them
                    if e_timeout.stdout: print(
                        f"    FFmpeg 输出 (stdout):\n{e_timeout.stdout.decode('utf-8', 'replace').strip()}")
                    if e_timeout.stderr: print(
                        f"    FFmpeg 错误 (stderr):\n{e_timeout.stderr.decode('utf-8', 'replace').strip()}")
                    failed_count += 1
                except Exception as e_general:
                    print(f"  执行 FFmpeg 从原始视频重新生成 WebP 时发生意外错误: {e_general}")
                    failed_count += 1

    print("\n--- 从原始视频重新生成 WebP 完成 ---")
    if processed_webp_files == 0:
        print("未在指定目录中找到任何 .webp 文件进行处理。")
    else:
        print(f"总共扫描 .webp 文件: {processed_webp_files}")
        print(f"成功重新生成: {regenerated_count} 个 WebP 文件")
        print(f"因大小未超阈值而跳过: {skipped_size_count} 个文件")
        print(f"因未找到对应原始视频而跳过: {no_source_found_count} 个文件")
        print(f"重新生成失败: {failed_count} 个文件")


if __name__ == "__main__":
    print("WebP 文件批量重新生成脚本 (从原始视频)")
    print("======================================")

    if not check_ffmpeg_availability(FFMPEG_PATH):
        input("\nFFmpeg 未正确配置。按 Enter 键退出...")
    else:
        target_root_directory_path = get_valid_folder_path_from_user("请输入包含问题 WebP 文件的根目录路径: ")
        size_threshold_val, target_fps_val = get_regeneration_parameters()

        print("\n警告：此脚本将尝试覆盖原始的 .webp 文件。")
        confirm = input("在继续之前，请确保您已备份重要数据。输入 'yes' 继续: ").strip().lower()
        if confirm == 'yes':
            regenerate_webp_from_source_video(target_root_directory_path, FFMPEG_PATH,
                                              size_threshold_val, target_fps_val)
        else:
            print("操作已取消。")

        input("\n所有操作已完成 (或已取消)。按 Enter 键退出...")