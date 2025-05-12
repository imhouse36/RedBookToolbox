# 导入必要的模块
import os  # os.path 相关的部分将被 pathlib 替代，但 os.listdir 也会被替代
import zipfile  # 用于处理 .zip 文件
import pathlib # 导入 pathlib 模块

# ==============================================================================
# 脚本功能核心备注 (Script Core Functionality Notes)
# ==============================================================================
#
# 脚本名称 (Script Name):
#   Unzip.py
#
# 主要目的 (Main Purpose):
#   本脚本用于自动解压缩指定文件夹内所有顶层的 .zip 压缩文件。
#
# 工作流程 (Workflow):
#   1. 提示用户输入一个文件夹路径。
#   2. 验证用户输入的路径是否为有效文件夹。
#   3. 遍历该文件夹，查找所有以 '.zip' (不区分大小写) 结尾的文件。
#   4. 对找到的每个 .zip 文件，将其内容解压缩到其所在的同一个文件夹内。
#      例如，如果 D:\MyZips\archive.zip 被处理，其内容会解压到 D:\MyZips\。
#   5. 报告解压缩操作的成功和失败数量。
#
# 注意事项 (Important Notes):
#   - 原始的 .zip 文件在解压缩后仍会保留在原位。
#   - 如果 .zip 文件内部包含文件夹结构，该结构会在解压目标文件夹下被重建。
#   - 本脚本只处理指定文件夹内第一层的 .zip 文件，不会递归进入子文件夹查找 .zip 文件。
#   - 包含中文路径或中文文件名的 .zip 文件应该能被正确处理 (基于 Python 3 和 zipfile 模块的默认行为)。
#
# ==============================================================================

def get_valid_folder_path_from_user() -> pathlib.Path: # 返回 Path 对象
    """
    提示用户输入一个文件夹路径，并验证其有效性。
    持续提示直到用户输入一个存在的文件夹路径。
    :return: 用户输入的有效文件夹路径 (pathlib.Path 对象)
    """
    while True:
        folder_path_str = input("请输入包含 .zip 文件并作为解压缩目标的文件夹路径: ").strip()

        # 移除用户可能输入的路径两端的引号
        if folder_path_str.startswith('"') and folder_path_str.endswith('"'):
            folder_path_str = folder_path_str[1:-1]
        elif folder_path_str.startswith("'") and folder_path_str.endswith("'"):
            folder_path_str = folder_path_str[1:-1]

        folder_path = pathlib.Path(folder_path_str) # 转换为 Path 对象

        if folder_path.is_dir(): # 使用 Path对象的 is_dir() 方法
            return folder_path
        else:
            print(f"错误：路径 '{folder_path_str}' 不是一个有效的文件夹，或文件夹不存在。请重新输入。")


def unzip_all_zips_in_folder_to_itself(folder_path: pathlib.Path): # 接受 Path 对象
    """
    解压缩指定文件夹中所有的 .zip 文件到该文件夹自身。

    :param folder_path: 包含 .zip 文件并作为解压缩目标位置的文件夹路径 (pathlib.Path 对象)。
    """
    if not folder_path.is_dir(): # 使用 Path 对象的 is_dir()
        print(f"错误：文件夹 '{folder_path}' 在处理过程中似乎变得无效了。")
        return

    print(f"\n开始在文件夹 '{folder_path}' 内解压缩所有 .zip 文件...")
    found_zip_files = False
    processed_files = 0
    failed_files = 0

    for item_path in folder_path.iterdir(): # 使用 iterdir() 遍历目录内容
        # item_path 已经是 pathlib.Path 对象

        if item_path.is_file() and item_path.suffix.lower() == '.zip': # 使用 is_file() 和 suffix
            found_zip_files = True
            print(f"  正在处理: {item_path.name}") # 使用 name 属性获取文件名
            try:
                with zipfile.ZipFile(item_path, 'r') as zip_ref: # ZipFile 可以直接接受 Path 对象
                    zip_ref.extractall(folder_path) # extractall 也可以直接接受 Path 对象
                print(f"    '{item_path.name}' 已成功解压缩到 '{folder_path}'")
                processed_files += 1
            except zipfile.BadZipFile:
                print(f"    错误: '{item_path.name}' 是一个损坏的ZIP文件或格式不支持。")
                failed_files += 1
            except Exception as e:
                print(f"    解压缩 '{item_path.name}' 时发生错误: {e}")
                failed_files += 1
        # 原来的 elif 分支因为没有操作，已移除

    if not found_zip_files:
        print(f"在 '{folder_path}' 中没有找到 .zip 文件。")
    else:
        print(f"\n所有 .zip 文件处理完毕。")
        print(f"  成功解压缩: {processed_files} 个文件。")
        if failed_files > 0:
            print(f"  解压缩失败: {failed_files} 个文件。")


if __name__ == "__main__":
    target_directory = get_valid_folder_path_from_user() # 返回的是 Path 对象

    if target_directory: # Path 对象在布尔上下文中如果有效则为True (这里主要判断是否为None, 但函数保证返回有效Path)
        unzip_all_zips_in_folder_to_itself(target_directory)

    input("\n按 Enter 键退出...")