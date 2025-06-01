# -*- coding: utf-8 -*-
# 脚本功能:
# 本脚本用于自动解压缩指定文件夹内所有顶层的 .zip 压缩文件。
# 每个压缩文件会被解压到以其文件名（不含扩展名）命名的子文件夹中。
# 解压完成后，原始的 .zip 文件将被删除。
#
# 工作流程:
#   1. 提示用户输入包含 .zip 文件的文件夹路径。
#   2. 校验文件夹路径是否存在。
#   3. 扫描文件夹内的所有 .zip 文件（仅顶层，不递归）。
#   4. 逐个处理每个 .zip 文件：
#      a. 创建以压缩文件名命名的目标文件夹
#      b. 解压文件到目标文件夹
#      c. 验证解压是否成功
#      d. 删除原始 .zip 文件
#   5. 输出处理结果和统计信息。
#
# 达成的结果:
# - 指定文件夹内所有 .zip 文件将被解压到对应的子文件夹中。
# - 原始 .zip 文件将被删除（节省磁盘空间）。
# - 控制台会输出详细的处理状态和最终的统计报告。
#
# 注意事项:
# - 解压操作会覆盖同名文件，请确保目标文件夹内没有重要的同名文件。
# - 请确保对目标文件夹有读写权限。
# - 如果压缩文件损坏或密码保护，解压将失败但不会影响其他文件的处理。
# - 脚本仅处理顶层的 .zip 文件，不会递归处理子文件夹内的压缩文件。

import pathlib
import zipfile
import time
import sys
from typing import List, Tuple, Optional

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

def get_zip_files_from_folder(folder_path: pathlib.Path) -> List[pathlib.Path]:
    """
    获取指定文件夹中的所有 .zip 文件（仅顶层，不递归）。

    参数:
        folder_path (pathlib.Path): 文件夹路径。

    返回:
        List[pathlib.Path]: .zip 文件路径列表。
    """
    print(f"\n--- 扫描文件夹 '{folder_path}' ---")
    
    try:
        zip_files = [
            f for f in folder_path.iterdir()
            if f.is_file() and f.suffix.lower() == '.zip'
        ]
        
        print(f"找到 {len(zip_files)} 个 .zip 文件")
        
        if zip_files:
            total_size = 0
            for zip_file in zip_files:
                file_size = zip_file.stat().st_size
                total_size += file_size
                print(f"  - {zip_file.name} ({file_size / (1024*1024):.2f} MB)")
            
            print(f"总压缩文件大小: {total_size / (1024*1024):.2f} MB")
        
        return zip_files
        
    except OSError as e:
        print(f"错误：无法读取文件夹 '{folder_path}': {e}")
        return []

def extract_zip_file(zip_path: pathlib.Path, extract_to: pathlib.Path) -> bool:
    """
    解压单个 .zip 文件到指定目录。

    参数:
        zip_path (pathlib.Path): .zip 文件路径。
        extract_to (pathlib.Path): 解压目标目录。

    返回:
        bool: 解压是否成功。
    """
    try:
        # 创建目标目录
        extract_to.mkdir(parents=True, exist_ok=True)
        
        # 解压文件
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # 检查压缩文件是否有密码保护
            try:
                zip_ref.testzip()
            except RuntimeError as e:
                if "Bad password" in str(e) or "password required" in str(e).lower():
                    print(f"    ✗ 解压失败：文件需要密码")
                    return False
                else:
                    print(f"    ✗ 解压失败：压缩文件损坏 - {e}")
                    return False
            
            # 获取压缩文件信息
            file_list = zip_ref.namelist()
            total_files = len(file_list)
            
            print(f"    解压 {total_files} 个文件到: {extract_to.name}")
            
            # 解压所有文件
            zip_ref.extractall(extract_to)
            
            # 验证解压结果
            extracted_files = list(extract_to.rglob('*'))
            extracted_file_count = len([f for f in extracted_files if f.is_file()])
            
            print(f"    ✓ 成功解压 {extracted_file_count} 个文件")
            
            return True
            
    except zipfile.BadZipFile:
        print(f"    ✗ 解压失败：不是有效的 ZIP 文件")
        return False
    except PermissionError:
        print(f"    ✗ 解压失败：权限不足")
        return False
    except Exception as e:
        print(f"    ✗ 解压失败：{e}")
        return False

