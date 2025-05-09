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

import os
import errno


# import sys # sys模块不再需要，因为我们使用input()

def create_folders(base_dir_param):
    """
    在指定的基础目录下创建10个编号的子文件夹。

    参数:
    base_dir_param (str): 用户通过input()输入的基础目录路径。
    """
    # 脚本核心逻辑开始
    try:
        # 步骤1: 确保基础目录存在
        # 如果用户提供的基础目录 (base_dir_param) 不存在，则尝试创建它。
        # os.makedirs 会创建所有必需的中间目录。
        if not os.path.exists(base_dir_param):
            os.makedirs(base_dir_param)
            print(f"基础目录已创建: {base_dir_param}")
        else:
            print(f"基础目录已存在: {base_dir_param}")

        # 步骤2: 创建10个文件夹，命名从1到10
        # 循环10次，每次创建一个编号的子文件夹。
        for i in range(1, 11):
            # 构造每个子文件夹的完整路径
            folder_path = os.path.join(base_dir_param, str(i))

            # 检查子文件夹是否已存在
            if not os.path.exists(folder_path):
                # 如果不存在，则创建子文件夹
                os.mkdir(folder_path)
                print(f"创建文件夹: {folder_path}")
            else:
                # 如果已存在，则打印提示信息
                print(f"文件夹已存在: {folder_path}")

        print("所有文件夹创建完成")
        # 结果: 在 base_dir_param 目录下，会生成名为 "1" 到 "10" 的10个子文件夹。

    except OSError as e:
        # 步骤3: 错误处理
        # 捕获在创建文件夹过程中可能发生的操作系统错误。
        if e.errno != errno.EEXIST:
            print(f"创建文件夹时出错: {e}")
            # 根据情况，你可能仍想在这里 raise e，或者只是打印错误然后允许脚本结束
            # raise
        else:
            print(f"尝试创建已存在的目录时被忽略 (属于正常流程): {e.filename}")
    except Exception as ex:  # 捕获其他可能的错误，例如路径字符串无效
        print(f"发生意外错误: {ex}")


if __name__ == "__main__":
    # 主程序入口

    # 提示用户输入基础目录路径
    # input() 函数会暂停脚本执行，等待用户在控制台输入，并按 Enter 键
    base_directory_from_input = input("请输入基础目录路径 (例如: D:\\Downloads\\live\\小红书发布图\\万达店): ")

    # 去除用户输入路径前后可能存在的空格
    base_directory_from_input = base_directory_from_input.strip()

    # 检查用户是否真的输入了内容
    if not base_directory_from_input:
        print("错误：未输入目录路径。脚本将退出。")
    else:
        print(f"接收到的基础目录路径: {base_directory_from_input}")
        # 调用核心功能函数
        create_folders(base_directory_from_input)