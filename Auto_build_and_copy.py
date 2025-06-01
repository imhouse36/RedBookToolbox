# -*- coding: utf-8 -*-
# 脚本功能:
# 本脚本首先提示用户输入希望创建的编号子文件夹数量、"素材"文件夹路径和"发布"文件夹的基础路径。
# 然后，在指定的"发布"基础路径下创建这些编号子文件夹。
# 最后，将"素材"文件夹内各个类别子目录中的图片文件，随机复制到新创建的这些编号子文件夹中。
#
# 工作流程:
#   1. 记录脚本开始时间。
#   2. 提示用户输入要在"发布"文件夹下创建的子文件夹数量。
#   3. 校验输入的数量是否为正整数。
#   4. 提示用户输入"素材"文件夹的路径，并校验。
#   5. 提示用户输入"发布"文件夹的基础路径（编号子文件夹将在此创建），并校验。
#   6. 在"发布"基础路径下创建指定数量的编号子文件夹 (例如 "1", "2", ..., "N")。
#   7. 获取"素材"文件夹下的所有子目录列表（图片来源分类）。
#   8. 获取新创建的"发布"编号子文件夹列表。
#   9. 对于每一个新创建的"发布"编号子文件夹：
#      a. 遍历"素材"文件夹的每一个分类子目录。
#      b. 从当前"素材"分类子目录中随机选择一张图片。
#      c. 将选中的图片复制到当前的"发布"编号子文件夹中。
#  10. 记录结束时间，计算总用时。
#  11. 输出总共复制的文件数量和总执行时间。
#
# 达成的结果:
# - 用户指定的"发布"基础目录将会存在，并在其下创建指定数量的编号子文件夹。
# - 每个新创建的编号子文件夹中，都会包含从"素材"文件夹的每个分类子目录中随机抽取的一张图片。
# - 控制台会输出详细的操作信息、创建状态、复制状态以及最终的统计报告。
#
# 注意事项:
# - 脚本仅处理常见图片格式（jpg, jpeg, png, webp, bmp, gif）。如需其他格式，请修改 `IMAGE_EXTENSIONS`。
# - 如果"素材"的某个分类子目录中没有图片文件，则在处理对应的"发布"编号子文件夹时，该素材类别将被跳过。
# - 如果目标位置已存在同名文件，脚本会自动重命名避免冲突。
# - 请确保对"素材"文件夹有读取权限，对"发布"基础路径及其子目录有写入和创建权限。
# - 输入的文件夹数量必须是大于0的整数。

import pathlib
import shutil
import random
import time
from typing import List, Dict, Tuple
import argparse
import sys

# 支持的图片格式常量
IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif')

def get_positive_integer_input(prompt_message: str) -> int:
    """
    提示用户输入一个正整数，并持续请求直到输入有效。

    参数:
        prompt_message (str): 显示给用户的提示信息。

    返回:
        int: 用户输入的有效正整数。
    """
    while True:
        try:
            num_str = input(prompt_message).strip()
            if not num_str:
                print("错误：未输入内容。请重新输入。")
                continue
            num_val = int(num_str)
            if num_val <= 0:
                print("错误：输入的数字必须是大于0的正整数。请重新输入。")
            else:
                return num_val
        except ValueError:
            print("错误：请输入一个有效的数字。请重新输入。")
        except KeyboardInterrupt:
            print("\n用户取消操作。")
            sys.exit(0)

def get_valid_folder_path_from_user(prompt_message: str, ensure_exists: bool = True) -> pathlib.Path:
    """
    提示用户输入一个文件夹路径。
    如果 ensure_exists 为 True, 则持续请求直到输入一个已存在的有效文件夹路径。
    如果 ensure_exists 为 False, 仅验证输入非空。

    参数:
        prompt_message (str): 显示给用户的提示信息。
        ensure_exists (bool): 是否必须确保路径存在且为目录。

    返回:
        pathlib.Path: 用户输入的文件夹路径对象。
    """
    while True:
        try:
            folder_path_str = input(prompt_message).strip()
            if not folder_path_str:
                print("错误：未输入路径。请重新输入。")
                continue
            
            folder_path = pathlib.Path(folder_path_str)
            
            if ensure_exists:
                if folder_path.exists() and folder_path.is_dir():
                    return folder_path
                else:
                    print(f"错误：路径 '{folder_path}' 不存在或不是一个文件夹。请重新输入。")
            else:
                return folder_path
        except KeyboardInterrupt:
            print("\n用户取消操作。")
            sys.exit(0)

