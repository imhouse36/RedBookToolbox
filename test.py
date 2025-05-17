# -*- coding: UTF-8 -*-
"""
文件及文件夹内文件MD5校验工具

主要功能：
1. 计算指定单个文件的MD5哈希值。
2. 如果输入的是文件夹路径，则计算该文件夹下所有直接子文件的MD5哈希值（不递归子文件夹）。

工作过程：
1. 提示用户输入要校验的文件或文件夹的完整路径。
2. 将输入路径转换为绝对路径，以确保路径的规范性。
3. 检查转换后的路径是否存在。
4. 如果路径指向一个文件：
   a. 打印开始计算该文件的提示信息。
   b. 以二进制读取模式（"rb"）打开文件。
   c. 为了高效处理大文件并避免内存问题，分块读取文件内容。
   d. 对每个读取的数据块，更新MD5哈希对象。
   e. 文件读取完毕后，获取最终的MD5哈希值（十六进制字符串）。
   f. 打印文件的完整路径和其对应的MD5值。
   g. 打印计算完成的总结性信息和边框。
5. 如果路径指向一个文件夹：
   a. 打印开始扫描文件夹的提示信息。
   b. 使用 os.listdir() 获取文件夹内的所有条目（文件名和子文件夹名）。
   c. 遍历这些条目，对每一个条目，使用 os.path.join() 构建其完整路径。
   d. 使用 os.path.isfile() 判断该条目是否为文件。
   e. 如果是文件，则将其加入待处理文件列表。
   f. 打印找到的直接文件总数。
   g. 遍历待处理文件列表，对每个文件：
      i.  打印当前处理进度（例如 "[1/10]"）和文件名。
      ii. 调用MD5计算逻辑（与处理单个文件时类似）。
      iii. 记录计算成功或失败的状态。
   h. 打印文件夹扫描完成的总结信息，包括成功和失败的文件数量。
6. 如果路径无效（不存在、既不是文件也不是文件夹等）或在处理过程中发生IO错误等其他异常，
   则会打印相应的错误提示信息。

达成结果：
- 对于单个文件输入：清晰地输出该文件的MD5哈希值。
- 对于文件夹输入：为文件夹内每个直接子文件输出其MD5哈希值，并在最后提供一个包含成功和失败计数的摘要。

注意事项：
- 请确保输入的是有效的文件或文件夹路径。相对路径也会被尝试解析为绝对路径。
- 对于非常大的文件，MD5计算过程可能需要一些时间，请耐心等待。
- 当前版本在处理文件夹时，仅处理其直接包含的文件，不会递归进入子文件夹进行校验。
  如果需要递归校验，脚本需要进一步修改（例如使用 os.walk()）。
- 此脚本依赖 Python 3.7 及以上版本的 `hashlib` (用于MD5计算) 和 `os` (用于路径操作和文件系统交互) 模块。
"""

import hashlib
import os


def calculate_file_md5(file_path):
    """
    计算并打印指定文件的MD5哈希值。

    参数:
    file_path (str): 文件的完整路径。

    返回:
    str: 文件的MD5哈希值 (十六进制字符串)。如果文件无效或计算过程中发生错误，则返回 None。
    """
    # 再次检查路径是否为文件以及文件是否存在
    # 虽然调用此函数前通常已经进行了检查，但作为独立函数，这样做可以增强其健壮性
    if not os.path.isfile(file_path):
        print(f"  错误: 路径 '{file_path}' 不是一个有效的文件或文件不存在。")
        return None

    md5_hash = hashlib.md5()
    # 定义读取缓冲区大小，例如 8KB。这个大小可以根据实际情况调整，
    # 对于大多数情况，8KB到64KB是一个合理的范围。
    buffer_size = 8192

    try:
        # 以二进制读取模式("rb")打开文件，这是计算哈希值的标准做法
        with open(file_path, "rb") as f:
            while True:
                # 分块读取文件内容
                data_chunk = f.read(buffer_size)
                if not data_chunk:
                    # 当read()返回空字节串时，表示已到达文件末尾
                    break
                # 更新MD5哈希对象
                md5_hash.update(data_chunk)

        # 获取计算得到的MD5值的十六进制表示
        hex_digest = md5_hash.hexdigest()

        # 打印文件的详细信息和其MD5值
        print(f"  文件路径: {file_path}")
        print(f"  MD5 哈希: {hex_digest}")
        return hex_digest
    except IOError as e:
        # 处理文件读取过程中可能发生的IO错误
        print(f"  错误: 读取文件 '{os.path.basename(file_path)}' 时发生IO错误: {e}")
        return None
    except Exception as e:
        # 处理计算过程中可能发生的其他未知错误
        print(f"  错误: 计算MD5时发生未知错误: {e}")
        return None


