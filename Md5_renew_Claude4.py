# -*- coding: utf-8 -*-
# 脚本功能:
# 本脚本用于批量修改指定文件夹内图片文件的MD5值。
# 通过在每个图片文件的末尾附加随机字节数据来改变文件的MD5哈希值，
# 同时保持图片的可读性和显示效果不变。
#
# 工作流程:
#   1. 提示用户输入要处理的文件夹路径。
#   2. 校验文件夹路径是否存在。
#   3. 扫描文件夹内的所有图片文件。
#   4. 逐个处理每个图片文件：
#      a. 计算原始MD5值
#      b. 在文件末尾附加随机字节
#      c. 计算新的MD5值
#      d. 验证MD5值已改变
#   5. 输出处理结果和统计信息。
#
# 达成的结果:
# - 指定文件夹内所有图片文件的MD5值将被修改。
# - 图片文件的视觉效果和可用性保持不变。
# - 控制台会输出详细的处理状态和最终的统计报告。
#
# 注意事项:
# - 脚本支持常见图片格式（jpg, jpeg, png, webp, bmp, gif）。
# - 修改操作是不可逆的，建议在处理前备份重要文件。
# - 请确保对目标文件夹及其文件有读写权限。
# - 附加的随机数据量很小（16字节），对文件大小影响微乎其微。

import pathlib
import hashlib
import random
import time
import sys
from typing import List, Tuple, Optional

# 支持的图片格式常量
IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif')

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

def get_image_files_from_folder(folder_path: pathlib.Path) -> List[pathlib.Path]:
    """
    获取指定文件夹中的所有图片文件。

    参数:
        folder_path (pathlib.Path): 文件夹路径。

    返回:
        List[pathlib.Path]: 图片文件路径列表。
    """
    print(f"\n--- 扫描文件夹 '{folder_path}' ---")
    
    try:
        image_files = [
            f for f in folder_path.iterdir()
            if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
        ]
        
        print(f"找到 {len(image_files)} 张图片文件")
        
        if image_files:
            # 统计文件格式
            format_count = {}
            total_size = 0
            
            for img in image_files:
                ext = img.suffix.lower()
                format_count[ext] = format_count.get(ext, 0) + 1
                total_size += img.stat().st_size
            
            print("图片格式统计:")
            for ext, count in sorted(format_count.items()):
                print(f"  {ext}: {count} 张")
            
            print(f"总文件大小: {total_size / (1024*1024):.2f} MB")
        
        return image_files
        
    except OSError as e:
        print(f"错误：无法读取文件夹 '{folder_path}': {e}")
        return []

def calculate_file_md5(file_path: pathlib.Path) -> Optional[str]:
    """
    计算文件的MD5哈希值。

    参数:
        file_path (pathlib.Path): 文件路径。

    返回:
        Optional[str]: MD5哈希值（十六进制字符串），如果出错则返回None。
    """
    try:
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        print(f"    错误: 计算MD5失败 - {e}")
        return None

def modify_file_md5(file_path: pathlib.Path) -> bool:
    """
    通过在文件末尾附加随机字节来修改文件的MD5值。

    参数:
        file_path (pathlib.Path): 要修改的文件路径。

    返回:
        bool: 修改是否成功。
    """
    try:
        # 计算原始MD5
        original_md5 = calculate_file_md5(file_path)
        if original_md5 is None:
            return False
        
        # 生成16字节的随机数据
        random_bytes = bytes([random.randint(0, 255) for _ in range(16)])
        
        # 在文件末尾附加随机字节
        with open(file_path, "ab") as f:
            f.write(random_bytes)
        
        # 计算新的MD5
        new_md5 = calculate_file_md5(file_path)
        if new_md5 is None:
            return False
        
        # 验证MD5已改变
        if original_md5 != new_md5:
            print(f"    ✓ MD5修改成功")
            print(f"      原始: {original_md5}")
            print(f"      新值: {new_md5}")
            return True
        else:
            print(f"    ✗ MD5修改失败：值未改变")
            return False
            
    except PermissionError:
        print(f"    错误: 文件被占用或权限不足")
        return False
    except Exception as e:
        print(f"    错误: {e}")
        return False

