# -*- coding: utf-8 -*-
import os
import shutil
import random
import time  # 导入 time 模块以计算执行时间


# --------------------------------------------------------------------------------------------------
# 主要功能:
#   将指定“素材”文件夹内的图片文件，随机复制到“发布”文件夹的各个子目录中。
#
# 工作过程:
#   1. 记录开始时间。
#   2. 提示用户输入“素材”文件夹路径和“发布”文件夹路径。
#   3. 校验输入的路径是否存在且为文件夹。
#   4. 获取“素材”文件夹下的所有子目录列表（这些是图片来源的分类）。
#   5. 获取“发布”文件夹下的所有子目录列表（这些是图片要复制到的目标位置）。
#   6. 初始化总复制文件计数器。
#   7. 对于“发布”文件夹中的每一个子目录：
#      a. 遍历“素材”文件夹的每一个子目录。
#      b. 从当前“素材”子目录中随机选择一张图片。
#      c. 将选中的图片复制到当前的“发布”子目录中，成功则总计数器加一。
#   8. 确保每个“发布”子目录中复制的图片数量等于“素材”文件夹中子目录的数量。
#      如果某个“素材”子目录中没有图片，则会跳过该类别，并在最终提示。
#   9. 记录结束时间，计算总用时。
#  10. 输出总共复制的文件数量和总执行时间。
#
# 达成的结果:
#   “发布”文件夹的每个子目录中，都会包含从“素材”文件夹的每个子目录中随机抽取的一张图片。
#   因此，每个“发布”子目录中的图片数量理论上应等于“素材”文件夹中子目录的数量。
#   脚本执行完毕后，会显示本次操作复制的总文件数和所用时间。
#
# 注意事项:
#   - 脚本仅处理常见图片格式（jpg, jpeg, png, gif, bmp）。如需其他格式，请修改 `image_extensions`。
#   - 如果“素材”的某个子目录中没有图片文件，则在处理对应的“发布”子目录时，该素材类别将被跳过。
#   - 如果“发布”子目录中已存在同名文件，`shutil.copy2` 会覆盖现有文件。
#   - 脚本会打印详细的操作信息和可能的警告或错误。
#   - 请确保对“素材”文件夹有读取权限，对“发布”文件夹及其子目录有写入权限。
# --------------------------------------------------------------------------------------------------

def get_folder_path_from_user(prompt_message: str) -> str:
    """
    提示用户输入一个文件夹路径，并持续请求直到输入一个有效的文件夹路径。

    参数:
        prompt_message (str): 显示给用户的提示信息。

    返回:
        str: 用户输入的有效文件夹路径。
    """
    while True:
        folder_path = input(prompt_message).strip()
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            return folder_path
        else:
            print(f"错误：路径 '{folder_path}' 不存在或不是一个文件夹。请重新输入。")


def copy_random_images():
    """
    主函数，执行图片随机复制逻辑，并在结束时报告统计信息。
    """
    start_time = time.time()  # 记录脚本开始时间
    total_files_copied = 0  # 初始化总复制文件计数器

    print("--- 开始执行图片随机复制任务 ---")

    # 1. 获取用户输入的路径
    source_base_path = get_folder_path_from_user("请输入“素材”文件夹的完整路径: ")
    target_base_path = get_folder_path_from_user("请输入“发布”文件夹的完整路径: ")

    # 定义支持的图片文件扩展名
    image_extensions = ('.jpg', '.jpeg', '.png', '.webp', '.bmp')

    # 2. 获取“素材”文件夹下的所有子目录 (素材类别目录)
    try:
        source_subfolders = [
            d for d in os.listdir(source_base_path)
            if os.path.isdir(os.path.join(source_base_path, d))
        ]
    except OSError as e:
        print(f"错误：无法读取“素材”文件夹 '{source_base_path}' 的内容: {e}")
        return

    if not source_subfolders:
        print(f"警告：“素材”文件夹 '{source_base_path}' 中没有找到任何子目录。脚本无法继续。")
        return
    print(f"“素材”文件夹中找到 {len(source_subfolders)} 个子目录 (类别): {', '.join(source_subfolders)}")

    # 3. 获取“发布”文件夹下的所有子目录 (目标发布目录)
    try:
        target_subfolders = [
            d for d in os.listdir(target_base_path)
            if os.path.isdir(os.path.join(target_base_path, d))
        ]
    except OSError as e:
        print(f"错误：无法读取“发布”文件夹 '{target_base_path}' 的内容: {e}")
        return

    if not target_subfolders:
        print(f"警告：“发布”文件夹 '{target_base_path}' 中没有找到任何子目录。脚本无法继续。")
        return
    print(f"“发布”文件夹中找到 {len(target_subfolders)} 个子目录 (目标): {', '.join(target_subfolders)}")

    # 4. 遍历“发布”文件夹的每个子目录
    for target_sub_name in target_subfolders:
        current_target_dir_path = os.path.join(target_base_path, target_sub_name)
        print(f"\n--- 正在处理“发布”子目录: '{target_sub_name}' ---")

        copied_images_count_for_this_target = 0  # 记录成功复制到当前目标子目录的图片数量

        # 5. 遍历“素材”文件夹的每个子目录 (每个素材类别)
        for source_sub_name in source_subfolders:
            current_source_category_path = os.path.join(source_base_path, source_sub_name)

            try:
                # 获取当前素材类别目录下的所有图片文件
                available_images = [
                    f for f in os.listdir(current_source_category_path)
                    if os.path.isfile(os.path.join(current_source_category_path, f)) and \
                       f.lower().endswith(image_extensions)
                ]
            except OSError as e:
                print(f"  错误: 无法读取素材类别目录 '{current_source_category_path}' 的内容: {e}")
                continue

            if not available_images:
                print(f"  警告: 素材类别目录 '{source_sub_name}' 中没有找到图片文件。跳过此类别。")
                continue

            chosen_image_name = random.choice(available_images)
            source_image_full_path = os.path.join(current_source_category_path, chosen_image_name)
            target_image_full_path = os.path.join(current_target_dir_path, chosen_image_name)

            try:
                shutil.copy2(source_image_full_path, target_image_full_path)
                print(f"  已将 '{source_sub_name}/{chosen_image_name}' 复制到 '{target_sub_name}/{chosen_image_name}'")
                copied_images_count_for_this_target += 1
                total_files_copied += 1  # 增加总复制文件计数
            except Exception as e:
                print(f"  错误: 复制文件 '{source_image_full_path}' 到 '{target_image_full_path}' 失败: {e}")

        print(f"--- 完成处理“发布”子目录 '{target_sub_name}'。")
        print(f"  预期复制图片数量: {len(source_subfolders)} (等于“素材”子目录数量)")
        print(f"  实际为该目录复制图片数量: {copied_images_count_for_this_target}")
        if copied_images_count_for_this_target < len(source_subfolders):
            print(f"  注意: 实际复制数量少于预期，可能是因为部分“素材”子目录中没有图片。")

    end_time = time.time()  # 记录脚本结束时间
    duration = end_time - start_time  # 计算总用时

    print("\n--- 图片随机复制任务全部完成 ---")
    print(f"总共复制文件数量: {total_files_copied}")
    print(f"总执行时间: {duration:.2f} 秒")  # 格式化输出时间，保留两位小数


if __name__ == "__main__":
    copy_random_images()