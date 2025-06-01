# -*- coding: utf-8 -*-
# 脚本功能:
# 本脚本用于将指定源文件夹内的所有图片文件随机复制到目标文件夹的各个编号子文件夹中。
# 每个编号子文件夹都会获得一张随机选择的图片文件。
#
# 工作流程:
#   1. 提示用户输入源文件夹路径（包含图片文件的文件夹）。
#   2. 校验源文件夹路径是否存在且包含图片文件。
#   3. 提示用户输入目标文件夹路径（包含编号子文件夹的文件夹）。
#   4. 校验目标文件夹路径是否存在且包含编号子文件夹。
#   5. 从源文件夹中获取所有图片文件列表。
#   6. 获取目标文件夹中的所有编号子文件夹列表。
#   7. 为每个编号子文件夹随机选择一张图片并复制过去。
#   8. 输出复制结果和统计信息。
#
# 达成的结果:
# - 目标文件夹的每个编号子文件夹中都会包含一张从源文件夹随机选择的图片。
# - 控制台会输出详细的复制状态和最终的统计报告。
#
# 注意事项:
# - 脚本仅处理常见图片格式（jpg, jpeg, png, webp, bmp, gif）。如需其他格式，请修改 `IMAGE_EXTENSIONS`。
# - 如果源文件夹中没有图片文件，脚本会提示错误并退出。
# - 如果目标位置已存在同名文件，脚本会自动重命名避免冲突。
# - 请确保对源文件夹有读取权限，对目标文件夹及其子目录有写入权限。

import pathlib
import shutil
import random
import time
import sys
from typing import List, Tuple

# 支持的图片格式常量
IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif')

def get_valid_folder_path_from_user(prompt_message: str) -> pathlib.Path:
    """
    提示用户输入一个文件夹路径，并持续请求直到输入一个已存在的有效文件夹路径。

    参数:
        prompt_message (str): 显示给用户的提示信息。

    返回:
        pathlib.Path: 用户输入的有效文件夹路径对象。
    """
    while True:
        try:
            folder_path_str = input(prompt_message).strip()
            if not folder_path_str:
                print("错误：未输入路径。请重新输入。")
                continue
            
            folder_path = pathlib.Path(folder_path_str)
            
            if folder_path.exists() and folder_path.is_dir():
                return folder_path
            else:
                print(f"错误：路径 '{folder_path}' 不存在或不是一个文件夹。请重新输入。")
        except KeyboardInterrupt:
            print("\n用户取消操作。")
            sys.exit(0)

def get_image_files_from_folder(folder_path: pathlib.Path) -> List[pathlib.Path]:
    """
    获取指定文件夹中的所有图片文件。

    参数:
        folder_path (pathlib.Path): 文件夹路径。

    返回:
        List[pathlib.Path]: 图片文件路径列表。
    """
    print(f"\n--- 扫描源文件夹 '{folder_path}' ---")
    
    try:
        image_files = [
            f for f in folder_path.iterdir()
            if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
        ]
        
        print(f"找到 {len(image_files)} 张图片文件")
        
        if image_files:
            print("图片格式统计:")
            format_count = {}
            for img in image_files:
                ext = img.suffix.lower()
                format_count[ext] = format_count.get(ext, 0) + 1
            
            for ext, count in sorted(format_count.items()):
                print(f"  {ext}: {count} 张")
        
        return image_files
        
    except OSError as e:
        print(f"错误：无法读取源文件夹 '{folder_path}': {e}")
        return []

def get_numbered_subfolders(folder_path: pathlib.Path) -> List[pathlib.Path]:
    """
    获取指定文件夹中的所有编号子文件夹。

    参数:
        folder_path (pathlib.Path): 文件夹路径。

    返回:
        List[pathlib.Path]: 编号子文件夹路径列表（按数字排序）。
    """
    print(f"\n--- 扫描目标文件夹 '{folder_path}' ---")
    
    try:
        numbered_folders = [
            d for d in folder_path.iterdir()
            if d.is_dir() and d.name.isdigit()
        ]
        
        # 按数字排序
        numbered_folders.sort(key=lambda x: int(x.name))
        
        print(f"找到 {len(numbered_folders)} 个编号子文件夹")
        
        if numbered_folders:
            folder_names = [f.name for f in numbered_folders]
            print(f"编号范围: {min(folder_names)} - {max(folder_names)}")
        
        return numbered_folders
        
    except OSError as e:
        print(f"错误：无法读取目标文件夹 '{folder_path}': {e}")
        return []

