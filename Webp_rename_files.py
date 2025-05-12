# -*- coding: utf-8 -*-
import os


# --------------------------------------------------------------------------------------------------
# 主要功能:
#   递归地重命名指定顶层文件夹及其所有子文件夹内的文件。
#   新的命名规则为：当前文件所在文件夹的名称_数字编号.原文件扩展名。
#
# 工作过程:
#   采用两阶段重命名策略以确保稳健性，针对每个被处理的文件夹独立执行。
#
#   遍历阶段:
#     1. 提示用户输入要操作的顶层文件夹路径。
#     2. 使用 os.walk() 递归遍历顶层文件夹及其所有子文件夹。
#
#   对于 os.walk() 发现的每一个文件夹 (dirpath):
#     A. 准备阶段:
#        1. 获取当前文件夹 (dirpath) 的基本名称 (例如，路径 "/path/to/MyFolder" 的基本名称是 "MyFolder")。
#           这个基本名称将作为该文件夹下文件重命名的前缀。
#        2. 如果无法获取有效文件夹名称 (例如，对于某些根目录的特殊情况)，则跳过该目录下的文件处理。
#
#     B. 阶段 1: 为当前文件夹下的文件添加临时后缀
#        1. 列出当前文件夹 (dirpath) 中的所有文件，并按原文件名排序。
#        2. 为每个文件生成一个临时文件名，通过在其原名后附加一个独特的后缀 (如 ".__rename_temp_process__")。
#           示例: "image.jpg" -> "image.jpg.__rename_temp_process__"
#        3. 将当前文件夹中所有符合条件的文件重命名为它们的临时名称。
#        4. 收集所有成功生成的临时文件名（位于当前文件夹内），并保持它们的原始排序。
#
#     C. 阶段 2: 将当前文件夹内的临时文件重命名为最终格式
#        1. 初始化一个从1开始的数字计数器 (此计数器对每个文件夹都是独立的)。
#        2. 遍历当前文件夹内，在阶段1B中生成的、排序好的临时文件列表。
#        3. 对于每个临时文件：
#           a. 移除临时后缀，得到文件的原始名称部分（用于提取原始扩展名）。
#           b. 从该原始名称部分中提取原始扩展名 (例如，从 "image.jpg" 中提取 ".jpg")。
#           c. 构建新的文件名，格式为: "{当前文件夹基本名称}_{计数器}{原始扩展名}"
#              示例: "MyFolder_1.jpg", "MyFolder_2.png", ...
#           d. 将临时文件重命名为这个新的最终文件名。
#           e. 计数器递增。
#           f. 累加总重命名文件数。
#
#   错误处理与报告:
#     - 如果输入的顶层路径无效或不是文件夹，会提示用户重新输入。
#     - 如果在文件操作过程中发生IO错误，会捕获并打印错误信息，并尝试继续处理其他文件/文件夹。
#     - 如果某个文件夹为空或不包含任何符合条件的文件，会提示并跳过该文件夹。
#     - 脚本执行完毕后，会显示总共成功重命名的文件数量。
#
# 达成的结果:
#   指定顶层文件夹及其所有子文件夹内的文件，都会根据其所在的直接父文件夹的名称进行重命名。
#   例如，如果顶层文件夹是 "ProjectX"，它里面有文件 "a.txt" 和子文件夹 "Docs"。
#   "Docs" 里面有文件 "b.doc"。
#   结果会是："ProjectX/ProjectX_1.txt" 和 "ProjectX/Docs/Docs_1.doc"。
#
# 注意事项:
#   - 此脚本会直接修改文件名，操作不可逆。强烈建议在操作前备份重要数据。
#   - 临时后缀 "__rename_temp_process__" 被设计为相对独特。
#   - 如果脚本在某个文件的重命名过程中失败，该文件可能保留其原始名称或临时名称。
#   - 脚本兼容 Python 3.7 及以上版本。
# --------------------------------------------------------------------------------------------------

def get_folder_path_from_user(prompt_message: str) -> str:
    """
    提示用户输入一个文件夹路径，并持续请求直到输入一个有效的文件夹路径。
    """
    while True:
        folder_path = input(prompt_message).strip()
        if not folder_path:
            print("错误：路径不能为空，请重新输入。")
            continue
        normalized_path = os.path.normpath(folder_path)
        if os.path.exists(normalized_path) and os.path.isdir(normalized_path):
            return normalized_path
        else:
            print(f"错误：路径 '{folder_path}' (标准化为 '{normalized_path}') 不存在或不是一个文件夹。请重新输入。")


