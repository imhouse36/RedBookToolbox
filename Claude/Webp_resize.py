import os
import subprocess
import pathlib
import time
import signal
import threading
from typing import Union, Tuple, List, Optional, Dict

# ==============================================================================
# WebP 文件批量重新生成脚本 (从原始视频)
# ==============================================================================
#
# 主要功能 (Main Purpose):
#   本脚本用于批量处理指定根目录及其子目录下的 WebP 文件。
#   如果一个 WebP 文件的大小超过用户设定的阈值，脚本会尝试找到其对应的原始视频文件，
#   并从该原始视频文件重新生成一个新的 WebP 文件 (通常是截取视频前几秒并应用新的帧率)，
#   用以替换掉原来的、可能存在问题或过大的 WebP 文件。
#
# 工作流程 (Workflow):
#   1. 提示用户输入一个包含 WebP 文件（以及对应原始视频文件）的根目录路径
#   2. 提示用户输入 WebP 文件的大小阈值 (MB) 和重新生成时使用的新目标帧率 (fps)
#   3. 验证用户输入的路径是否为有效文件夹
#   4. 检查 FFmpeg 是否已安装并配置
#   5. 预扫描并显示符合条件的 WebP 文件列表
#   6. 用户确认后开始批量处理
#   7. 递归遍历指定根目录及其所有子目录
#   8. 查找所有超过阈值的 WebP 文件并尝试重新生成
#   9. 实时显示处理进度和统计信息
#
# 注意事项 (Important Notes):
#   - 依赖 FFmpeg：确保 FFmpeg 已正确安装
#   - 文件覆盖：脚本会直接覆盖旧的 .webp 文件，强烈建议备份数据
#   - 原始视频文件命名：脚本假设原始视频文件名与 .webp 文件名（去除 .webp 后缀）部分相同
#   - 错误处理：包含对 FFmpeg 执行错误和超时的基本处理
#
# ==============================================================================

# --- 配置参数 ---
FFMPEG_PATH = "ffmpeg"
ORIGINAL_VIDEO_EXTENSIONS = ['.mp4', '.mov', '.mkv', '.avi', '.wmv', '.flv', '.webm', '.mpeg', '.mpg']

# --- 全局变量用于进程管理 ---
current_ffmpeg_process = None
process_lock = threading.Lock()
# 保持原有的转码和压缩参数不变
BASE_WEBP_CONVERSION_OPTIONS_FROM_VIDEO = [
    "-c:v", "libwebp",
    "-lossless", "0",
    "-q:v", "75",
    "-loop", "0",
    "-an",
]
VIDEO_DURATION_FOR_WEBP = "3"  # 秒
FFMPEG_TIMEOUT_SECONDS = 180


def signal_handler(signum, frame):
    """信号处理函数，用于处理中断信号"""
    global current_ffmpeg_process
    print("\n\n⚠️  接收到终止信号，正在停止当前操作...")
    
    with process_lock:
        if current_ffmpeg_process and current_ffmpeg_process.poll() is None:
            print("🔄 正在终止 FFmpeg 进程...")
            try:
                current_ffmpeg_process.terminate()
                # 等待进程终止，最多等待5秒
                try:
                    current_ffmpeg_process.wait(timeout=5)
                    print("✅ FFmpeg 进程已正常终止")
                except subprocess.TimeoutExpired:
                    print("⚠️  FFmpeg 进程未响应，强制终止...")
                    current_ffmpeg_process.kill()
                    current_ffmpeg_process.wait()
                    print("✅ FFmpeg 进程已强制终止")
            except Exception as e:
                print(f"❌ 终止 FFmpeg 进程时出错: {e}")
            finally:
                current_ffmpeg_process = None
    
    print("🛑 操作已终止")
    exit(0)


