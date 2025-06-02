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
from typing import List, Tuple, Optional
# 添加多线程支持
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Python 3.7兼容的类型提示导入
try:
    from typing import List, Tuple, Optional
except ImportError:
    # 如果typing模块导入失败，定义空的类型提示
    List = list
    Tuple = tuple
    Optional = type(None)

# 线程锁用于线程安全的计数器
copy_lock = threading.Lock()
copy_stats = {'total': 0, 'success': 0, 'failed': 0}

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


def copy_file_safely_threaded(args: tuple) -> tuple:
    """
    线程安全的文件复制函数
    
    参数:
        args: (source_path, target_path, filename, thread_id)
    
    返回:
        tuple: (是否成功, 最终文件名, 错误信息, 线程ID)
    """
    source_path, target_path, filename, thread_id = args
    
    try:
        # 生成唯一文件名
        unique_filename = generate_unique_filename(target_path, filename)
        
        source_file_path = source_path / filename
        target_file_path = target_path / unique_filename
        
        # 复制文件
        shutil.copy2(source_file_path, target_file_path)
        
        # 线程安全的统计更新
        with copy_lock:
            copy_stats['success'] += 1
            
        return True, unique_filename, "", thread_id
        
    except Exception as e:
        with copy_lock:
            copy_stats['failed'] += 1
        return False, filename, str(e), thread_id


def copy_random_images_parallel(source_folders: List[Path], target_folders: List[Path], 
                               max_workers: int = 4) -> Tuple[bool, int, int]:
    """
    并行复制图片文件，提升处理速度
    
    参数:
        source_folders: 素材文件夹列表
        target_folders: 目标文件夹列表  
        max_workers: 最大工作线程数
    
    返回:
        tuple: (是否全部成功, 成功复制数, 尝试复制数)
    """
    print(f"\n🚀 使用 {max_workers} 个线程并行复制图片...")
    
    # 重置统计
    global copy_stats
    copy_stats = {'total': 0, 'success': 0, 'failed': 0}
    
    # 准备复制任务列表
    copy_tasks = []
    
    for target_folder in target_folders:
        for source_folder in source_folders:
            # 获取源文件夹中的图片文件
            image_files = [f for f in source_folder.iterdir() 
                         if f.is_file() and f.suffix.lower() in image_extensions]
            
            if image_files:
                # 随机选择一张图片
                selected_image = random.choice(image_files)
                copy_tasks.append((source_folder, target_folder, selected_image.name, len(copy_tasks)))
    
    copy_stats['total'] = len(copy_tasks)
    
    if not copy_tasks:
        print("⚠️ 没有找到可复制的图片文件")
        return False, 0, 0
    
    print(f"📋 准备复制 {len(copy_tasks)} 个文件...")
    
    # 使用线程池并行执行
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_task = {executor.submit(copy_file_safely_threaded, task): task 
                         for task in copy_tasks}
        
        # 处理完成的任务
        completed = 0
        for future in as_completed(future_to_task):
            completed += 1
            task = future_to_task[future]
            
            try:
                success, final_name, error, thread_id = future.result()
                
                # 计算进度
                progress = (completed / len(copy_tasks)) * 100
                
                if success:
                    print(f"✅ [{progress:5.1f}%] 线程{thread_id:2d}: {final_name}")
                else:
                    print(f"❌ [{progress:5.1f}%] 线程{thread_id:2d}: {task[2]} - {error}")
                    
                # 每10个任务显示一次汇总
                if completed % 10 == 0 or completed == len(copy_tasks):
                    with copy_lock:
                        print(f"📊 进度汇总: {copy_stats['success']}/{copy_stats['total']} 成功, "
                             f"{copy_stats['failed']} 失败")
                        
            except Exception as e:
                print(f"❌ 任务执行异常: {e}")
                with copy_lock:
                    copy_stats['failed'] += 1
    
    # 返回结果
    success_rate = copy_stats['success'] / copy_stats['total'] if copy_stats['total'] > 0 else 0
    all_success = copy_stats['failed'] == 0
    
    print(f"\n📈 复制完成统计:")
    print(f"   成功: {copy_stats['success']} 个文件")
    print(f"   失败: {copy_stats['failed']} 个文件") 
    print(f"   成功率: {success_rate:.1%}")
    
    return all_success, copy_stats['success'], copy_stats['total']


def main():
    """
    主函数：控制程序的执行流程。
    """
    try:
        # 记录脚本开始时间
        script_start_time = time.time()
        
        # 执行图片复制任务
        success, copied_count, attempted_count = copy_random_images_parallel()
        
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