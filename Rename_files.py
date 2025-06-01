# -*- coding: utf-8 -*-

# ==============================================================================
# 脚本功能核心备注 (Script Core Functionality Notes)
# ==============================================================================
#
# 脚本名称 (Script Name):
#   Rename_files_Claude4.py (Claude4优化版)
#
# 主要目的 (Main Purpose):
#   本脚本用于递归地重命名指定顶层文件夹及其所有子文件夹内的文件。
#   新的命名规则为：当前文件所在文件夹的名称_数字编号.原文件扩展名。
#
# 工作流程 (Workflow):
#   采用两阶段重命名策略以确保稳健性，针对每个被处理的文件夹独立执行。
#
#   遍历阶段:
#     1. 提示用户输入要操作的顶层文件夹路径
#     2. 验证用户输入的路径是否为有效文件夹
#     3. 使用 os.walk() 递归遍历顶层文件夹及其所有子文件夹
#     4. 显示详细的处理进度和统计信息
#     5. 生成最终的处理报告
#
#   对于 os.walk() 发现的每一个文件夹 (dirpath):
#     A. 准备阶段:
#        1. 获取当前文件夹 (dirpath) 的基本名称
#        2. 如果无法获取有效文件夹名称，则跳过该目录下的文件处理
#
#     B. 阶段 1: 为当前文件夹下的文件添加临时后缀
#        1. 列出当前文件夹中的所有文件，并按原文件名排序
#        2. 为每个文件生成临时文件名，附加独特后缀
#        3. 将文件重命名为临时名称
#        4. 收集所有成功生成的临时文件名
#
#     C. 阶段 2: 将临时文件重命名为最终格式
#        1. 初始化数字计数器（每个文件夹独立）
#        2. 遍历临时文件列表
#        3. 构建新文件名：{文件夹名称}_{计数器}{原始扩展名}
#        4. 将临时文件重命名为最终文件名
#        5. 更新统计信息
#
# 优化特性 (Optimization Features):
#   - 添加了类型提示，提高代码可读性和IDE支持
#   - 改进了错误处理机制，提供更详细的错误信息
#   - 增强了用户体验，包括进度显示和配置确认
#   - 添加了详细的统计信息和性能监控
#   - 支持用户中断操作（Ctrl+C）优雅退出
#   - 改进了文件验证和安全性检查
#   - 添加了处理时间统计和速度监控
#
# 达成的结果 (Results):
#   指定顶层文件夹及其所有子文件夹内的文件，都会根据其所在的直接父文件夹的名称进行重命名。
#   例如："ProjectX/a.txt" -> "ProjectX/ProjectX_1.txt"
#         "ProjectX/Docs/b.doc" -> "ProjectX/Docs/Docs_1.doc"
#
# 注意事项 (Important Notes):
#   - 此脚本会直接修改文件名，操作不可逆。强烈建议在操作前备份重要数据
#   - 临时后缀被设计为相对独特，避免冲突
#   - 如果脚本在重命名过程中失败，文件可能保留原始名称或临时名称
#   - 脚本兼容 Python 3.7 及以上版本
#   - 支持用户中断操作（Ctrl+C）优雅退出
#
# ==============================================================================

import os
import time
import sys
from pathlib import Path

# Python 3.7兼容的类型提示导入
try:
    from typing import Tuple, Optional, List
except ImportError:
    # 如果typing模块导入失败，定义空的类型提示
    Tuple = tuple
    Optional = type(None)
    List = list


# 临时文件后缀常量
TEMP_SUFFIX = ".__rename_temp_process__"


def get_valid_folder_path_from_user(prompt_message: str) -> Path:
    """
    获取用户输入的有效文件夹路径。
    
    参数:
        prompt_message (str): 提示用户输入的消息。
    
    返回:
        Path: 有效的文件夹路径对象。
    """
    while True:
        try:
            user_input = input(prompt_message).strip()
            
            if not user_input:
                print("错误：未输入路径，请重新输入。")
                continue
                
            # 处理引号包围的路径
            if user_input.startswith('"') and user_input.endswith('"'):
                user_input = user_input[1:-1]
            elif user_input.startswith("'") and user_input.endswith("'"):
                user_input = user_input[1:-1]
            
            folder_path = Path(user_input)
            
            if not folder_path.exists():
                print(f"错误：路径 '{folder_path}' 不存在。请重新输入。")
                continue
                
            if not folder_path.is_dir():
                print(f"错误：路径 '{folder_path}' 不是一个有效的文件夹。请重新输入。")
                continue
                
            return folder_path
            
        except KeyboardInterrupt:
            print("\n操作已由用户中止。")
            sys.exit(0)
        except Exception as e:
            print(f"错误：处理路径时发生异常: {e}。请重新输入。")