def process_image_files(image_files: List[pathlib.Path]) -> Tuple[int, int]:
    """
    批量处理图片文件，修改它们的MD5值。

    参数:
        image_files (List[pathlib.Path]): 图片文件路径列表。

    返回:
        Tuple[int, int]: (成功处理的文件数量, 失败的文件数量)
    """
    print(f"\n--- 开始批量修改图片文件MD5值 ---")
    
    success_count = 0
    failed_count = 0
    total_files = len(image_files)
    
    for i, image_file in enumerate(image_files, 1):
        progress = (i / total_files) * 100
        file_size = image_file.stat().st_size / 1024  # KB
        
        print(f"  [进度: {progress:.1f}%] 处理文件: {image_file.name} ({file_size:.1f} KB)")
        
        if modify_file_md5(image_file):
            success_count += 1
        else:
            failed_count += 1
    
    return success_count, failed_count

def main():
    """
    主函数：控制程序的执行流程。
    """
    print("图片文件MD5值修改工具")
    print("功能：通过附加随机字节修改图片文件的MD5值")
    print("=" * 50)
    
    # 记录脚本开始时间
    start_time = time.time()
    
    try:
        # 1. 获取用户输入：文件夹路径
        folder_path = get_valid_folder_path_from_user(
            "请输入包含图片文件的文件夹路径: "
        )
        
        # 2. 获取文件夹中的图片文件
        image_files = get_image_files_from_folder(folder_path)
        
        if not image_files:
            print("\n未找到任何图片文件。")
            print(f"支持的图片格式: {', '.join(IMAGE_EXTENSIONS)}")
            return
        
        print(f"\n配置确认:")
        print(f"- 目标文件夹: {folder_path}")
        print(f"- 图片文件数量: {len(image_files)}")
        print(f"- 支持格式: {', '.join(IMAGE_EXTENSIONS)}")
        print(f"- 修改方式: 在文件末尾附加16字节随机数据")
        
        # 警告提示
        print("\n⚠️  重要提示:")
        print("- 此操作将永久修改文件，建议先备份重要文件")
        print("- 修改后的图片仍可正常查看和使用")
        print("- 文件大小会增加16字节")
        
        # 确认处理
        confirm = input("\n确认开始处理？(y/N): ").strip().lower()
        if confirm not in ['y', 'yes', '是']:
            print("用户取消操作。")
            return
        
        # 3. 执行批量处理
        success_count, failed_count = process_image_files(image_files)
        
        # 4. 输出统计信息
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"\n{'='*60}")
        print("图片MD5修改完成统计报告:")
        print(f"{'='*60}")
        print(f"成功处理文件数量: {success_count}")
        print(f"处理失败文件数量: {failed_count}")
        print(f"总文件数量: {len(image_files)}")
        print(f"总执行时间: {execution_time:.2f} 秒")
        
        if success_count > 0:
            print(f"平均处理速度: {success_count/execution_time:.2f} 文件/秒")
            print(f"总增加文件大小: {success_count * 16} 字节")
        
        success_rate = (success_count / len(image_files)) * 100 if image_files else 0
        print(f"成功率: {success_rate:.1f}%")
        
        print(f"{'='*60}")
        
        if failed_count > 0:
            print("\n注意：部分文件处理失败，可能原因：")
            print("- 文件被其他程序打开")
            print("- 文件权限不足")
            print("- 文件损坏或格式异常")
            print("建议检查失败的文件并重试。")
        
        print("\n程序执行完毕。")
        
    except KeyboardInterrupt:
        print("\n\n用户中断程序执行。")
    except Exception as e:
        print(f"\n程序执行过程中发生意外错误: {e}")
        print("请检查输入参数和文件权限后重试。")

if __name__ == "__main__":
    main()