def create_numbered_folders(base_dir: pathlib.Path, num_folders_to_create: int) -> bool:
    """
    在指定的基础目录下创建指定数量的编号子文件夹。

    参数:
        base_dir (pathlib.Path): 基础目录路径对象。
        num_folders_to_create (int): 要创建的子文件夹数量。

    返回:
        bool: 如果所有操作成功完成则返回 True，否则 False。
    """
    print(f"\n--- 开始创建编号子文件夹于 '{base_dir}' ---")
    try:
        # 确保基础目录存在
        base_dir.mkdir(parents=True, exist_ok=True)
        print(f"发布基础目录 '{base_dir}' 确保存在。")

        success_count = 0
        for i in range(1, num_folders_to_create + 1):
            folder_path = base_dir / str(i)
            try:
                folder_path.mkdir(exist_ok=True)
                print(f"  子文件夹 '{folder_path.name}' 创建成功。")
                success_count += 1
            except OSError as e:
                print(f"  创建子文件夹 '{folder_path}' 时出错: {e}")

        print(f"--- 完成创建编号子文件夹：成功 {success_count}/{num_folders_to_create} ---")
        return success_count == num_folders_to_create
    except OSError as e:
        print(f"处理发布基础目录 '{base_dir}' 时发生操作系统错误: {e}")
        return False
    except Exception as ex:
        print(f"创建编号子文件夹时发生意外错误: {ex}")
        return False

def get_images_from_categories(source_materials_path: pathlib.Path) -> Dict[str, List[pathlib.Path]]:
    """
    获取素材文件夹各分类目录中的所有图片文件。

    参数:
        source_materials_path (pathlib.Path): 素材文件夹路径。

    返回:
        Dict[str, List[pathlib.Path]]: 分类名称到图片文件列表的映射。
    """
    print("\n--- 扫描素材文件夹结构 ---")
    categories_images = {}
    
    try:
        category_dirs = [d for d in source_materials_path.iterdir() if d.is_dir()]
        
        if not category_dirs:
            print(f"警告：素材文件夹 '{source_materials_path}' 中没有找到任何分类子目录。")
            return categories_images
        
        for category_dir in category_dirs:
            try:
                image_files = [
                    f for f in category_dir.iterdir()
                    if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
                ]
                categories_images[category_dir.name] = image_files
                print(f"  分类 '{category_dir.name}': 找到 {len(image_files)} 张图片")
            except OSError as e:
                print(f"  错误: 无法读取分类目录 '{category_dir}': {e}")
                categories_images[category_dir.name] = []
        
        total_images = sum(len(images) for images in categories_images.values())
        print(f"--- 扫描完成：{len(categories_images)} 个分类，共 {total_images} 张图片 ---")
        
    except OSError as e:
        print(f"错误：无法读取素材文件夹 '{source_materials_path}': {e}")
    
    return categories_images

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