def get_human_readable_size(size_bytes: Optional[int]) -> str:
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
    """提示用户输入一个文件夹路径，并验证其有效性"""
    while True:
        print(f"\n{prompt_message}")
        folder_path_str = input(">> ").strip()
        
        # 移除引号
        if folder_path_str.startswith('"') and folder_path_str.endswith('"'):
            folder_path_str = folder_path_str[1:-1]
        elif folder_path_str.startswith("'") and folder_path_str.endswith("'"):
            folder_path_str = folder_path_str[1:-1]

        if not folder_path_str:
            print("❌ 错误：路径不能为空，请重新输入。")
            continue
            
        folder_path_obj = pathlib.Path(folder_path_str)
        if folder_path_obj.is_dir():
            print(f"✅ 路径验证成功: {folder_path_obj.absolute()}")
            return folder_path_obj
        else:
            print(f"❌ 错误：路径 '{folder_path_str}' 不是一个有效的文件夹，或文件夹不存在。")


def check_ffmpeg_availability(ffmpeg_exe_path: str) -> bool:
    """检查FFmpeg是否可用"""
    print("正在检查 FFmpeg 可用性...")
    try:
        result = subprocess.run([ffmpeg_exe_path, "-version"], 
                              capture_output=True, check=True, text=True,
                              encoding='utf-8', errors='replace')
        print(f"✅ FFmpeg 在 '{ffmpeg_exe_path}' 找到并可用。")
        return True
    except FileNotFoundError:
        print(f"❌ 错误: FFmpeg 可执行文件在 '{ffmpeg_exe_path}' 未找到。")
        print("   请确保FFmpeg已安装并添加到系统PATH，或者在脚本中正确配置 FFMPEG_PATH。")
        return False
    except subprocess.CalledProcessError as e:
        print(f"❌ 错误: 执行 FFmpeg -version 时出错 (返回码: {e.returncode}):")
        if e.stdout: print(f"   Stdout: {e.stdout.strip()}")
        if e.stderr: print(f"   Stderr: {e.stderr.strip()}")
        print("   FFmpeg 可能安装不正确。")
        return False
    except Exception as e_gen:
        print(f"❌ 检查 FFmpeg 可用性时发生未知错误: {e_gen}")
        return False


def get_regeneration_parameters() -> Tuple[float, int]:
    """获取用户输入的大小阈值 X (MB) 和新帧率 Y (fps)"""
    print("\n📋 请设置重新生成参数:")
    print("=" * 40)
    
    # 获取大小阈值
    while True:
        try:
            print("\n📏 文件大小阈值设置:")
            size_threshold_mb_str = input("请输入大小阈值 (MB)，超过此大小的 WebP 文件将被重新生成\n>> ").strip()
            size_threshold_mb = float(size_threshold_mb_str)
            if size_threshold_mb <= 0:
                print("❌ 错误：大小阈值必须为正数。")
                continue
            size_threshold_bytes = size_threshold_mb * 1024 * 1024
            print(f"✅ 已设置大小阈值: {get_human_readable_size(int(size_threshold_bytes))}")
            break
        except ValueError:
            print("❌ 错误：请输入一个有效的数字作为大小阈值。")

    # 获取帧率
    while True:
        try:
            print("\n🎬 帧率设置:")
            new_fps_str = input("请输入重新生成 WebP 时使用的目标帧率 (fps)\n>> ").strip()
            new_fps_val = int(new_fps_str)
            if new_fps_val <= 0:
                print("❌ 错误：帧率必须为正整数。")
                continue
            print(f"✅ 已设置目标帧率: {new_fps_val} fps")
            break
        except ValueError:
            print("❌ 错误：请输入一个有效的整数作为帧率。")
    
    return size_threshold_bytes, new_fps_val


def find_original_video_file(webp_dir_path: pathlib.Path, base_name_for_lookup: str) -> Optional[pathlib.Path]:
    """
    根据 WebP 文件的基本名称和目录，查找可能的原始视频文件
    返回找到的原始视频文件的 Path 对象，如果找不到则返回 None
    """
    for video_ext in ORIGINAL_VIDEO_EXTENSIONS:
        potential_video_path = webp_dir_path / (base_name_for_lookup + video_ext)
        if potential_video_path.is_file():
            return potential_video_path
    return None