def get_folder_prefix_name(dirpath: str) -> Optional[str]:
    """
    获取文件夹的前缀名称，用于文件重命名。
    
    参数:
        dirpath (str): 文件夹路径。
    
    返回:
        str 或 None: 文件夹前缀名称，如果无法获取则返回None。
    """
    current_folder_name = os.path.basename(dirpath)
    
    # 处理驱动器根目录的特殊情况
    if not current_folder_name:
        drive, tail = os.path.splitdrive(dirpath)
        # 检查是否是驱动器根目录
        if dirpath == drive or (drive and not tail) or (drive and tail in ('\\', '/')):
            cleaned_drive_name = drive.replace(":", "").replace("\\", "").replace("/", "")
            if cleaned_drive_name:
                return f"{cleaned_drive_name}_root_files"
        return None
    
    return current_folder_name


def process_stage_one_add_temp_suffix(dirpath: str, filenames: list) -> list:
    """
    阶段1：为当前文件夹下的文件添加临时后缀。
    
    参数:
        dirpath (str): 当前文件夹路径。
        filenames (list): 文件名列表。
    
    返回:
        list: 成功生成的临时文件名列表。
    """
    try:
        # 只处理当前目录下的文件，排除已有临时后缀的文件
        initial_files = sorted([
            f for f in filenames
            if os.path.isfile(os.path.join(dirpath, f)) and not f.endswith(TEMP_SUFFIX)
        ])
    except OSError as e:
        print(f"  错误: 无法读取文件夹 '{dirpath}' 的内容以准备阶段1: {e}")
        return []

    if not initial_files:
        print(f"  文件夹 '{dirpath}' 中没有符合条件的文件可进行第一阶段重命名。")
        return []

    temp_files_generated = []
    
    for original_filename in initial_files:
        original_full_path = os.path.join(dirpath, original_filename)
        temp_filename = original_filename + TEMP_SUFFIX
        temp_full_path = os.path.join(dirpath, temp_filename)

        try:
            if os.path.exists(temp_full_path):
                print(f"    警告 (阶段1): 目标临时文件名 '{temp_filename}' 已存在。")
                print(f"    跳过文件 '{original_filename}' 的第一阶段重命名。")
                if temp_filename.endswith(TEMP_SUFFIX):
                    temp_files_generated.append(temp_filename)
                continue

            os.rename(original_full_path, temp_full_path)
            temp_files_generated.append(temp_filename)
            
        except OSError as e:
            print(f"    错误 (阶段1): 重命名 '{original_filename}' 失败: {e}")
        except Exception as e:
            print(f"    未知错误 (阶段1): 重命名 '{original_filename}' 失败: {e}")
    
    return temp_files_generated


def process_stage_two_final_rename(dirpath: str, folder_prefix: str) -> Tuple[int, int]:
    """
    阶段2：将临时文件重命名为最终格式。
    
    参数:
        dirpath (str): 当前文件夹路径。
        folder_prefix (str): 文件夹前缀名称。
    
    返回:
        tuple: (成功重命名的文件数, 失败的文件数)
    """
    try:
        # 重新扫描当前目录以获取所有临时文件
        temp_files = sorted([
            f for f in os.listdir(dirpath)
            if os.path.isfile(os.path.join(dirpath, f)) and f.endswith(TEMP_SUFFIX)
        ])
    except OSError as e:
        print(f"  错误: 无法读取文件夹 '{dirpath}' 的内容以准备阶段2: {e}")
        return 0, 0

    if not temp_files:
        print(f"  文件夹 '{dirpath}' 中没有临时文件可进行第二阶段重命名。")
        return 0, 0

    file_counter = 1
    renamed_count = 0
    failed_count = 0

    for temp_filename in temp_files:
        temp_full_path = os.path.join(dirpath, temp_filename)

        if not temp_filename.endswith(TEMP_SUFFIX):
            print(f"    警告 (阶段2): 文件 '{temp_filename}' 没有预期的临时后缀。跳过。")
            failed_count += 1
            continue

        # 提取原始扩展名
        original_name_part = temp_filename[:-len(TEMP_SUFFIX)]
        _, original_ext = os.path.splitext(original_name_part)

        # 构建最终文件名
        final_filename = f"{folder_prefix}_{file_counter}{original_ext}"
        final_full_path = os.path.join(dirpath, final_filename)

        try:
            if os.path.exists(final_full_path):
                print(f"    警告 (阶段2): 目标文件名 '{final_filename}' 已存在。")
                print(f"    跳过重命名 '{temp_filename}'。")
                failed_count += 1
                continue

            os.rename(temp_full_path, final_full_path)
            print(f"    已重命名: '{temp_filename}' -> '{final_filename}'")
            renamed_count += 1
            file_counter += 1
            
        except OSError as e:
            print(f"    错误 (阶段2): 重命名 '{temp_filename}' 到 '{final_filename}' 失败: {e}")
            print(f"    文件 '{temp_filename}' 可能仍带有临时后缀。")
            failed_count += 1
        except Exception as e:
            print(f"    未知错误 (阶段2): 重命名 '{temp_filename}' 到 '{final_filename}' 失败: {e}")
            failed_count += 1

    return renamed_count, failed_count