def generate_unique_filename(target_dir: pathlib.Path, original_name: str) -> str:
    """
    生成唯一的文件名以避免冲突。

    参数:
        target_dir (pathlib.Path): 目标目录。
        original_name (str): 原始文件名。

    返回:
        str: 唯一的文件名。
    """
    target_file = target_dir / original_name
    if not target_file.exists():
        return original_name
    
    # 如果文件已存在，添加数字后缀
    stem = pathlib.Path(original_name).stem
    suffix = pathlib.Path(original_name).suffix
    counter = 1
    
    while True:
        new_name = f"{stem}_{counter}{suffix}"
        if not (target_dir / new_name).exists():
            return new_name
        counter += 1

def copy_random_images_to_folders(source_images: List[pathlib.Path], 
                                 target_folders: List[pathlib.Path]) -> Tuple[int, int]:
    """
    将源图片随机复制到目标文件夹中。

    参数:
        source_images (List[pathlib.Path]): 源图片文件列表。
        target_folders (List[pathlib.Path]): 目标文件夹列表。

    返回:
        Tuple[int, int]: (成功复制的文件数量, 发生冲突并重命名的文件数量)
    """
    print(f"\n--- 开始执行随机复制任务 ---")
    
    success_count = 0
    conflict_count = 0
    
    total_folders = len(target_folders)
    
    for i, target_folder in enumerate(target_folders, 1):
        progress = (i / total_folders) * 100
        
        try:
            # 随机选择一张图片
            selected_image = random.choice(source_images)
            
            # 生成唯一文件名
            unique_filename = generate_unique_filename(target_folder, selected_image.name)
            target_file_path = target_folder / unique_filename
            
            # 执行复制
            shutil.copy2(selected_image, target_file_path)
            
            # 检查文件名冲突
            if unique_filename != selected_image.name:
                conflict_count += 1
                print(f"  [进度: {progress:.1f}%] 文件夹 '{target_folder.name}': {selected_image.name} -> {unique_filename} (重命名)")
            else:
                print(f"  [进度: {progress:.1f}%] 文件夹 '{target_folder.name}': {selected_image.name}")
            
            success_count += 1
            
        except OSError as e:
            print(f"  [进度: {progress:.1f}%] 错误: 复制到文件夹 '{target_folder.name}' 失败: {e}")
        except Exception as ex:
            print(f"  [进度: {progress:.1f}%] 意外错误: 处理文件夹 '{target_folder.name}' 时发生错误: {ex}")
    
    return success_count, conflict_count

def main():
    """
    主函数：控制程序的执行流程。
    """
    print("图片文件随机复制工具")
    print("=" * 40)
    
    # 记录脚本开始时间
    start_time = time.time()
    
    try:
        # 1. 获取用户输入：源文件夹路径
        source_path = get_valid_folder_path_from_user(
            "请输入源文件夹的完整路径（包含图片文件）: "
        )
        
        # 2. 获取源文件夹中的图片文件
        source_images = get_image_files_from_folder(source_path)
        
        if not source_images:
            print("\n错误：源文件夹中没有找到任何图片文件。")
            print(f"支持的图片格式: {', '.join(IMAGE_EXTENSIONS)}")
            return
        
        # 3. 获取用户输入：目标文件夹路径
        target_path = get_valid_folder_path_from_user(
            "请输入目标文件夹的完整路径（包含编号子文件夹）: "
        )
        
        # 4. 获取目标文件夹中的编号子文件夹
        target_folders = get_numbered_subfolders(target_path)
        
        if not target_folders:
            print("\n错误：目标文件夹中没有找到任何编号子文件夹。")
            print("编号子文件夹应该是纯数字命名的文件夹（如：1, 2, 3...）")
            return
        
        print(f"\n配置确认:")
        print(f"- 源图片数量: {len(source_images)}")
        print(f"- 目标文件夹数量: {len(target_folders)}")
        print(f"- 源文件夹路径: {source_path}")
        print(f"- 目标文件夹路径: {target_path}")
        
        # 5. 执行复制任务
        success_count, conflict_count = copy_random_images_to_folders(source_images, target_folders)
        
        # 6. 输出统计信息
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"\n{'='*50}")
        print("图片复制任务完成统计报告:")
        print(f"{'='*50}")
        print(f"成功复制文件数量: {success_count}")
        print(f"解决的文件名冲突: {conflict_count}")
        print(f"目标文件夹总数: {len(target_folders)}")
        print(f"总执行时间: {execution_time:.2f} 秒")
        
        if success_count > 0:
            print(f"平均复制速度: {success_count/execution_time:.2f} 文件/秒")
        
        success_rate = (success_count / len(target_folders)) * 100 if target_folders else 0
        print(f"成功率: {success_rate:.1f}%")
        
        print(f"{'='*50}")
        print("程序执行完毕。")
        
    except KeyboardInterrupt:
        print("\n\n用户中断程序执行。")
    except Exception as e:
        print(f"\n程序执行过程中发生意外错误: {e}")
        print("请检查输入参数和文件权限后重试。")

if __name__ == "__main__":
    main()