def build_ffmpeg_command_for_regeneration(ffmpeg_exe_path: str,
                                          source_video_path: pathlib.Path,
                                          output_webp_path: pathlib.Path,
                                          target_fps: int) -> List[str]:
    """构建用于从视频重新生成WebP的FFmpeg命令列表"""
    command = [
        ffmpeg_exe_path,
        "-y",
        "-i", str(source_video_path),
        "-t", VIDEO_DURATION_FOR_WEBP,
    ]

    command.extend(BASE_WEBP_CONVERSION_OPTIONS_FROM_VIDEO)

    # 处理视频滤镜参数
    existing_vf_filters = []
    temp_command = []
    vf_value_next = False

    # 提取现有的-vf（如果有）并移除它，以便我们可以重新构建它
    for i, opt in enumerate(command):
        if opt == "-vf":
            if i + 1 < len(command):
                existing_vf_filters.extend(f.strip() for f in command[i + 1].split(',') if f.strip())
            vf_value_next = True
            continue
        if vf_value_next:
            vf_value_next = False
            continue
        temp_command.append(opt)

    command = temp_command

    # 从现有滤镜中移除任何旧的fps设置（如果存在）
    final_filters = [f for f in existing_vf_filters if not f.startswith("fps=")]

    # 添加新的fps设置
    final_filters.append(f"fps={target_fps}")

    if final_filters:
        command.extend(["-vf", ",".join(final_filters)])

    command.append(str(output_webp_path))
    return command


def scan_webp_files(root_dir_path: pathlib.Path, size_threshold_bytes: float) -> List[Dict]:
    """预扫描符合条件的 WebP 文件"""
    print("\n🔍 正在扫描 WebP 文件...")
    webp_files_info = []
    total_scanned = 0
    
    for dirpath_str, _, filenames in os.walk(root_dir_path):
        current_dir_path = pathlib.Path(dirpath_str)
        for filename in filenames:
            webp_path = current_dir_path / filename
            if webp_path.suffix.lower() == ".webp" and webp_path.is_file():
                total_scanned += 1
                try:
                    file_size = webp_path.stat().st_size
                    if file_size > size_threshold_bytes:
                        base_name = webp_path.stem
                        source_video = find_original_video_file(current_dir_path, base_name)
                        
                        webp_files_info.append({
                            'path': webp_path,
                            'size': file_size,
                            'base_name': base_name,
                            'source_video': source_video
                        })
                except OSError:
                    continue
    
    print(f"✅ 扫描完成: 总共扫描 {total_scanned} 个 WebP 文件")
    print(f"   找到 {len(webp_files_info)} 个超过阈值的 WebP 文件")
    
    return webp_files_info


def display_scan_results(webp_files_info: List[Dict], size_threshold_bytes: float):
    """显示扫描结果"""
    if not webp_files_info:
        print(f"\n📊 扫描结果: 未找到超过 {get_human_readable_size(int(size_threshold_bytes))} 的 WebP 文件。")
        return False
    
    print(f"\n📊 扫描结果汇总:")
    print("=" * 60)
    
    has_source_count = sum(1 for info in webp_files_info if info['source_video'])
    no_source_count = len(webp_files_info) - has_source_count
    
    print(f"📁 总共找到 {len(webp_files_info)} 个超过阈值的 WebP 文件")
    print(f"📁 有源视频文件: {has_source_count} 个")
    print(f"❌ 无源视频文件: {no_source_count} 个")
    
    if no_source_count > 0:
        print(f"\n⚠️  警告: 有 {no_source_count} 个 WebP 文件无法找到对应的源视频文件")
    
    print("\n📄 详细列表:")
    print("-" * 60)
    for i, info in enumerate(webp_files_info, 1):
        status = "✅" if info['source_video'] else "❌"
        print(f"{i:3d}. {status} {info['path'].name} ({get_human_readable_size(info['size'])})")
        if info['source_video']:
            print(f"     源视频: {info['source_video'].name}")
        else:
            print(f"     源视频: 未找到")
        print()
    
    return True


def confirm_processing() -> bool:
    """用户确认是否开始处理"""
    print("\n🚀 开始处理确认:")
    print("=" * 40)
    print("⚠️  注意: 处理过程将直接覆盖现有的 WebP 文件，建议先备份数据！")
    
    while True:
        choice = input("\n是否继续处理? (y/n): ").strip().lower()
        if choice in ['y', 'yes', '是', '继续']:
            return True
        elif choice in ['n', 'no', '否', '取消']:
            return False
        else:
            print("❌ 请输入 y 或 n")


