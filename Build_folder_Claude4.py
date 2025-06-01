# -*- coding: utf-8 -*-
# 脚本功能:
# 本脚本用于在指定的根目录下创建一系列编号子文件夹。
# 用户可以输入要创建的文件夹数量，脚本会自动创建从 "1" 到 "N" 的编号文件夹。
#
# 工作流程:
#   1. 提示用户输入要创建的文件夹数量。
#   2. 校验输入的数量是否为正整数。
#   3. 提示用户输入根目录路径，并校验路径是否存在。
#   4. 在指定的根目录下创建编号文件夹（例如 "1", "2", ..., "N"）。
#   5. 输出创建结果和统计信息。
#
# 达成的结果:
# - 在用户指定的根目录下创建指定数量的编号子文件夹。
# - 控制台会输出详细的创建状态和最终的统计报告。
#
# 注意事项:
# - 如果目标文件夹已存在，脚本会跳过创建并继续处理下一个。
# - 请确保对根目录有写入和创建权限。
# - 输入的文件夹数量必须是大于0的整数。

import pathlib
import time
import sys
from typing import Tuple

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
        except KeyboardInterrupt:
            print("\n用户取消操作。")
            sys.exit(0)

def get_valid_folder_path_from_user(prompt_message: str) -> pathlib.Path:
    """
    提示用户输入一个文件夹路径，并持续请求直到输入一个已存在的有效文件夹路径。

    参数:
        prompt_message (str): 显示给用户的提示信息。

    返回:
        pathlib.Path: 用户输入的有效文件夹路径对象。
    """
    while True:
        try:
            folder_path_str = input(prompt_message).strip()
            if not folder_path_str:
                print("错误：未输入路径。请重新输入。")
                continue
            
            folder_path = pathlib.Path(folder_path_str)
            
            if folder_path.exists() and folder_path.is_dir():
                return folder_path
            else:
                print(f"错误：路径 '{folder_path}' 不存在或不是一个文件夹。请重新输入。")
        except KeyboardInterrupt:
            print("\n用户取消操作。")
            sys.exit(0)

def create_numbered_folders(root_dir: pathlib.Path, num_folders: int) -> Tuple[int, int]:
    """
    在指定的根目录下创建指定数量的编号子文件夹。

    参数:
        root_dir (pathlib.Path): 根目录路径对象。
        num_folders (int): 要创建的文件夹数量。

    返回:
        Tuple[int, int]: (成功创建的文件夹数量, 跳过的文件夹数量)
    """
    print(f"\n--- 开始在 '{root_dir}' 下创建 {num_folders} 个编号文件夹 ---")
    
    success_count = 0
    skipped_count = 0
    
    for i in range(1, num_folders + 1):
        folder_path = root_dir / str(i)
        
        try:
            if folder_path.exists():
                print(f"  文件夹 '{i}' 已存在，跳过创建")
                skipped_count += 1
            else:
                folder_path.mkdir(parents=True, exist_ok=True)
                print(f"  文件夹 '{i}' 创建成功")
                success_count += 1
        except OSError as e:
            print(f"  创建文件夹 '{i}' 时出错: {e}")
        except Exception as ex:
            print(f"  创建文件夹 '{i}' 时发生意外错误: {ex}")
    
    return success_count, skipped_count

def main():
    """
    主函数：控制程序的执行流程。
    """
    print("编号文件夹批量创建工具")
    print("=" * 40)
    
    # 记录脚本开始时间
    start_time = time.time()
    
    try:
        # 1. 获取用户输入：要创建的文件夹数量
        num_folders = get_positive_integer_input(
            "请输入要创建的编号文件夹数量: "
        )
        
        # 2. 获取用户输入：根目录路径
        root_path = get_valid_folder_path_from_user(
            "请输入根目录的完整路径: "
        )
        
        print(f"\n配置确认:")
        print(f"- 创建文件夹数量: {num_folders}")
        print(f"- 根目录路径: {root_path}")
        
        # 3. 创建编号文件夹
        success_count, skipped_count = create_numbered_folders(root_path, num_folders)
        
        # 4. 输出统计信息
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"\n{'='*50}")
        print("文件夹创建任务完成统计报告:")
        print(f"{'='*50}")
        print(f"成功创建文件夹数量: {success_count}")
        print(f"跳过的文件夹数量: {skipped_count}")
        print(f"总处理文件夹数量: {num_folders}")
        print(f"总执行时间: {execution_time:.2f} 秒")
        
        if success_count > 0:
            print(f"平均创建速度: {success_count/execution_time:.2f} 文件夹/秒")
        
        print(f"{'='*50}")
        print("程序执行完毕。")
        
    except KeyboardInterrupt:
        print("\n\n用户中断程序执行。")
    except Exception as e:
        print(f"\n程序执行过程中发生意外错误: {e}")
        print("请检查输入参数和文件权限后重试。")

if __name__ == "__main__":
    main()