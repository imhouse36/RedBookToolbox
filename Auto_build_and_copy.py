# -*- coding: utf-8 -*-
# 脚本功能:
# 本脚本首先提示用户输入希望创建的编号子文件夹数量、“素材”文件夹路径和“发布”文件夹的基础路径。
# 然后，在指定的“发布”基础路径下创建这些编号子文件夹。
# 最后，将“素材”文件夹内各个类别子目录中的图片文件，随机复制到新创建的这些编号子文件夹中。
#
# 工作流程:
#   1. 记录脚本开始时间。
#   2. 提示用户输入要在“发布”文件夹下创建的子文件夹数量。
#   3. 校验输入的数量是否为正整数。
#   4. 提示用户输入“素材”文件夹的路径，并校验。
#   5. 提示用户输入“发布”文件夹的基础路径（编号子文件夹将在此创建），并校验。
#   6. 在“发布”基础路径下创建指定数量的编号子文件夹 (例如 "1", "2", ..., "N")。
#   7. 获取“素材”文件夹下的所有子目录列表（图片来源分类）。
#   8. 获取新创建的“发布”编号子文件夹列表。
#   9. 对于每一个新创建的“发布”编号子文件夹：
#      a. 遍历“素材”文件夹的每一个分类子目录。
#      b. 从当前“素材”分类子目录中随机选择一张图片。
#      c. 将选中的图片复制到当前的“发布”编号子文件夹中。
#  10. 记录结束时间，计算总用时。
#  11. 输出总共复制的文件数量和总执行时间。
#
# 达成的结果:
# - 用户指定的“发布”基础目录将会存在，并在其下创建指定数量的编号子文件夹。
# - 每个新创建的编号子文件夹中，都会包含从“素材”文件夹的每个分类子目录中随机抽取的一张图片。
# - 控制台会输出详细的操作信息、创建状态、复制状态以及最终的统计报告。
#
# 注意事项:
# - 脚本仅处理常见图片格式（jpg, jpeg, png, webp, bmp）。如需其他格式，请修改 `image_extensions`。
# - 如果“素材”的某个分类子目录中没有图片文件，则在处理对应的“发布”编号子文件夹时，该素材类别将被跳过。
# - 如果目标位置已存在同名文件，`shutil.copy2` 会覆盖现有文件。
# - 请确保对“素材”文件夹有读取权限，对“发布”基础路径及其子目录有写入和创建权限。
# - 输入的文件夹数量必须是大于0的整数。

import pathlib # 导入 pathlib 模块，用于以面向对象的方式处理文件系统路径
import os      # 导入 os 模块，用于操作系统相关功能，如路径检查、列出目录内容
import shutil  # 导入 shutil 模块，用于高级文件操作，如复制文件
import random  # 导入 random 模块，用于随机选择
import time    # 导入 time 模块，用于计算脚本执行时间
import errno   # 导入 errno 模块 (虽然pathlib已处理很多情况，保留以备不时之需)

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

def get_valid_folder_path_from_user(prompt_message: str, ensure_exists: bool = True) -> str:
    """
    提示用户输入一个文件夹路径。
    如果 ensure_exists 为 True, 则持续请求直到输入一个已存在的有效文件夹路径。
    如果 ensure_exists 为 False, 仅验证输入非空 (用于将要创建的目录的父目录场景，父目录本身不必先存在)。

    参数:
        prompt_message (str): 显示给用户的提示信息。
        ensure_exists (bool): 是否必须确保路径存在且为目录。

    返回:
        str: 用户输入的文件夹路径字符串。
    """
    while True:
        folder_path_str = input(prompt_message).strip()
        if not folder_path_str:
            print("错误：未输入路径。请重新输入。")
            continue
        if ensure_exists:
            if os.path.exists(folder_path_str) and os.path.isdir(folder_path_str):
                return folder_path_str
            else:
                print(f"错误：路径 '{folder_path_str}' 不存在或不是一个文件夹。请重新输入。")
        else: # 如果不需要确保存在，只要有输入即可 (用于父目录场景)
            return folder_path_str


