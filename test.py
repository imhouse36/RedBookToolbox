# -*- coding: UTF-8 -*-
"""
========================================================================================================================
== 文件名称: rename_subfolders_replace_substring.py
== 功能描述: 本脚本用于扫描指定根目录下的所有子目录，如果子目录的名称中包含特定的子字符串（例如 "-一刻"），
==           则将其替换为另一个子字符串（例如 "_一刻"）。
== 工作过程:
==   1. 提示用户输入一个根目录路径。
==   2. 校验用户输入的路径是否存在且为目录。
==   3. 定义要查找的子字符串 target_substring = "-一刻"。
==   4. 定义替换后的子字符串 replacement_substring = "_一刻"。
==   5. 使用 os.walk(root_path, topdown=False) 递归遍历指定根目录下的所有子目录。
==      - topdown=False 确保从最深层目录开始处理，这对于重命名操作更安全。
==   6. 对于 os.walk() 返回的每一级目录 (dirpath) 及其包含的子目录名列表 (dirnames):
==      a. 遍历 dirnames 中的每一个子目录名 (current_sub_dir_name)。
==      b. 如果 current_sub_dir_name 包含 target_substring:
==         i.  通过将 target_substring 替换为 replacement_substring，生成新的子目录名。
==         ii. 构造该子目录的旧完整路径和新完整路径。
==         iii.将这个计划中的重命名操作（旧路径、新路径）添加到一个列表中。
==   7. 在实际执行任何重命名之前，会列出所有计划中的重命名操作，并请求用户最终确认。
==   8. 用户确认后，脚本将逐个执行列表中的重命名操作 (os.rename())。
==      - 在执行前会再次检查源路径是否存在，目标路径是否已存在，以增加安全性。
==   9. 处理可能发生的错误，如权限不足、新名称已存在等。
==   10. 输出操作结果，包括成功重命名的数量和失败的列表（如有）。
== 达成结果:
==   - 指定根目录下，名称中含有 "-一刻" 的子目录，其名称中的 "-一刻" 部分将被替换为 "_一刻"。
==   - 例如：D:\\Data\\Folder-一刻-Backup 将被重命名为 D:\\Data\\Folder_一刻-Backup。
== 注意事项:
==   - 文件夹重命名是敏感操作，请务必在操作前备份重要数据！
==   - 建议先在非重要数据的测试目录中运行本脚本，熟悉其行为。
==   - 如果新的文件夹名称在同一目录下已存在，脚本会跳过该重命名以避免冲突。
==   - 替换是针对子字符串的，如果一个目录名多次出现 "-一刻"，所有匹配项都会被替换。
==   - 请确保执行脚本的用户对相关目录有读、写、修改权限。
== Python 版本: 3.7
========================================================================================================================
"""
import os