def rename_files_recursively():
    """
    主函数，执行递归的两阶段文件重命名逻辑。
    """
    print("--- 开始执行递归文件重命名任务 ---")

    top_level_folder_path = get_folder_path_from_user("请输入要重命名文件的顶层文件夹路径: ")

    total_renamed_files_count = 0  # 总共成功重命名的文件数
    temp_suffix = ".__rename_temp_process__"  # 临时后缀

    # 使用 os.walk 进行递归遍历
    for dirpath, dirnames, filenames in os.walk(top_level_folder_path, topdown=True):
        # dirpath: 当前正在访问的文件夹的路径
        # dirnames: dirpath 中子文件夹的名称列表 (os.walk 会进一步遍历它们)
        # filenames: dirpath 中文件的名称列表

        current_folder_name = os.path.basename(dirpath)

        # 对于驱动器根目录 (如 "C:\")，basename 可能返回空字符串。
        # 我们需要一个非空的文件夹名作为前缀。
        if not current_folder_name:
            drive, tail = os.path.splitdrive(dirpath)
            # 检查是否是驱动器根目录本身 (e.g., "C:\", "D:", "/")
            if dirpath == drive or (drive and not tail) or (drive and tail in ('\\', '/')):
                cleaned_drive_name = drive.replace(":", "").replace("\\", "").replace("/", "")
                if cleaned_drive_name:
                    current_folder_name = f"{cleaned_drive_name}_root_files"  # 例如 "C_root_files"
                    print(f"\n--- 正在处理驱动器根目录 '{dirpath}' 下的文件 (使用前缀: '{current_folder_name}') ---")
                else:
                    print(f"\n警告: 无法为根目录 '{dirpath}' 生成有效前缀。跳过此目录下的直接文件处理。")
                    continue  # 跳过当前根目录的文件，但os.walk会继续其子目录
            else:  # 其他原因导致 basename 为空
                print(f"\n警告: 无法从路径 '{dirpath}' 获取有效的文件夹名称。跳过此目录。")
                continue
        else:
            print(f"\n--- 正在处理文件夹: '{dirpath}' (使用前缀: '{current_folder_name}') ---")

        # --- 阶段 1: 为当前文件夹 (dirpath) 下的文件添加临时后缀 ---
        # print(f"  --- 阶段 1: 为 '{dirpath}' 中的文件添加临时后缀 ---")

        try:
            # 只处理当前目录 (dirpath) 下的文件 (filenames 来自 os.walk)
            initial_files_in_current_dir = sorted([
                f for f in filenames
                if os.path.isfile(os.path.join(dirpath, f)) and not f.endswith(temp_suffix)
            ])
        except OSError as e:
            print(f"  错误: 无法读取文件夹 '{dirpath}' 的内容以准备阶段1: {e}")
            continue  # 跳到 os.walk 的下一个目录

        if not initial_files_in_current_dir:
            print(f"  文件夹 '{dirpath}' 中没有符合条件的文件可进行第一阶段重命名。")
            # 仍需检查是否有上次残留的临时文件

        # print(f"  找到 {len(initial_files_in_current_dir)} 个原始文件准备进行第一阶段重命名。")
        temp_files_generated_in_current_dir_order = []

        for original_filename in initial_files_in_current_dir:
            original_full_path = os.path.join(dirpath, original_filename)
            temp_filename_for_current = original_filename + temp_suffix
            temp_full_path_for_current = os.path.join(dirpath, temp_filename_for_current)

            try:
                if os.path.exists(temp_full_path_for_current):
                    print(f"    警告 (阶段1): 目标临时文件名 '{temp_filename_for_current}' 已在 '{dirpath}' 中存在。")
                    print(f"    跳过文件 '{original_filename}' 的第一阶段重命名。该临时文件将直接进入第二阶段处理。")
                    if temp_filename_for_current.endswith(temp_suffix):  # 双重检查
                        temp_files_generated_in_current_dir_order.append(temp_filename_for_current)
                    continue

                os.rename(original_full_path, temp_full_path_for_current)
                # print(f"    '{original_filename}' -> '{temp_filename_for_current}' (在 '{dirpath}')")
                temp_files_generated_in_current_dir_order.append(temp_filename_for_current)
            except OSError as e:
                print(
                    f"    错误 (阶段1): 重命名 '{original_filename}' 到 '{temp_filename_for_current}' (在 '{dirpath}') 失败: {e}")
            except Exception as e:
                print(
                    f"    未知错误 (阶段1): 重命名 '{original_filename}' 到 '{temp_filename_for_current}' (在 '{dirpath}') 失败: {e}")

        # --- 阶段 2: 将当前文件夹内的临时文件重命名为最终格式 ---
        # print(f"\n  --- 阶段 2 (文件夹: '{dirpath}'): 将临时文件重命名为最终格式 ---")

        # 重新扫描当前目录以获取所有临时文件，包括新生成的和可能已存在的
        try:
            current_dir_temp_files = sorted([
                f for f in os.listdir(dirpath)
                if os.path.isfile(os.path.join(dirpath, f)) and f.endswith(temp_suffix)
            ])
        except OSError as e:
            print(f"  错误: 无法读取文件夹 '{dirpath}' 的内容以准备阶段2: {e}")
            continue  # 跳到 os.walk 的下一个目录

        if not current_dir_temp_files:
            if not initial_files_in_current_dir:  # 如果最初就没有文件，也没有临时文件，就正常提示
                print(f"  文件夹 '{dirpath}' 中没有临时文件可进行第二阶段重命名，且初始也没有文件。")
            elif initial_files_in_current_dir and not temp_files_generated_in_current_dir_order:
                print(f"  文件夹 '{dirpath}' 中有初始文件，但阶段1未能生成或找到临时文件。")
            else:  # 有初始文件，但没有临时文件，可能是阶段1全部失败
                print(f"  文件夹 '{dirpath}' 中没有临时文件可进行第二阶段重命名。")
            continue  # 继续处理 os.walk 的下一个目录

        file_counter_for_current_dir = 1
        renamed_in_this_dir = 0

        for temp_filename in current_dir_temp_files:
            temp_full_path = os.path.join(dirpath, temp_filename)

            if not temp_filename.endswith(temp_suffix):  # 防御性检查
                print(f"    警告 (阶段2): 文件 '{temp_filename}' (在 '{dirpath}') 没有预期的临时后缀。跳过。")
                continue

            original_name_part_for_ext = temp_filename[:-len(temp_suffix)]
            _, original_ext = os.path.splitext(original_name_part_for_ext)

            final_filename = f"{current_folder_name}_{file_counter_for_current_dir}{original_ext}"
            final_full_path = os.path.join(dirpath, final_filename)

            try:
                if os.path.exists(final_full_path):
                    print(f"    警告 (阶段2): 目标最终文件名 '{final_filename}' 已在 '{dirpath}' 中存在。")
                    print(
                        f"    这可能表示文件夹中有与预期命名模式冲突的文件，或上次运行未清理。跳过重命名 '{temp_filename}'。")
                    continue

                os.rename(temp_full_path, final_full_path)
                print(f"    已重命名: '{dirpath}{os.sep}{temp_filename}' -> '{final_filename}'")
                total_renamed_files_count += 1
                renamed_in_this_dir += 1
                file_counter_for_current_dir += 1
            except OSError as e:
                print(f"    错误 (阶段2): 重命名 '{temp_filename}' 到 '{final_filename}' (在 '{dirpath}') 失败: {e}")
                print(f"    文件 '{temp_filename}' (在 '{dirpath}') 可能仍带有临时后缀。请手动检查。")
            except Exception as e:
                print(
                    f"    未知错误 (阶段2): 重命名 '{temp_filename}' 到 '{final_filename}' (在 '{dirpath}') 失败: {e}")

        if renamed_in_this_dir > 0:
            print(f"  在文件夹 '{dirpath}' 中成功重命名 {renamed_in_this_dir} 个文件。")
        elif initial_files_in_current_dir or current_dir_temp_files:  # 如果有文件但没重命名成功
            print(f"  在文件夹 '{dirpath}' 中未成功重命名任何文件（尽管有待处理文件）。")

    print("\n--- 递归文件重命名任务全部结束 ---")
    print(f"总共成功重命名文件数量: {total_renamed_files_count}")


if __name__ == "__main__":
    rename_files_recursively()