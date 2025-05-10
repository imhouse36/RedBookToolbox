# 脚本功能:
# 本脚本用于在指定的父目录下创建一系列用户指定数量的编号子文件夹 (例如，如果用户输入5，则创建 1, 2, 3, 4, 5)。
# 每次运行时，会提示用户输入基础目录的路径以及要创建的子文件夹数量。
#
# 工作流程:
# 1. 提示用户输入一个基础目录 (base_dir) 的路径。
# 2. 检查用户是否输入了路径，如果未输入则退出。
# 3. 提示用户输入要创建的子文件夹数量。
# 4. 校验输入的数量是否为正整数，如果不是则要求重新输入。
# 5. 检查基础目录是否存在，如果不存在，则创建该基础目录。
# 6. 在基础目录内，尝试创建用户指定数量的子文件夹，名称从 "1" 开始递增编号。
# 7. 如果某个子文件夹已存在，则打印提示信息；如果不存在，则创建它并打印创建信息。
# 8. 处理可能发生的操作系统错误 (例如权限问题)，但忽略文件夹已存在的错误。
#
# 达成的结果:
# - 执行脚本后，用户指定的基础目录将会存在。
# - 在该基础目录下，会存在用户指定数量的、从 "1" 开始编号的子文件夹。
# - 控制台会输出每个文件夹的创建状态以及最终的处理完成信息。
#
# 注意事项:
# - 请确保运行脚本的用户对指定的基础目录及其子目录有写入权限。
# - 输入的文件夹数量必须是大于0的整数。

import pathlib # 导入 pathlib 模块，用于以面向对象的方式处理文件系统路径
import errno   # 导入 errno 模块，用于处理特定的错误号 (虽然pathlib内置了部分处理)

def create_folders_pathlib(base_dir_str: str, num_folders_to_create: int):
    """
    在指定的基础目录下创建指定数量的编号子文件夹 (使用 pathlib)。

    参数:
    base_dir_str (str): 用户通过input()输入的基础目录路径字符串。
    num_folders_to_create (int): 用户希望创建的子文件夹数量。
    """
    try:
        # 将输入的字符串路径转换为 Path 对象，方便进行路径操作
        base_path = pathlib.Path(base_dir_str)

        # 创建基础目录
        # base_path.mkdir(parents=True, exist_ok=True)
        # - parents=True: 如果路径中的父目录不存在，则一并创建 (类似于 os.makedirs)。
        # - exist_ok=True: 如果目标目录已经存在，则不会引发 FileExistsError 错误。
        base_path.mkdir(parents=True, exist_ok=True)
        print(f"基础目录 '{base_path}' 确保存在。")

        # 创建指定数量的子文件夹
        # 循环从 1 到 num_folders_to_create (包含)
        for i in range(1, num_folders_to_create + 1):
            # 使用 / 操作符拼接路径，这是 pathlib 的一个便捷特性
            folder_name = str(i) # 文件夹名称为数字字符串 "1", "2", ...
            folder_path = base_path / folder_name

            try:
                # 创建子文件夹
                # exist_ok=True: 如果子文件夹已存在，不引发错误。
                # parents=False (默认): 因为我们已经确保了 base_path (父目录) 存在。
                folder_path.mkdir(exist_ok=True)
                print(f"子文件夹 '{folder_path}' 确保存在。")
            except OSError as e:
                # 捕获在创建单个子文件夹时可能发生的操作系统错误，例如权限问题。
                # FileExistsError 会被 exist_ok=True 处理，所以这里主要捕获其他 OSError。
                print(f"创建子文件夹 '{folder_path}' 时出错: {e}")

        print(f"已处理完 {num_folders_to_create} 个子文件夹的创建请求。")

    except OSError as e:
        # 主要捕获在处理 base_path.mkdir 时可能发生的严重错误，
        # 例如，如果 base_dir_str 指向一个文件，或者因权限不足无法创建基础目录。
        print(f"处理基础目录 '{base_dir_str}' 时发生操作系统错误: {e}")
    except Exception as ex:
        # 捕获其他所有未预料到的意外错误，增加脚本的健壮性。
        print(f"发生意外错误: {ex}")


if __name__ == "__main__":
    # 提示用户输入基础目录路径，并移除首尾可能存在的空白字符
    base_directory_from_input = input("请输入基础目录路径 : ").strip()

    # 检查用户是否输入了基础目录路径
    if not base_directory_from_input:
        print("错误：未输入目录路径。脚本将退出。")
    else:
        # 如果输入了基础目录路径，则继续提示输入要创建的文件夹数量
        num_folders_to_create_input = 0 # 初始化变量
        while True: # 使用循环来确保用户输入的是有效的正整数
            try:
                num_folders_str = input("请输入要创建的子文件夹个数 (例如: 5): ").strip()
                if not num_folders_str: # 检查是否输入了内容
                    print("错误：未输入文件夹个数。请重新输入。")
                    continue

                num_folders_to_create_input = int(num_folders_str) # 尝试将输入转换为整数

                if num_folders_to_create_input <= 0: # 检查数字是否为正数
                    print("错误：文件夹个数必须是大于0的正整数。请重新输入。")
                else:
                    break # 输入有效，跳出循环
            except ValueError:
                # 如果 int()转换失败 (例如用户输入了文本)，则捕获 ValueError
                print("错误：请输入一个有效的数字作为文件夹个数 (例如: 5)。请重新输入。")

        # 打印用户输入的路径和数量，以便确认
        print(f"接收到的基础目录路径: '{base_directory_from_input}'")
        print(f"计划创建的子文件夹个数: {num_folders_to_create_input}")

        # 调用函数执行文件夹创建操作
        create_folders_pathlib(base_directory_from_input, num_folders_to_create_input)

        print("脚本执行完毕。")