def process_webp_regeneration(webp_files_info: List[Dict], target_fps: int) -> Tuple[int, int]:
    """批量处理 WebP 文件重新生成"""
    success_count = 0
    fail_count = 0
    processable_files = [info for info in webp_files_info if info['source_video']]
    
    if not processable_files:
        print("\n❌ 没有可处理的文件（所有文件都缺少源视频）")
        return 0, 0
    
    print(f"\n🔄 开始处理 {len(processable_files)} 个文件...")
    print("=" * 60)
    
    start_time = time.time()
    
    for index, file_info in enumerate(processable_files, 1):
        webp_path = file_info['path']
        source_video_path = file_info['source_video']
        original_size = file_info['size']
        
        print(f"\n[{index}/{len(processable_files)}] 处理: {webp_path.name}")
        print(f"  原始大小: {get_human_readable_size(original_size)}")
        print(f"  源视频: {source_video_path.name}")
        
        # 构建 FFmpeg 命令
        ffmpeg_command = build_ffmpeg_command_for_regeneration(
            FFMPEG_PATH, source_video_path, webp_path, target_fps
        )
        
        try:
            # 执行 FFmpeg 命令
            print(f"  正在重新生成...")
            
            # 使用 Popen 以便能够控制进程
            with process_lock:
                global current_ffmpeg_process
                current_ffmpeg_process = subprocess.Popen(
                    ffmpeg_command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding='utf-8',
                    errors='replace'
                )
            
            try:
                stdout, stderr = current_ffmpeg_process.communicate(timeout=FFMPEG_TIMEOUT_SECONDS)
                returncode = current_ffmpeg_process.returncode
            finally:
                with process_lock:
                    current_ffmpeg_process = None
            
            if returncode == 0:
                # 检查新文件大小
                try:
                    new_size = webp_path.stat().st_size
                    size_change = new_size - original_size
                    size_change_percent = (size_change / original_size) * 100
                    
                    print(f"  ✅ 成功! 新大小: {get_human_readable_size(new_size)}")
                    if size_change > 0:
                        print(f"     大小增加: +{get_human_readable_size(size_change)} (+{size_change_percent:.1f}%)")
                    else:
                        print(f"     大小减少: {get_human_readable_size(abs(size_change))} ({size_change_percent:.1f}%)")
                    
                    success_count += 1
                except OSError as e:
                    print(f"  ❌ 无法获取新文件大小: {e}")
                    success_count += 1  # 仍然算作成功，因为 FFmpeg 返回成功
            else:
                print(f"  ❌ FFmpeg 失败 (返回码: {returncode})")
                if stderr:
                    print(f"     错误信息: {stderr.strip()[:200]}")
                fail_count += 1
                
        except subprocess.TimeoutExpired:
            print(f"  ❌ 超时 (超过 {FFMPEG_TIMEOUT_SECONDS} 秒)")
            # 终止超时的进程
            with process_lock:
                if current_ffmpeg_process and current_ffmpeg_process.poll() is None:
                    try:
                        current_ffmpeg_process.terminate()
                        try:
                            current_ffmpeg_process.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            current_ffmpeg_process.kill()
                            current_ffmpeg_process.wait()
                    except Exception as e:
                        print(f"     终止进程时出错: {e}")
                    finally:
                        current_ffmpeg_process = None
            fail_count += 1
        except Exception as e:
            print(f"  ❌ 处理失败: {e}")
            fail_count += 1
        
        # 显示进度
        progress = (index / len(processable_files)) * 100
        elapsed_time = time.time() - start_time
        if index > 0:
            avg_time_per_file = elapsed_time / index
            remaining_files = len(processable_files) - index
            estimated_remaining_time = avg_time_per_file * remaining_files
            print(f"  进度: {progress:.1f}% | 剩余时间: {estimated_remaining_time:.1f}秒")
    
    total_time = time.time() - start_time
    print(f"\n🏁 处理完成! 总用时: {total_time:.2f}秒")
    
    return success_count, fail_count