def process_directory_files(dir_path):
    """
    处理指定的文件夹，计算其中所有直接子文件的MD5值。
    此函数不递归进入子文件夹。

    参数:
    dir_path (str): 文件夹的完整路径。
    """
    print(f"\n>>> 开始扫描文件夹: '{dir_path}'")
    print("==================================================")

    files_to_process = []  # 用于存储文件夹内找到的直接文件路径
    try:
        # 遍历目录中的所有条目（文件名和子文件夹名）
        for item_name in os.listdir(dir_path):
            # 构建条目的完整路径
            item_path = os.path.join(dir_path, item_name)
            # 检查该完整路径是否指向一个文件
            if os.path.isfile(item_path):
                files_to_process.append(item_path)
    except OSError as e:
        # 处理访问文件夹时可能发生的OS错误（如权限问题）
        print(f"  错误: 访问文件夹 '{dir_path}' 时发生错误: {e}")
        print("==================================================")
        return

    if not files_to_process:
        # 如果文件夹为空或不包含任何直接文件
        print(f"  提示: 文件夹 '{os.path.basename(dir_path)}' 为空或不包含任何直接文件。")
        print("==================================================")
        return

    total_files = len(files_to_process)
    print(f"  在文件夹 '{os.path.basename(dir_path)}' 中找到 {total_files} 个直接文件。开始计算MD5...")
    print("--------------------------------------------------")

    success_count = 0  # 记录成功计算MD5的文件数量
    failure_count = 0  # 记录计算MD5失败的文件数量

    # 遍历找到的所有文件，并计算它们的MD5值
    for i, file_path_in_dir in enumerate(files_to_process):
        # 打印当前处理进度和文件名，使用 os.path.basename 获取纯文件名
        print(f"\n  处理中 [{i + 1}/{total_files}]: '{os.path.basename(file_path_in_dir)}'")
        if calculate_file_md5(file_path_in_dir):
            success_count += 1
        else:
            failure_count += 1

        # 在每个文件处理信息后添加一个小的分隔，除非是最后一个文件，以增强可读性
        if i < total_files - 1:
            print("  ------------------------------------------------")  # 注意缩进与上方信息对齐

    # 打印文件夹处理的总结信息
    print("\n--------------------------------------------------")  # 与上方分隔符对应
    print(f"文件夹 '{os.path.basename(dir_path)}' 扫描完成。")
    print(f"  总计文件数: {total_files}")
    print(f"  成功计算MD5: {success_count} 个")
    print(f"  计算MD5失败: {failure_count} 个")
    print("==================================================")


if __name__ == "__main__":
    # 打印美观的欢迎标题
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║          欢迎使用文件/文件夹MD5值校验工具 (Python 3.7)         ║")
    print("╚══════════════════════════════════════════════════════════════╝")

    try:
        # 获取用户输入的路径，并去除首尾可能存在的空白字符
        raw_path = input(
            "\n请输入要校验MD5值的文件或文件夹完整路径：\n(例如: D:\\downloads\\setup.exe 或 D:\\my_documents)\n> ").strip()

        if not raw_path:
            # 处理用户未输入任何内容的情况
            print("\n错误: 输入的路径不能为空。请重新运行脚本并提供有效路径。")
        else:
            # 将用户输入的路径（可能是相对路径）转换为绝对路径
            # 这样可以确保后续操作基于一个明确的、唯一的路径
            target_path = os.path.abspath(raw_path)
            print(f"  [INFO] 您输入的路径是: '{raw_path}', 程序将处理绝对路径: '{target_path}'")

            # 首先检查目标路径是否存在于文件系统中
            if not os.path.exists(target_path):
                print(f"\n错误: 路径 '{target_path}' 不存在。请检查路径是否正确。")
            # 如果路径存在，则判断它是文件还是文件夹
            elif os.path.isfile(target_path):
                # 如果是文件，则进行单个文件MD5计算
                print(f"\n>>> 开始处理单个文件: '{os.path.basename(target_path)}'")
                print("==================================================")
                print(f"  正在计算文件 '{os.path.basename(target_path)}' 的MD5值，请稍候...")
                if calculate_file_md5(target_path):
                    # MD5值已在 calculate_file_md5 函数内部打印
                    print("  MD5计算完成。")
                else:
                    # 如果 calculate_file_md5 返回None，表示计算失败
                    print(f"  未能计算文件 '{os.path.basename(target_path)}' 的MD5值。")
                print("==================================================")
            elif os.path.isdir(target_path):
                # 如果是文件夹，则调用处理文件夹的函数
                process_directory_files(target_path)
            else:
                # 这种情况比较少见：路径存在，但既不是文件也不是常规意义上的文件夹
                # (例如某些特殊的系统设备文件或损坏的快捷方式等)
                print(f"\n错误: 路径 '{target_path}' 不是一个常规的文件或文件夹。请检查路径类型。")

    except KeyboardInterrupt:
        # 优雅地处理用户通过 Ctrl+C 中断程序执行的情况
        print("\n\n操作已由用户取消。程序即将退出。")
    except Exception as e:
        # 捕获在主程序流程中其他所有未明确预料到的异常
        print(f"\n发生严重错误: {e}")
        print("程序执行遇到问题，请检查上述错误信息。")

    # 打印友好的结束语
    print("\n感谢使用本工具！祝您一切顺利！")
    print("==================================================")