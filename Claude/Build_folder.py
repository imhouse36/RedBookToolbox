# -*- coding: utf-8 -*-
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
# - 支持用户中断操作（Ctrl+C）优雅退出。

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
    提示用户输入一个文件夹路径，并验证输入非空。

    参数:
        prompt_message (str): 显示给用户的提示信息。

    返回:
        pathlib.Path: 用户输入的文件夹路径对象。
    """
    while True:
        try:
            folder_path_str = input(prompt_message).strip()
            if not folder_path_str:
                print("错误：未输入路径。请重新输入。")
                continue
            return pathlib.Path(folder_path_str)
        except KeyboardInterrupt:
            print("\n用户取消操作。")
            sys.exit(0)

def create_folders_pathlib(base_dir: pathlib.Path, num_folders_to_create: int) -> Tuple[bool, int]:
    """
    在指定的基础目录下创建指定数量的编号子文件夹 (使用 pathlib)。

    参数:
        base_dir (pathlib.Path): 基础目录路径对象。
        num_folders_to_create (int): 用户希望创建的子文件夹数量。

    返回:
        Tuple[bool, int]: (是否全部成功, 成功创建的文件夹数量)
    """
    print(f"\n--- 开始创建编号子文件夹于 '{base_dir}' ---")
    start_time = time.time()
    success_count = 0
    
    try:
        # 创建基础目录
        # parents=True: 如果路径中的父目录不存在，则一并创建
        # exist_ok=True: 如果目标目录已经存在，则不会引发 FileExistsError 错误
        base_dir.mkdir(parents=True, exist_ok=True)
        print(f"基础目录 '{base_dir}' 确保存在。")

        # 创建指定数量的子文件夹
        for i in range(1, num_folders_to_create + 1):
            folder_name = str(i)
            folder_path = base_dir / folder_name
            progress = (i / num_folders_to_create) * 100

            try:
                # 检查文件夹是否已存在
                if folder_path.exists():
                    print(f"  [进度: {progress:.1f}%] 子文件夹 '{folder_name}' 已存在，跳过创建。")
                else:
                    folder_path.mkdir(exist_ok=True)
                    print(f"  [进度: {progress:.1f}%] 子文件夹 '{folder_name}' 创建成功。")
                success_count += 1
            except OSError as e:
                print(f"  [进度: {progress:.1f}%] 创建子文件夹 '{folder_path}' 时出错: {e}")

        # 输出统计信息
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"\n{'='*50}")
        print("文件夹创建任务完成统计报告:")
        print(f"{'='*50}")
        print(f"成功处理文件夹数量: {success_count}/{num_folders_to_create}")
        print(f"总执行时间: {execution_time:.2f} 秒")
        print(f"平均创建速度: {success_count/execution_time:.2f} 文件夹/秒" if execution_time > 0 else "平均创建速度: N/A")
        print(f"{'='*50}")
        
        return success_count == num_folders_to_create, success_count

    except OSError as e:
        print(f"处理基础目录 '{base_dir}' 时发生操作系统错误: {e}")
        return False, success_count
    except Exception as ex:
        print(f"创建编号子文件夹时发生意外错误: {ex}")
        return False, success_count


def main():
    """
    主函数：控制程序的执行流程。
    """
    print("编号文件夹批量创建工具")
    print("=" * 50)
    
    # 记录脚本开始时间
    script_start_time = time.time()
    
    try:
        # 1. 获取用户输入：基础目录路径
        base_path = get_valid_folder_path_from_user(
            "请输入基础目录路径: "
        )
        
        # 2. 获取用户输入：要创建的子文件夹数量
        num_folders = get_positive_integer_input(
            "请输入要创建的子文件夹个数 (例如: 5): "
        )
        
        print(f"\n配置确认:")
        print(f"- 基础目录路径: {base_path}")
        print(f"- 创建子文件夹数量: {num_folders}")
        
        # 3. 执行文件夹创建任务
        success, created_count = create_folders_pathlib(base_path, num_folders)
        
        if success:
            print("\n所有文件夹创建任务完成！")
        else:
            print(f"\n文件夹创建任务部分完成，成功创建 {created_count}/{num_folders} 个文件夹。")
        
        # 4. 输出脚本总执行时间
        script_end_time = time.time()
        total_script_time = script_end_time - script_start_time
        print(f"\n脚本总执行时间: {total_script_time:.2f} 秒")
        print("程序执行完毕。")
        
    except KeyboardInterrupt:
        print("\n\n用户中断程序执行。")
    except Exception as e:
        print(f"\n程序执行过程中发生意外错误: {e}")
        print("请检查输入参数和文件权限后重试。")

if __name__ == "__main__":
    main()