def rename_subdirectories_replace_string(root_folder_path):
    """
    重命名指定根目录下的子目录，将名称中的 "-一刻" 替换为 "_一刻"。

    参数:
    root_folder_path (str): 要操作的根目录路径。
    """
    target_substring = "-一刻"
    replacement_substring = "_一刻"

    print(f"\n{'=' * 25} 开始批量重命名子目录 (替换子字符串) {'=' * 25}")
    print(f"[*] 目标根目录: {root_folder_path}")
    print(f"[*] 查找规则: 子目录名中包含 \"{target_substring}\"")
    print(f"[*] 替换规则: 将 \"{target_substring}\" 替换为 \"{replacement_substring}\"")

    # 校验路径是否为有效目录
    if not os.path.isdir(root_folder_path):
        print(f"[!] 错误: 路径 '{root_folder_path}' 不是一个有效的目录或不存在。")
        print(f"{'=' * 30} 处理结束 {'=' * 30}\n")
        return

    planned_renames = []  # 存储计划进行的重命名操作 (old_path, new_path)

    print("\n[*] 正在扫描子目录并预分析重命名操作 (从深层目录开始)...")
    # 使用 os.walk 遍历，topdown=False 表示从最深层目录开始向上遍历
    for dirpath, dirnames, filenames in os.walk(root_folder_path, topdown=False):
        # dirnames 是 dirpath 目录下的子目录名列表
        for sub_dir_name in dirnames:
            if target_substring in sub_dir_name:
                new_sub_dir_name = sub_dir_name.replace(target_substring, replacement_substring)

                # 如果替换后名称没有变化（例如，原名就是 "Folder_一刻" 而 target 是 "-一刻"），则跳过
                if new_sub_dir_name == sub_dir_name:
                    continue

                old_full_path = os.path.join(dirpath, sub_dir_name)
                new_full_path = os.path.join(dirpath, new_sub_dir_name)

                # 预检查新路径是否已存在
                if os.path.exists(new_full_path):
                    print(
                        f"    [!] 警告: 计划将 '{old_full_path}' 重命名为 '{new_full_path}', 但目标路径已存在。此重命名将被跳过。")
                    continue

                planned_renames.append((old_full_path, new_full_path))
                print(f"    计划重命名: '{old_full_path}'  ==>  '{new_full_path}'")

    if not planned_renames:
        print(f"\n[*] 未找到名称中包含 \"{target_substring}\" 的可重命名子目录，或所有潜在目标新名称已存在。")
        print(f"\n{'=' * 30} 处理结束 {'=' * 30}\n")
        return

    print(f"\n[*] 共计划进行 {len(planned_renames)} 个重命名操作。")
    print("\n" + "=" * 70)
    print("== 重要提示: 以下文件夹将被重命名。请仔细核对！                 ==")
    print("==          此操作具有一定风险，建议提前备份数据。               ==")
    print("=" * 70)
    for i, (old, new) in enumerate(planned_renames):
        print(f"  {i + 1}. 从: {old}")
        print(f"     至: {new}")

    confirm = input(
        f"\n===> 是否确认执行这 {len(planned_renames)} 个重命名操作? (请输入 'yes' 确认, 其他任意键取消): ").strip().lower()

    if confirm != 'yes':
        print("\n[*] 用户取消了操作。没有文件夹被重命名。")
        print(f"\n{'=' * 30} 处理结束 {'=' * 30}\n")
        return

    print("\n[*] 开始执行重命名操作...")
    successful_renames = 0
    failed_renames_details = []  # 存储 (old_path, new_path, error_message)

    for old_path, new_path in planned_renames:
        try:
            # 在执行前再次检查条件
            if not os.path.exists(old_path):
                print(f"    [!] 跳过 (源不存在): '{old_path}' 在执行前已不存在。")
                failed_renames_details.append((old_path, new_path, "源路径在执行前消失"))
                continue
            if os.path.exists(new_path):
                print(f"    [!] 跳过 (目标已存在): '{new_path}' 在执行前已存在。")
                failed_renames_details.append((old_path, new_path, "目标路径在执行前已存在"))
                continue

            os.rename(old_path, new_path)
            print(f"    [✓] 成功: '{old_path}'  ==>  '{new_path}'")
            successful_renames += 1
        except OSError as e:
            error_msg = f"重命名 '{old_path}' 到 '{new_path}' 失败: {e}"
            print(f"    [!] 错误: {error_msg}")
            failed_renames_details.append((old_path, new_path, str(e)))
        except Exception as e:
            error_msg = f"重命名 '{old_path}' 到 '{new_path}' 时发生未知错误: {e}"
            print(f"    [!] 错误: {error_msg}")
            failed_renames_details.append((old_path, new_path, str(e)))

    # 输出操作总结
    print("\n" + "*" * 30 + " 操作总结 " + "*" * 30)
    print(f"[*] 计划重命名操作总数: {len(planned_renames)}")
    print(f"[*] 成功重命名文件夹数量: {successful_renames}")
    if failed_renames_details:
        print(f"[!] 未能成功重命名/跳过的操作数量: {len(failed_renames_details)}")
        print("[!] 详情:")
        for old, new, reason in failed_renames_details:
            print(f"    - 操作: '{old}' -> '{new}'")
            print(f"      原因: {reason}")
    elif len(planned_renames) > 0 and confirm == 'yes':
        print("[*] 所有计划的重命名操作均已成功处理。")

    print(f"\n{'=' * 30} 处理结束 {'=' * 30}\n")


if __name__ == "__main__":
    print("+" + "-" * 78 + "+")
    print("|" + " " * 12 + "批量重命名子目录 (替换特定子字符串) 工具 (Python 3.7)" + " " * 11 + "|")
    print("+" + "-" * 78 + "+")
    print(f"| 功能: 将指定根目录下所有子目录名中的 \"-一刻\" 替换为 \"_一刻\"。             |")
    print("| 警告: 文件夹重命名操作有风险，请务必提前备份重要数据！               |")
    print("|       建议先在测试目录中运行以熟悉脚本行为。                         |")
    print("+" + "-" * 78 + "+")

    while True:
        target_root_directory = input("\n请输入要操作的根目录完整路径 (例如 D:\\MyProjects): \n>>> ").strip()
        if target_root_directory:
            rename_subdirectories_replace_string(target_root_directory)
            break
        else:
            print("[!] 输入的路径不能为空，请重新输入。")