def display_final_results(success_count: int, fail_count: int, total_files: int):
    """显示最终处理结果"""
    print("\n" + "=" * 60)
    print("📊 最终统计结果")
    print("=" * 60)
    print(f"📁 总共扫描的 WebP 文件: {total_files}")
    print(f"✅ 成功重新生成: {success_count} 个")
    print(f"❌ 处理失败: {fail_count} 个")
    
    if success_count > 0:
        success_rate = (success_count / (success_count + fail_count)) * 100 if (success_count + fail_count) > 0 else 0
        print(f"📈 成功率: {success_rate:.1f}%")
    
    if fail_count > 0:
        print(f"\n⚠️  建议检查失败的文件，可能原因:")
        print(f"   • 源视频文件损坏或格式不支持")
        print(f"   • 磁盘空间不足")
        print(f"   • 文件权限问题")
        print(f"   • FFmpeg 配置问题")


def main():
    """主函数"""
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("🎬 WebP 文件批量重新生成工具")
    print("" + "=" * 80)
    print("功能: 从原始视频重新生成超过指定大小的 WebP 文件")
    print("注意: 操作将直接覆盖现有文件，建议先备份！")
    print("" + "=" * 80)
    
    try:
        # 1. 检查 FFmpeg 可用性
        if not check_ffmpeg_availability(FFMPEG_PATH):
            print("\n❌ 程序终止: FFmpeg 不可用")
            return
        
        # 2. 从标准输入获取参数（适用于Web环境）
        try:
            # 从标准输入读取参数（按服务器传递顺序：path, size_threshold, fps）
            path_str = input().strip()
            size_threshold_str = input().strip()
            fps_str = input().strip()
            
            # 验证路径
            root_dir_path = pathlib.Path(path_str)
            if not root_dir_path.exists() or not root_dir_path.is_dir():
                raise ValueError(f"路径不存在或不是目录: {path_str}")
            
            # 验证大小阈值
            size_threshold_mb = float(size_threshold_str)
            if size_threshold_mb <= 0:
                raise ValueError("大小阈值必须为正数")
            size_threshold_bytes = size_threshold_mb * 1024 * 1024
            
            # 验证帧率
            target_fps = int(fps_str)
            if target_fps <= 0:
                raise ValueError("帧率必须为正整数")
                
            print(f"✅ 参数设置成功:")
            print(f"   路径: {root_dir_path.absolute()}")
            print(f"   大小阈值: {get_human_readable_size(int(size_threshold_bytes))}")
            print(f"   目标帧率: {target_fps} fps")
            
        except (ValueError, EOFError) as e:
            print(f"❌ 参数读取错误: {e}")
            return
        
        # 3. 扫描文件
        webp_files_info = scan_webp_files(root_dir_path, size_threshold_bytes)
        
        # 4. 显示扫描结果
        if not display_scan_results(webp_files_info, size_threshold_bytes):
            print("\n✅ 没有需要处理的文件，程序结束。")
            return
        
        # 5. 自动确认处理（Web环境下不需要用户交互）
        print("\n🚀 开始自动处理...")
        
        # 6. 开始处理
        success_count, fail_count = process_webp_regeneration(webp_files_info, target_fps)
        
        # 7. 显示最终结果
        display_final_results(success_count, fail_count, len(webp_files_info))
        
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断操作 (Ctrl+C)")
        # 确保清理当前进程
        with process_lock:
            if current_ffmpeg_process and current_ffmpeg_process.poll() is None:
                try:
                    current_ffmpeg_process.terminate()
                    current_ffmpeg_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    current_ffmpeg_process.kill()
                    current_ffmpeg_process.wait()
                except Exception:
                    pass
                finally:
                    current_ffmpeg_process = None
        print("程序已停止。")
    except Exception as e:
        print(f"\n❌ 程序执行过程中发生未知错误: {e}")
        # 确保清理当前进程
        with process_lock:
            if current_ffmpeg_process and current_ffmpeg_process.poll() is None:
                try:
                    current_ffmpeg_process.terminate()
                    current_ffmpeg_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    current_ffmpeg_process.kill()
                    current_ffmpeg_process.wait()
                except Exception:
                    pass
                finally:
                    current_ffmpeg_process = None
        print("建议检查输入参数和系统配置。")


if __name__ == "__main__":
    main()
    