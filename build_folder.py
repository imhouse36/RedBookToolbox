# 脚本功能:
# 本脚本用于在指定的父目录下创建一系列编号的子文件夹 (1, 2, ..., 10)。
# 每次运行时，会提示用户输入基础目录的路径。
#
# 工作流程:
# 1. 提示用户输入一个基础目录 (base_dir) 的路径。
# 2. 检查用户是否输入了路径。
# 3. 检查基础目录是否存在，如果不存在，则创建该基础目录。
# 4. 在基础目录内，尝试创建10个子文件夹，名称从 "1" 到 "10"。
# 5. 如果某个子文件夹已存在，则打印提示信息；如果不存在，则创建它并打印创建信息。
# 6. 处理可能发生的操作系统错误 (例如权限问题)，但忽略文件夹已存在的错误。
#
# 达成的结果:
# - 执行脚本后，用户指定的基础目录将会存在。
# - 在该基础目录下，会存在名为 "1", "2", ..., "10" 的10个子文件夹。
# - 控制台会输出每个文件夹的创建状态。

import pathlib # 导入 pathlib
import errno   # errno 仍然可能用于某些特定的错误检查，但Path对象的方法通常会自己处理

def create_folders_pathlib(base_dir_str):
    """
    在指定的基础目录下创建10个编号的子文件夹 (使用 pathlib)。

    参数:
    base_dir_str (str): 用户通过input()输入的基础目录路径字符串。
    """
    try:
        base_path = pathlib.Path(base_dir_str)

        # 创建基础目录
        # mkdir(parents=True, exist_ok=True)
        # parents=True: 如果父目录不存在，一并创建 (类似 os.makedirs)
        # exist_ok=True: 如果目录已存在，不引发错误
        base_path.mkdir(parents=True, exist_ok=True)
        print(f"基础目录 '{base_path}' 确保存在。")

        # 创建10个子文件夹
        for i in range(1, 31):
            folder_path = base_path / str(i) # 使用 / 操作符拼接路径
            try:
                folder_path.mkdir(exist_ok=True) # parents=False 默认，因为父目录已存在
                print(f"子文件夹 '{folder_path}' 确保存在。")
            except OSError as e:
                # 捕获可能的权限问题等
                print(f"创建子文件夹 '{folder_path}' 时出错: {e}")


        print("所有文件夹处理完成。")

    except OSError as e: # 主要捕获 base_path.mkdir 时可能发生的错误
        # 例如，如果 base_dir_str 指向一个文件，或者权限不足
        print(f"处理基础目录 '{base_dir_str}' 时发生操作系统错误: {e}")
    except Exception as ex: # 捕获其他意外错误
        print(f"发生意外错误: {ex}")


if __name__ == "__main__":
    base_directory_from_input = input("请输入基础目录路径 : ").strip()

    if not base_directory_from_input:
        print("错误：未输入目录路径。脚本将退出。")
    else:
        print(f"接收到的基础目录路径: {base_directory_from_input}")
        create_folders_pathlib(base_directory_from_input)