def create_numbered_folders(base_dir_str: str, num_folders_to_create: int):
    """
    在指定的基础目录下创建指定数量的编号子文件夹 (使用 pathlib)。

    参数:
    base_dir_str (str): 用户通过input()输入的基础目录路径字符串。
    num_folders_to_create (int): 用户希望创建的子文件夹数量。

    返回:
        bool: 如果所有操作（或尝试操作）成功完成则返回 True，否则 False。
    """
    print(f"\n--- 开始创建编号子文件夹于 '{base_dir_str}' ---")
    try:
        base_path = pathlib.Path(base_dir_str)
        base_path.mkdir(parents=True, exist_ok=True)
        print(f"发布基础目录 '{base_path}' 确保存在。")

        for i in range(1, num_folders_to_create + 1):
            folder_name = str(i)
            folder_path = base_path / folder_name
            try:
                folder_path.mkdir(exist_ok=True)
                print(f"  子文件夹 '{folder_path}' 确保存在。")
            except OSError as e:
                print(f"  创建子文件夹 '{folder_path}' 时出错: {e}")
                # 即使单个文件夹创建失败，也尝试继续创建其他文件夹

        print(f"--- 完成创建 {num_folders_to_create} 个编号子文件夹的尝试 ---")
        return True
    except OSError as e:
        print(f"处理发布基础目录 '{base_dir_str}' 时发生操作系统错误: {e}")
        return False
    except Exception as ex:
        print(f"创建编号子文件夹时发生意外错误: {ex}")
        return False

def copy_random_images_to_numbered_folders(source_materials_path_str: str, target_publish_base_path_str: str):
    """
    将“素材”文件夹的图片随机复制到“发布”基础路径下的编号子文件夹中。

    参数:
        source_materials_path_str (str): “素材”文件夹的路径。
        target_publish_base_path_str (str): “发布”文件夹的基础路径，其下应有编号子文件夹。
    """
    print("\n--- 开始执行图片随机复制任务 ---")
    start_time = time.time()
    total_files_copied = 0
    image_extensions = ('.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif') # 增加了.gif

    # 1. 获取“素材”文件夹下的所有子目录 (素材类别目录)
    try:
        source_categories = [
            d for d in os.listdir(source_materials_path_str)
            if os.path.isdir(os.path.join(source_materials_path_str, d))
        ]
    except OSError as e:
        print(f"错误：无法读取“素材”文件夹 '{source_materials_path_str}' 的内容: {e}")
        return

    if not source_categories:
        print(f"警告：“素材”文件夹 '{source_materials_path_str}' 中没有找到任何分类子目录。无法进行复制。")
        return
    print(f"“素材”文件夹中找到 {len(source_categories)} 个分类子目录: {', '.join(source_categories)}")

    # 2. 获取“发布”基础路径下的所有编号子文件夹 (目标发布目录)
    try:
        # 我们期望这些是数字命名的文件夹，可以根据需要添加更严格的过滤
        target_numbered_folders = [
            d for d in os.listdir(target_publish_base_path_str)
            if os.path.isdir(os.path.join(target_publish_base_path_str, d)) and d.isdigit()
        ]
    except OSError as e:
        print(f"错误：无法读取“发布”基础文件夹 '{target_publish_base_path_str}' 的内容: {e}")
        return

    if not target_numbered_folders:
        print(f"警告：“发布”基础文件夹 '{target_publish_base_path_str}' 中没有找到编号子目录。请确保已先创建。")
        return
    print(f"“发布”基础文件夹中找到 {len(target_numbered_folders)} 个编号子目录: {', '.join(target_numbered_folders)}")

    # 3. 遍历“发布”文件夹的每个编号子目录
    for target_folder_name in target_numbered_folders:
        current_target_dir_full_path = os.path.join(target_publish_base_path_str, target_folder_name)
        print(f"\n--- 正在处理“发布”编号子目录: '{target_folder_name}' ---")

        copied_images_count_for_this_target = 0

        # 4. 遍历“素材”文件夹的每个分类子目录
        for source_category_name in source_categories:
            current_source_category_full_path = os.path.join(source_materials_path_str, source_category_name)

            try:
                available_images = [
                    f for f in os.listdir(current_source_category_full_path)
                    if os.path.isfile(os.path.join(current_source_category_full_path, f)) and \
                       f.lower().endswith(image_extensions)
                ]
            except OSError as e:
                print(f"  错误: 无法读取素材分类目录 '{current_source_category_full_path}' 的内容: {e}")
                continue # 跳过这个有问题的素材分类

            if not available_images:
                print(f"  警告: 素材分类目录 '{source_category_name}' 中没有找到支持的图片文件。跳过此类别。")
                continue

            chosen_image_name = random.choice(available_images)
            source_image_full_path = os.path.join(current_source_category_full_path, chosen_image_name)
            # 为避免目标文件名冲突，可以考虑在复制时重命名，但当前需求是直接复制
            target_image_full_path = os.path.join(current_target_dir_full_path, chosen_image_name)

            try:
                # 确保目标目录存在 (虽然按流程它应该存在)
                os.makedirs(current_target_dir_full_path, exist_ok=True)
                shutil.copy2(source_image_full_path, target_image_full_path)
                print(f"  已将 '{source_category_name}/{chosen_image_name}' 复制到 '{target_folder_name}/{chosen_image_name}'")
                copied_images_count_for_this_target += 1
                total_files_copied += 1
            except Exception as e:
                print(f"  错误: 复制文件 '{source_image_full_path}' 到 '{target_image_full_path}' 失败: {e}")

        print(f"--- 完成处理“发布”编号子目录 '{target_folder_name}' ---")
        print(f"  预期为该目录复制图片数量 (等于素材分类数): {len(source_categories)}")
        print(f"  实际为该目录复制图片数量: {copied_images_count_for_this_target}")
        if copied_images_count_for_this_target < len(source_categories):
            print(f"  注意: 实际复制数量少于预期，可能是因为部分“素材”分类目录中没有图片或读取/复制时出错。")

    end_time = time.time()
    duration = end_time - start_time

    print("\n--- 图片随机复制任务全部完成 ---")
    print(f"总共复制文件数量: {total_files_copied}")
    print(f"总执行时间: {duration:.2f} 秒")


