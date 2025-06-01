# -*- coding: utf-8 -*-
# 主要功能:
#   将指定"素材"文件夹内的图片文件，随机复制到"发布"文件夹的各个子目录中。
#
# 工作过程:
#   1. 记录开始时间。
#   2. 提示用户输入"素材"文件夹路径和"发布"文件夹路径。
#   3. 校验输入的路径是否存在且为文件夹。
#   4. 获取"素材"文件夹下的所有子目录列表（这些是图片来源的分类）。
#   5. 获取"发布"文件夹下的所有子目录列表（这些是图片要复制到的目标位置）。
#   6. 初始化总复制文件计数器。
#   7. 对于"发布"文件夹中的每一个子目录：
#      a. 遍历"素材"文件夹的每一个子目录。
#      b. 从当前"素材"子目录中随机选择一张图片。
#      c. 将选中的图片复制到当前的"发布"子目录中，成功则总计数器加一。
#   8. 确保每个"发布"子目录中复制的图片数量等于"素材"文件夹中子目录的数量。
#      如果某个"素材"子目录中没有图片，则会跳过该类别，并在最终提示。
#   9. 记录结束时间，计算总用时。
#  10. 输出总共复制的文件数量和总执行时间。
#
# 达成的结果:
#   "发布"文件夹的每个子目录中，都会包含从"素材"文件夹的每个子目录中随机抽取的一张图片。
#   因此，每个"发布"子目录中的图片数量理论上应等于"素材"文件夹中子目录的数量。
#   脚本执行完毕后，会显示本次操作复制的总文件数和所用时间。
#
# 注意事项:
#   - 脚本仅处理常见图片格式（jpg, jpeg, png, gif, webp, bmp）。如需其他格式，请修改 `image_extensions`。
#   - 如果"素材"的某个子目录中没有图片文件，则在处理对应的"发布"子目录时，该素材类别将被跳过。
#   - 如果"发布"子目录中已存在同名文件，脚本会智能处理文件名冲突，避免覆盖现有文件。
#   - 脚本会打印详细的操作信息和可能的警告或错误。
#   - 请确保对"素材"文件夹有读取权限，对"发布"文件夹及其子目录有写入权限。
#   - 支持用户中断操作（Ctrl+C）优雅退出。

import os
import shutil
import random
import time
import sys
from pathlib import Path

# Python 3.7兼容的类型提示导入
try:
    from typing import List, Tuple, Optional
except ImportError:
    # 如果typing模块导入失败，定义空的类型提示
    List = list
    Tuple = tuple
    Optional = type(None)


def get_valid_folder_path_from_user(prompt_message: str) -> Path:
    """
    提示用户输入一个文件夹路径，并持续请求直到输入一个有效的文件夹路径。

    参数:
        prompt_message (str): 显示给用户的提示信息。

    返回:
        Path: 用户输入的有效文件夹路径对象。
    """
    while True:
        try:
            folder_path_str = input(prompt_message).strip()
            if not folder_path_str:
                print("错误：未输入路径。请重新输入。")
                continue
            
            folder_path = Path(folder_path_str)
            if folder_path.exists() and folder_path.is_dir():
                return folder_path
            else:
                print(f"错误：路径 '{folder_path}' 不存在或不是一个文件夹。请重新输入。")
        except KeyboardInterrupt:
            print("\n用户取消操作。")
            sys.exit(0)
        except Exception as e:
            print(f"错误：处理路径时发生异常: {e}。请重新输入。")


def get_subdirectories(base_path: Path, folder_type: str):
    """
    获取指定目录下的所有子目录列表。

    参数:
        base_path (Path): 基础目录路径。
        folder_type (str): 文件夹类型描述（用于错误提示）。

    返回:
        list: 子目录名称列表。
    """
    try:
        subdirs = [
            item.name for item in base_path.iterdir()
            if item.is_dir()
        ]
        return subdirs
    except OSError as e:
        print(f"错误：无法读取{folder_type}文件夹 '{base_path}' 的内容: {e}")
        return []


def get_image_files_in_directory(directory_path: Path, image_extensions):
    """
    获取指定目录下的所有图片文件列表。

    参数:
        directory_path (Path): 目录路径。
        image_extensions: 支持的图片文件扩展名元组。

    返回:
        list: 图片文件名列表。
    """
    try:
        image_files = [
            item.name for item in directory_path.iterdir()
            if item.is_file() and item.suffix.lower() in image_extensions
        ]
        return image_files
    except OSError as e:
        print(f"  错误: 无法读取目录 '{directory_path}' 的内容: {e}")
        return []