def rename_files_recursively_optimized() -> Tuple[bool, int, int, int]:
    """
    主函数：执行递归的两阶段文件重命名逻辑（优化版）。
    
    返回:
        tuple: (是否全部成功, 成功处理的文件数, 失败的文件数, 处理的文件夹数)
    """
    print("递归文件重命名工具 (Claude4优化版)")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        # 1. 获取用户输入的文件夹路径
        print("\n步骤 1: 获取文件夹路径")
        top_level_folder_path = get_valid_folder_path_from_user(
            "请输入要重命名文件的顶层文件夹路径: "
        )
        
        print(f"\n配置确认:")
        print(f"- 目标文件夹: {top_level_folder_path}")
        print(f"- 重命名规则: {{文件夹名称}}_{{序号}}{{原扩展名}}")
        print(f"- 处理方式: 递归处理所有子文件夹")
        print(f"- 临时后缀: {TEMP_SUFFIX}")
        
        # 2. 用户确认
        print(f"\n步骤 2: 确认处理")
        print("⚠️  警告：此操作将直接修改文件名，操作不可逆！建议先备份重要数据。")
        
        try:
            confirm = input("\n确认开始重命名操作吗？(y/N): ").strip().lower()
            if confirm not in ['y', 'yes', '是']:
                print("操作已取消")
                return False, 0, 0, 0
        except KeyboardInterrupt:
            print("\n操作已由用户中止")
            return False, 0, 0, 0
        
        # 3. 开始递归处理
        print(f"\n步骤 3: 开始递归处理")
        print("=" * 60)
        
        total_renamed_files = 0
        total_failed_files = 0
        processed_folders = 0
        failed_folders = []
        
        # 使用 os.walk 进行递归遍历
        for dirpath, dirnames, filenames in os.walk(str(top_level_folder_path), topdown=True):
            try:
                # 获取文件夹前缀名称
                folder_prefix = get_folder_prefix_name(dirpath)
                
                if folder_prefix is None:
                    print(f"\n警告: 无法从路径 '{dirpath}' 获取有效的文件夹名称。跳过此目录。")
                    failed_folders.append(dirpath)
                    continue
                
                print(f"\n--- 正在处理文件夹: '{dirpath}' (前缀: '{folder_prefix}') ---")
                processed_folders += 1
                
                # 阶段 1: 添加临时后缀
                temp_files = process_stage_one_add_temp_suffix(dirpath, filenames)
                
                # 阶段 2: 最终重命名
                renamed_count, failed_count = process_stage_two_final_rename(dirpath, folder_prefix)
                
                total_renamed_files += renamed_count
                total_failed_files += failed_count
                
                if renamed_count > 0:
                    print(f"  ✅ 在文件夹 '{os.path.basename(dirpath)}' 中成功重命名 {renamed_count} 个文件")
                elif failed_count > 0:
                    print(f"  ❌ 在文件夹 '{os.path.basename(dirpath)}' 中处理失败 {failed_count} 个文件")
                else:
                    print(f"  ℹ️  文件夹 '{os.path.basename(dirpath)}' 中没有需要处理的文件")
                    
            except KeyboardInterrupt:
                print("\n\n操作被用户中断")
                break
            except Exception as e:
                print(f"\n处理文件夹 '{dirpath}' 时发生未预期的错误: {e}")
                failed_folders.append(dirpath)
                total_failed_files += 1
        
        # 4. 生成处理报告
        execution_time = time.time() - start_time
        
        print("\n" + "=" * 60)
        print("📊 处理完成 - 统计报告")
        print("=" * 60)
        print(f"📁 处理根目录: {top_level_folder_path}")
        print(f"📂 处理的文件夹数: {processed_folders} 个")
        print(f"✅ 成功重命名文件: {total_renamed_files} 个")
        print(f"❌ 处理失败文件: {total_failed_files} 个")
        print(f"⏱️  总执行时间: {execution_time:.2f} 秒")
        
        if total_renamed_files > 0:
            print(f"📈 平均处理速度: {total_renamed_files/execution_time:.2f} 文件/秒" if execution_time > 0 else "📈 平均处理速度: N/A")
        
        if failed_folders:
            print(f"\n⚠️  处理失败的文件夹:")
            for failed_folder in failed_folders:
                print(f"   - {failed_folder}")
        
        print("=" * 60)
        
        return total_failed_files == 0, total_renamed_files, total_failed_files, processed_folders
        
    except KeyboardInterrupt:
        print("\n\n操作被用户中断")
        return False, 0, 0, 0
    except Exception as e:
        print(f"\n递归重命名过程中发生错误: {e}")
        return False, 0, 0, 0


def main():
    """
    主函数：协调整个文件重命名流程。
    """
    try:
        print("🚀 启动递归文件重命名工具...")
        
        success, renamed_count, failed_count, folder_count = rename_files_recursively_optimized()
        
        if success and renamed_count > 0:
            print("\n🎉 所有文件重命名成功！")
        elif renamed_count > 0:
            print(f"\n⚠️  部分文件重命名完成，{failed_count} 个文件处理失败")
        else:
            print("\n❌ 没有文件被成功重命名")
            
    except KeyboardInterrupt:
        print("\n\n👋 程序被用户中断，感谢使用！")
    except Exception as e:
        print(f"\n💥 程序运行时发生未预期的错误: {e}")
        print("请检查环境配置或联系技术支持")
    finally:
        print("\n程序结束")


if __name__ == "__main__":
    main()