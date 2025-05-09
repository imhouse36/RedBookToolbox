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

import pathlib  # 导入 pathlib
import random
import shutil

# 定义常量
IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')
NUM_IMAGES_TO_COPY = 4


def distribute_images_optimized(source_folder_str: str):
    """
    将源文件夹中的图片随机分发到其子文件夹中 (使用 pathlib 和常量)。

    参数:
    source_folder_str (str): 用户通过input()输入的源文件夹路径字符串。
    """
    source_path = pathlib.Path(source_folder_str)

    # 步骤1 & 2: 检查源文件夹有效性
    if not source_path.exists() or not source_path.is_dir():
        print(f"错误：指定的源文件夹 '{source_path}' 不存在或不是一个目录。脚本将退出。")
        return

    # 步骤3: 扫描源文件夹根目录，收集所有图片文件
    print(f"正在从源文件夹 '{source_path}' 收集图片...")
    all_image_paths = []  # 存储图片的 Path 对象
    for item in source_path.iterdir():  # 遍历源目录下的所有条目
        # item 是一个 Path 对象
        if item.is_file() and item.suffix.lower() in IMAGE_EXTENSIONS:
            all_image_paths.append(item)

    if not all_image_paths:
        print(f"警告: 在源文件夹 '{source_path}' 的根目录中未找到任何图片文件。脚本将无法复制图片。")
        # 如果没有图片，后续很多操作无意义，可以考虑在这里也提前返回，或者让后续逻辑处理

    # 为了打印方便，显示文件名列表
    image_filenames_for_display = [p.name for p in all_image_paths]
    print(
        f"在源文件夹根目录共找到 {len(all_image_paths)} 张图片: {image_filenames_for_display if image_filenames_for_display else '无'}")

    # 步骤4: 获取源文件夹下的所有子目录列表
    subdirectories = []  # 存储子目录的 Path 对象
    for item in source_path.iterdir():
        if item.is_dir():
            subdirectories.append(item)

    subdirectory_names_for_display = [sd.name for sd in subdirectories]
    print(f"找到以下子目录: {subdirectory_names_for_display if subdirectory_names_for_display else '无'}")

    # 步骤5: 如果没有子目录或没有图片，则结束
    if not subdirectories:
        print(f"在 '{source_path}' 中未找到任何子目录。脚本结束。")
        return

    if not all_image_paths:  # 如果在前面没有图片时未返回，这里是最后的机会
        print(f"由于源文件夹根目录无图片，无法向任何子目录复制图片。脚本结束。")
        return

    # 步骤6: 遍历每个子目录
    for subdir_path in subdirectories:  # subdir_path 是一个 Path 对象
        print(f"\n正在处理子目录: {subdir_path}")

        # 步骤6a & 6b: 随机选择图片
        selected_image_paths = []
        if len(all_image_paths) >= NUM_IMAGES_TO_COPY:
            selected_image_paths = random.sample(all_image_paths, NUM_IMAGES_TO_COPY)
        else:
            selected_image_paths = all_image_paths[:]  # 复制列表以防意外修改
            print(
                f"  警告: 源图片不足 {NUM_IMAGES_TO_COPY} 张，只有 {len(all_image_paths)} 张图片可用。将复制所有可用图片到 '{subdir_path.name}'。")

        selected_filenames_for_display = [p.name for p in selected_image_paths]
        print(f"  为 '{subdir_path.name}' 选中的图片: {selected_filenames_for_display}")

        # 步骤6c: 将选中的图片复制到当前子目录
        for img_source_path in selected_image_paths:  # img_source_path 是源图片的 Path 对象
            destination_file_path = subdir_path / img_source_path.name  # 使用 / 拼接路径

            try:
                shutil.copy2(img_source_path, destination_file_path)
            except Exception as e:  # 可以考虑更具体的异常如 shutil.Error, IOError
                print(f"    复制文件 '{img_source_path.name}' 到 '{destination_file_path}' 时出错: {e}")

        if selected_image_paths:
            print(f"  已向子目录 '{subdir_path.name}' 复制 {len(selected_image_paths)} 张随机图片。")

    print("\n所有子目录处理完成。")


if __name__ == "__main__":
    # 主程序入口 (与原脚本基本一致)
    source_directory_from_input = input(
        "请输入源文件夹路径 (例如: D:\\Downloads\\live\\小红书发布图\\万达店): ").strip()

    if not source_directory_from_input:
        print("错误：未输入源文件夹路径。脚本将退出。")
    else:
        print(f"接收到的源文件夹路径: {source_directory_from_input}")
        distribute_images_optimized(source_directory_from_input)  # 调用优化后的函数