def process_zip_files(zip_files: List[pathlib.Path]) -> Tuple[int, int]:
    """
    批量处理 .zip 文件：解压并删除原文件。

    参数:
        zip_files (List[pathlib.Path]): .zip 文件路径列表。

    返回:
        Tuple[int, int]: (成功处理的文件数量, 失败的文件数量)
    """
    print(f"\n--- 开始批量解压 ZIP 文件 ---")
    
    success_count = 0
    failed_count = 0
    total_files = len(zip_files)
    
    for i, zip_file in enumerate(zip_files, 1):
        progress = (i / total_files) * 100
        file_size = zip_file.stat().st_size / (1024*1024)  # MB
        
        print(f"\n  [进度: {progress:.1f}%] 处理文件: {zip_file.name} ({file_size:.2f} MB)")
        
        # 确定解压目标文件夹
        extract_folder_name = zip_file.stem  # 文件名（不含扩展名）
        extract_path = zip_file.parent / extract_folder_name
        
        # 检查目标文件夹是否已存在
        if extract_path.exists():
            print(f"    警告：目标文件夹 '{extract_folder_name}' 已存在，将覆盖其中的同名文件")
        
        # 解压文件
        if extract_zip_file(zip_file, extract_path):
            # 解压成功，删除原始 ZIP 文件
            try:
                zip_file.unlink()
                print(f"    ✓ 已删除原始文件: {zip_file.name}")
                success_count += 1
            except Exception as e:
                print(f"    ⚠️  解压成功但删除原文件失败: {e}")
                success_count += 1  # 仍然算作成功，因为解压完成了
        else:
            failed_count += 1
    
    return success_count, failed_count

def main():
    """
    主函数：控制程序的执行流程。
    """
    print("ZIP 文件批量解压工具")
    print("功能：自动解压文件夹内所有 ZIP 文件并删除原文件")
    print("=" * 50)
    
    # 记录脚本开始时间
    start_time = time.time()
    
    try:
        # 1. 获取用户输入：文件夹路径
        folder_path = get_valid_folder_path_from_user(
            "请输入包含 ZIP 文件的文件夹路径: "
        )
        
        # 2. 获取文件夹中的 ZIP 文件
        zip_files = get_zip_files_from_folder(folder_path)
        
        if not zip_files:
            print("\n未找到任何 .zip 文件。")
            return
        
        print(f"\n配置确认:")
        print(f"- 目标文件夹: {folder_path}")
        print(f"- ZIP 文件数量: {len(zip_files)}")
        print(f"- 解压策略: 每个 ZIP 文件解压到同名文件夹")
        print(f"- 处理完成后: 删除原始 ZIP 文件")
        
        # 警告提示
        print("\n⚠️  重要提示:")
        print("- 解压操作会覆盖目标文件夹中的同名文件")
        print("- 原始 ZIP 文件将在解压成功后被删除")
        print("- 如果 ZIP 文件需要密码或已损坏，将跳过处理")
        print("- 建议在处理前备份重要文件")
        
        # 确认处理
        confirm = input("\n确认开始处理？(y/N): ").strip().lower()
        if confirm not in ['y', 'yes', '是']:
            print("用户取消操作。")
            return
        
        # 3. 执行批量处理
        success_count, failed_count = process_zip_files(zip_files)
        
        # 4. 输出统计信息
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"\n{'='*60}")
        print("ZIP 文件解压完成统计报告:")
        print(f"{'='*60}")
        print(f"成功处理文件数量: {success_count}")
        print(f"处理失败文件数量: {failed_count}")
        print(f"总文件数量: {len(zip_files)}")
        print(f"总执行时间: {execution_time:.2f} 秒")
        
        if success_count > 0:
            print(f"平均处理速度: {success_count/execution_time:.2f} 文件/秒")
        
        success_rate = (success_count / len(zip_files)) * 100 if zip_files else 0
        print(f"成功率: {success_rate:.1f}%")
        
        print(f"{'='*60}")
        
        if failed_count > 0:
            print("\n注意：部分文件处理失败，可能原因：")
            print("- ZIP 文件需要密码")
            print("- ZIP 文件已损坏")
            print("- 文件权限不足")
            print("- 磁盘空间不足")
            print("建议检查失败的文件并重试。")
        
        if success_count > 0:
            print(f"\n✓ 成功解压 {success_count} 个文件")
            print(f"✓ 已删除 {success_count} 个原始 ZIP 文件")
            print("所有解压的文件已保存在对应的子文件夹中。")
        
        print("\n程序执行完毕。")
        
    except KeyboardInterrupt:
        print("\n\n用户中断程序执行。")
    except Exception as e:
        print(f"\n程序执行过程中发生意外错误: {e}")
        print("请检查输入参数和文件权限后重试。")

if __name__ == "__main__":
    main()