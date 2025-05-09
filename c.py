# 脚本功能:
# 本脚本用于将指定源文件夹中的图片随机分发到其下的各个子文件夹中。
# 每个子文件夹会接收到固定数量（默认为4张）的随机图片副本。
# 每次运行时，会提示用户输入源文件夹的路径。
#
# 工作流程:
# 1. 提示用户输入一个源文件夹 (source_folder) 的路径。
# 2. 检查用户是否输入了路径。
# 3. 扫描源文件夹根目录，收集所有图片文件（.png, .jpg, .jpeg, .gif, .bmp）。
# 4. 获取源文件夹下的所有子目录列表。
# 5. 如果没有子目录，则打印提示信息并结束。
# 6. 遍历每个子目录：
#    a. 从收集到的所有图片列表中随机选择4张图片。
#    b. 如果源文件夹中的图片总数少于4张，则选择所有可用的图片。
#    c. 将选中的图片复制到当前正在处理的子目录中。
# 7. 打印每一步的操作信息，如复制完成的提示。
#
# 达成的结果:
# - 用户指定的源文件夹 (source_folder) 下的每个子文件夹中，都会包含4张从源文件夹根目录随机选取的图片副本。
# - 如果源文件夹根目录的图片总数不足4张，则每个子文件夹会包含所有这些图片的副本。
# - 原始图片文件仍保留在源文件夹的根目录中，不会被移动或删除。
# - 控制台会输出图片复制到各个子文件夹的情况。

import os
import random
import shutil


# import sys # sys模块不再需要

def distribute_images(source_folder_param):
    """
    将源文件夹中的图片随机分发到其子文件夹中。

    参数:
    source_folder_param (str): 用户通过input()输入的源文件夹路径。
                               此文件夹应包含图片文件以及目标子文件夹。
    """
    # 脚本核心逻辑开始
    all_images = []

    print(f"正在从源文件夹 '{source_folder_param}' 收集图片...")
    if not os.path.exists(source_folder_param) or not os.path.isdir(source_folder_param):
        print(f"错误：指定的源文件夹 '{source_folder_param}' 不存在或不是一个目录。脚本将退出。")
        return

    for file in os.listdir(source_folder_param):
        if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')):
            if os.path.isfile(os.path.join(source_folder_param, file)):
                all_images.append(file)

    if not all_images:
        print(f"警告: 在源文件夹 '{source_folder_param}' 的根目录中未找到任何图片文件。脚本将无法复制图片。")

    print(f"在源文件夹根目录共找到 {len(all_images)} 张图片: {all_images if all_images else '无'}")

    subdirectories = [d for d in os.listdir(source_folder_param) if os.path.isdir(os.path.join(source_folder_param, d))]
    print(f"找到以下子目录: {subdirectories if subdirectories else '无'}")

    if not subdirectories:
        print(f"在 '{source_folder_param}' 中未找到任何子目录。脚本结束。")
        return

    for subdir in subdirectories:
        subdir_path = os.path.join(source_folder_param, subdir)
        print(f"\n正在处理子目录: {subdir_path}")

        selected_images = []
        if not all_images:
            print(f"  由于源文件夹根目录无图片，无法向 '{subdir}' 复制图片。")
            continue

        if len(all_images) >= 4:
            selected_images = random.sample(all_images, 4)
        else:
            selected_images = all_images[:]
            print(f"  警告: 源图片不足4张，只有 {len(all_images)} 张图片可用。将复制所有可用图片到 '{subdir}'。")

        print(f"  为 '{subdir}' 选中的图片: {selected_images}")

        for img_filename in selected_images:
            source_file_path = os.path.join(source_folder_param, img_filename)
            destination_file_path = os.path.join(subdir_path, img_filename)

            try:
                shutil.copy2(source_file_path, destination_file_path)
            except Exception as e:
                print(f"    复制文件 '{img_filename}' 到 '{destination_file_path}' 时出错: {e}")

        if selected_images:
            print(f"  已向子目录 '{subdir}' 复制 {len(selected_images)} 张随机图片。")

    print("\n所有子目录处理完成。")


if __name__ == "__main__":
    # 主程序入口

    # 提示用户输入源文件夹路径
    source_directory_from_input = input("请输入源文件夹路径 (例如: D:\\Downloads\\live\\小红书发布图\\万达店): ")

    # 去除用户输入路径前后可能存在的空格
    source_directory_from_input = source_directory_from_input.strip()

    # 检查用户是否真的输入了内容
    if not source_directory_from_input:
        print("错误：未输入源文件夹路径。脚本将退出。")
    else:
        print(f"接收到的源文件夹路径: {source_directory_from_input}")
        # 调用核心功能函数
        distribute_images(source_directory_from_input)