def generate_unique_filename(target_path: Path, original_filename: str) -> str:
    """
    生成唯一的文件名，避免文件名冲突。

    参数:
        target_path (Path): 目标目录路径。
        original_filename (str): 原始文件名。

    返回:
        str: 唯一的文件名。
    """
    target_file_path = target_path / original_filename
    
    if not target_file_path.exists():
        return original_filename
    
    # 分离文件名和扩展名
    file_stem = Path(original_filename).stem
    file_suffix = Path(original_filename).suffix
    
    counter = 1
    while True:
        new_filename = f"{file_stem}_{counter}{file_suffix}"
        new_target_path = target_path / new_filename
        if not new_target_path.exists():
            return new_filename
        counter += 1
        
        # 防止无限循环
        if counter > 9999:
            timestamp = int(time.time())
            return f"{file_stem}_{timestamp}{file_suffix}"


def copy_file_safely(source_path: Path, target_path: Path, filename: str):
    """
    安全地复制文件，处理文件名冲突。

    参数:
        source_path (Path): 源文件路径。
        target_path (Path): 目标目录路径。
        filename (str): 文件名。

    返回:
        tuple: (是否成功, 最终文件名, 错误信息)
    """
    try:
        # 生成唯一文件名
        unique_filename = generate_unique_filename(target_path, filename)
        
        source_file_path = source_path / filename
        target_file_path = target_path / unique_filename
        
        # 复制文件
        shutil.copy2(source_file_path, target_file_path)
        
        return True, unique_filename, ""
    except Exception as e:
        return False, filename, str(e)