def copy_random_images_to_numbered_folders(source_materials_path: pathlib.Path, 
                                         target_publish_base_path: pathlib.Path) -> None:
    """
    将"素材"文件夹的图片随机复制到"发布"基础路径下的编号子文件夹中。

    参数:
        source_materials_path (pathlib.Path): "素材"文件夹的路径。
        target_publish_base_path (pathlib.Path): "发布"文件夹的基础路径。
    """
    print("\n--- 开始执行图片随机复制任务 ---")
    start_time = time.time()
    total_files_copied = 0
    skipped_categories = 0
    conflict_resolved = 0

    # 1. 预先获取所有素材图片
    categories_images = get_images_from_categories(source_materials_path)
    
    if not categories_images:
        print("无法进行复制：没有找到素材分类。")
        return

    # 2. 获取编号子文件夹
    try:
        target_numbered_folders = [
            d for d in target_publish_base_path.iterdir()
            if d.is_dir() and d.name.isdigit()
        ]
        target_numbered_folders.sort(key=lambda x: int(x.name))  # 按数字排序
    except OSError as e:
        print(f"错误：无法读取发布基础文件夹 '{target_publish_base_path}': {e}")
        return

    if not target_numbered_folders:
        print(f"警告：发布基础文件夹 '{target_publish_base_path}' 中没有找到编号子目录。")
        return
    
    print(f"发布基础文件夹中找到 {len(target_numbered_folders)} 个编号子目录")

    # 3. 执行复制操作
    total_operations = len(target_numbered_folders) * len(categories_images)
    current_operation = 0
    
    for target_folder in target_numbered_folders:
        print(f"\n--- 处理编号文件夹: '{target_folder.name}' ---")
        folder_copy_count = 0
        
        for category_name, image_list in categories_images.items():
            current_operation += 1
            progress = (current_operation / total_operations) * 100
            
            if not image_list:
                print(f"  [进度: {progress:.1f}%] 跳过分类 '{category_name}': 无图片文件")
                skipped_categories += 1
                continue
            
            try:
                # 随机选择一张图片
                selected_image = random.choice(image_list)
                
                # 生成唯一文件名
                unique_filename = generate_unique_filename(target_folder, selected_image.name)
                target_file_path = target_folder / unique_filename
                
                # 执行复制
                shutil.copy2(selected_image, target_file_path)
                
                # 检查文件名冲突
                if unique_filename != selected_image.name:
                    conflict_resolved += 1
                    print(f"  [进度: {progress:.1f}%] 分类 '{category_name}': {selected_image.name} -> {unique_filename} (重命名)")
                else:
                    print(f"  [进度: {progress:.1f}%] 分类 '{category_name}': {selected_image.name}")
                
                total_files_copied += 1
                folder_copy_count += 1
                
            except OSError as e:
                print(f"  [进度: {progress:.1f}%] 错误: 复制 '{selected_image}' 到 '{target_folder}' 失败: {e}")
            except Exception as ex:
                print(f"  [进度: {progress:.1f}%] 意外错误: 处理分类 '{category_name}' 时发生错误: {ex}")
        
        print(f"--- 编号文件夹 '{target_folder.name}' 完成：复制了 {folder_copy_count} 个文件 ---")
    
    # 4. 输出统计信息
    end_time = time.time()
    execution_time = end_time - start_time
    
    print(f"\n{'='*60}")
    print("图片复制任务完成统计报告:")
    print(f"{'='*60}")
    print(f"总共复制文件数量: {total_files_copied}")
    print(f"跳过的空分类数量: {skipped_categories}")
    print(f"解决的文件名冲突: {conflict_resolved}")
    print(f"总执行时间: {execution_time:.2f} 秒")
    print(f"平均复制速度: {total_files_copied/execution_time:.2f} 文件/秒" if execution_time > 0 else "平均复制速度: N/A")
    print(f"{'='*60}")

def main():
    """
    主函数：控制程序的执行流程。
    """
    print("图片文件夹自动构建和复制工具")
    print("=" * 50)
    
    # 记录脚本开始时间
    script_start_time = time.time()
    
    try:
        # 1. 获取用户输入：要创建的子文件夹数量
        num_folders = get_positive_integer_input(
            "请输入要在发布文件夹下创建的编号子文件夹数量: "
        )
        
        # 2. 获取用户输入：素材文件夹路径
        source_path = get_valid_folder_path_from_user(
            "请输入素材文件夹的完整路径: ", 
            ensure_exists=True
        )
        
        # 3. 获取用户输入：发布基础文件夹路径
        publish_base_path = get_valid_folder_path_from_user(
            "请输入发布文件夹的基础路径（编号子文件夹将在此创建）: ", 
            ensure_exists=False
        )
        
        print(f"\n配置确认:")
        print(f"- 创建子文件夹数量: {num_folders}")
        print(f"- 素材文件夹路径: {source_path}")
        print(f"- 发布基础路径: {publish_base_path}")
        
        # 4. 创建编号子文件夹
        if create_numbered_folders(publish_base_path, num_folders):
            print("\n编号子文件夹创建成功，开始复制图片...")
            
            # 5. 执行图片复制任务
            copy_random_images_to_numbered_folders(source_path, publish_base_path)
        else:
            print("\n编号子文件夹创建失败，程序终止。")
            return
        
        # 6. 输出脚本总执行时间
        script_end_time = time.time()
        total_script_time = script_end_time - script_start_time
        print(f"\n脚本总执行时间: {total_script_time:.2f} 秒")
        print("程序执行完毕。")
        
    except KeyboardInterrupt:
        print("\n\n用户中断程序执行。")
    except Exception as e:
        print(f"\n程序执行过程中发生意外错误: {e}")
        print("请检查输入参数和文件权限后重试。")

if __name__ == "__main__":
    main()                