if __name__ == "__main__":
    print("欢迎使用文件夹创建与图片随机复制脚本！")
    print("=" * 40)

    # 1. 获取要创建的文件夹数量
    num_folders = get_positive_integer_input("请输入要在“发布”文件夹下创建的编号子文件夹个数 (例如: 5): ")

    # 2. 获取素材文件夹路径
    materials_path = get_valid_folder_path_from_user("请输入“素材”文件夹的完整路径: ", ensure_exists=True)

    # 3. 获取发布基础文件夹路径
    # 对于发布基础路径，我们不需要它预先存在，因为 create_numbered_folders 会创建它 (如果它不存在)
    # 但是，为了用户体验，通常也期望用户提供一个有效的“父”路径概念
    # 这里，我们让用户输入一个路径，create_numbered_folders 中的 pathlib 会处理创建
    publish_base_path = get_valid_folder_path_from_user(
        "请输入“发布”文件夹的基础路径 (编号子文件夹将在此路径下创建): ",
        ensure_exists=False # 改为False，因为pathlib可以创建它
    )
    # 进一步校验 publish_base_path，确保它不是一个已存在的文件
    if os.path.exists(publish_base_path) and os.path.isfile(publish_base_path):
        print(f"错误：指定的发布基础路径 '{publish_base_path}' 是一个文件，而不是目录。脚本将退出。")
    else:
        print(f"\n确认信息:")
        print(f" - 将在 '{publish_base_path}' 下创建 {num_folders} 个编号子文件夹。")
        print(f" - 素材将从 '{materials_path}' 读取。")
        print("-" * 40)

        # 4. 创建编号子文件夹
        creation_successful = create_numbered_folders(publish_base_path, num_folders)

        if creation_successful:
            # 5. 如果文件夹创建（或尝试创建）完成，则执行图片复制
            #    检查publish_base_path是否真的被创建并且是目录，以防万一create_numbered_folders内部有未捕获问题
            if os.path.exists(publish_base_path) and os.path.isdir(publish_base_path):
                copy_random_images_to_numbered_folders(materials_path, publish_base_path)
            else:
                print(f"错误：发布基础目录 '{publish_base_path}' 未能成功创建或不是一个目录。无法进行图片复制。")
        else:
            print("由于编号子文件夹创建过程中发生错误，图片复制步骤将被跳过。")

    print("=" * 40)
    print("脚本执行完毕。")