def copy_random_images_optimized():
    """
    优化版本的图片随机复制函数，执行图片随机复制逻辑，并在结束时报告统计信息。
    支持两种输入模式：
    1. 交互式输入模式（命令行直接运行）
    2. 标准输入模式（Web环境或管道输入）

    返回:
        tuple: (是否全部成功, 成功复制的文件数量, 总尝试复制的文件数量)
    """
    print("图片随机复制工具 (Claude4优化版)")
    print("=" * 60)
    
    start_time = time.time()
    total_files_copied = 0
    total_files_attempted = 0
    failed_operations = []
    
    try:
        # 1. 智能检测输入模式并获取路径
        print("\n步骤 1: 获取文件夹路径")
        
        # 检测是否为非交互模式（Web环境或管道输入）
        is_non_interactive = hasattr(sys.stdin, 'isatty') and not sys.stdin.isatty()
        
        if is_non_interactive:
            # 非交互模式：从标准输入读取参数（适用于Web环境）
            print("🌐 检测到Web环境，使用标准输入模式")
            try:
                # 从标准输入读取参数（按服务器传递顺序：source_path, target_path）
                source_path_str = input().strip()
                target_path_str = input().strip()
                
                source_base_path = Path(source_path_str)
                target_base_path = Path(target_path_str)
                
                if not source_base_path.exists() or not source_base_path.is_dir():
                    raise ValueError(f"素材文件夹路径不存在或不是目录: {source_path_str}")
                if not target_base_path.exists() or not target_base_path.is_dir():
                    raise ValueError(f"发布文件夹路径不存在或不是目录: {target_path_str}")
                    
            except (ValueError, EOFError) as e:
                print(f"❌ 参数读取错误: {e}")
                return False, 0, 0
        else:
            # 交互模式：使用原有的交互式输入函数
            print("💻 检测到命令行环境，使用交互式输入模式")
            source_base_path = get_valid_folder_path_from_user(
                "请输入素材文件夹的路径: "
            )
            target_base_path = get_valid_folder_path_from_user(
                "请输入发布文件夹的路径: "
            )
        
        print(f"\n✅ 配置确认:")
        print(f"- 素材文件夹: {source_base_path}")
        print(f"- 发布文件夹: {target_base_path}")
        
        # 定义支持的图片文件扩展名（包含.gif格式）
        image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp')
        print(f"- 支持的图片格式: {', '.join(image_extensions)}")
        
        # 2. 获取"素材"文件夹下的所有子目录
        print("\n步骤 2: 扫描素材文件夹")
        source_subfolders = get_subdirectories(source_base_path, "素材")
        
        if not source_subfolders:
            print(f'警告："素材"文件夹 \'{source_base_path}\' 中没有找到任何子目录。脚本无法继续。')
            return False, 0, 0
        
        print(f"找到 {len(source_subfolders)} 个素材类别: {', '.join(source_subfolders)}")
        
        # 3. 获取"发布"文件夹下的所有子目录
        print("\n步骤 3: 扫描发布文件夹")
        target_subfolders = get_subdirectories(target_base_path, "发布")
        
        if not target_subfolders:
            print(f'警告："发布"文件夹 \'{target_base_path}\' 中没有找到任何子目录。脚本无法继续。')
            return False, 0, 0
        
        print(f"找到 {len(target_subfolders)} 个发布目标: {', '.join(target_subfolders)}")
        
        # 4. 开始复制过程
        print(f"\n步骤 4: 开始图片复制任务")
        print(f"{'='*60}")
        
        total_operations = len(target_subfolders) * len(source_subfolders)
        current_operation = 0
        
        # 遍历"发布"文件夹的每个子目录
        for target_index, target_sub_name in enumerate(target_subfolders, 1):
            current_target_dir_path = target_base_path / target_sub_name
            print(f"\n[{target_index}/{len(target_subfolders)}] 处理发布目录: '{target_sub_name}'")
            
            copied_images_count_for_this_target = 0
            skipped_categories = []
            
            # 遍历"素材"文件夹的每个子目录
            for source_sub_name in source_subfolders:
                current_operation += 1
                progress = (current_operation / total_operations) * 100
                
                current_source_category_path = source_base_path / source_sub_name
                
                # 获取当前素材类别目录下的所有图片文件
                available_images = get_image_files_in_directory(
                    current_source_category_path, image_extensions
                )
                
                if not available_images:
                    print(f"  [进度: {progress:.1f}%] 跳过类别 '{source_sub_name}' - 无图片文件")
                    skipped_categories.append(source_sub_name)
                    continue
                
                # 随机选择一张图片
                chosen_image_name = random.choice(available_images)
                total_files_attempted += 1
                
                # 安全复制文件
                success, final_filename, error_msg = copy_file_safely(
                    current_source_category_path, current_target_dir_path, chosen_image_name
                )
                
                if success:
                    if final_filename != chosen_image_name:
                        print(f"  [进度: {progress:.1f}%] '{source_sub_name}/{chosen_image_name}' → '{target_sub_name}/{final_filename}' (重命名避免冲突)")
                    else:
                        print(f"  [进度: {progress:.1f}%] '{source_sub_name}/{chosen_image_name}' → '{target_sub_name}/{final_filename}'")
                    copied_images_count_for_this_target += 1
                    total_files_copied += 1
                else:
                    error_info = f"复制 '{source_sub_name}/{chosen_image_name}' 到 '{target_sub_name}' 失败: {error_msg}"
                    print(f"  [进度: {progress:.1f}%] 错误: {error_info}")
                    failed_operations.append(error_info)
            
            # 输出当前目标目录的统计信息
            print(f"  ✓ 目标目录 '{target_sub_name}' 处理完成")
            print(f"    - 预期复制数量: {len(source_subfolders)}")
            print(f"    - 实际复制数量: {copied_images_count_for_this_target}")
            if skipped_categories:
                print(f"    - 跳过的类别: {', '.join(skipped_categories)}")
        
        # 5. 输出最终统计报告
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"\n{'='*60}")
        print("图片复制任务完成统计报告:")
        print(f"{'='*60}")
        print(f"总尝试复制文件数量: {total_files_attempted}")
        print(f"成功复制文件数量: {total_files_copied}")
        print(f"失败操作数量: {len(failed_operations)}")
        print(f"成功率: {(total_files_copied/total_files_attempted*100):.1f}%" if total_files_attempted > 0 else "成功率: N/A")
        print(f"总执行时间: {execution_time:.2f} 秒")
        print(f"平均复制速度: {total_files_copied/execution_time:.2f} 文件/秒" if execution_time > 0 else "平均复制速度: N/A")
        
        if failed_operations:
            print(f"\n失败操作详情:")
            for i, error in enumerate(failed_operations, 1):
                print(f"  {i}. {error}")
        
        print(f"{'='*60}")
        
        return len(failed_operations) == 0, total_files_copied, total_files_attempted
        
    except KeyboardInterrupt:
        print("\n\n用户中断程序执行。")
        return False, total_files_copied, total_files_attempted
    except Exception as e:
        print(f"\n程序执行过程中发生意外错误: {e}")
        print("请检查输入参数和文件权限后重试。")
        return False, total_files_copied, total_files_attempted


def main():
    """
    主函数：控制程序的执行流程。
    """
    try:
        # 记录脚本开始时间
        script_start_time = time.time()
        
        # 执行图片复制任务
        success, copied_count, attempted_count = copy_random_images_optimized()
        
        # 输出脚本总执行时间
        script_end_time = time.time()
        total_script_time = script_end_time - script_start_time
        
        if success:
            print("\n🎉 所有图片复制任务完成！")
        else:
            print(f"\n⚠️  图片复制任务部分完成，成功复制 {copied_count}/{attempted_count} 个文件。")
        
        print(f"\n脚本总执行时间: {total_script_time:.2f} 秒")
        print("程序执行完毕。")
        
    except KeyboardInterrupt:
        print("\n\n用户中断程序执行。")
    except Exception as e:
        print(f"\n程序执行过程中发生意外错误: {e}")
        print("请检查输入参数和文件权限后重试。")


if __name__ == "__main__":
    main()