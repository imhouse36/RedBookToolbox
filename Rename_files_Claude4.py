# -*- coding: utf-8 -*-
# 脚本功能:
# 本脚本用于递归重命名指定顶层文件夹及其所有子文件夹内的文件。
# 重命名规则："当前文件所在文件夹的名称_数字编号.原文件扩展名"
# 采用两阶段重命名策略，确保在同一文件夹内不会出现文件名冲突。
#
# 工作流程:
#   1. 提示用户输入要处理的顶层文件夹路径。
#   2. 校验文件夹路径是否存在。
#   3. 递归扫描所有子文件夹。
#   4. 对每个文件夹内的文件进行两阶段重命名：
#      第一阶段：重命名为临时名称（避免冲突）
#      第二阶段：重命名为最终目标名称
#   5. 输出处理结果和统计信息。
#
# 达成的结果:
# - 指定文件夹及其所有子文件夹内的文件将按照统一规则重命名。
# - 文件名格式："文件夹名_001.扩展名"、"文件夹名_002.扩展名" 等。
# - 保持原有的文件夹结构不变。
# - 控制台会输出详细的处理状态和最终的统计报告。
#
# 注意事项:
# - 重命名操作是不可逆的，建议在处理前备份重要文件。
# - 请确保对目标文件夹及其文件有读写权限。
# - 脚本会跳过隐藏文件和系统文件。
# - 如果文件夹名称包含特殊字符，会自动进行安全处理。

import pathlib
import time
import sys
import re
from typing import List, Tuple, Dict

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

def sanitize_folder_name(folder_name: str) -> str:
    """
    清理文件夹名称，移除或替换不适合用作文件名的字符。

    参数:
        folder_name (str): 原始文件夹名称。

    返回:
        str: 清理后的文件夹名称。
    """
    # 移除或替换Windows文件名中的非法字符
    illegal_chars = r'[<>:"/\|?*]'
    sanitized = re.sub(illegal_chars, '_', folder_name)
    
    # 移除前后空格和点号
    sanitized = sanitized.strip(' .')
    
    # 如果名称为空或只包含下划线，使用默认名称
    if not sanitized or sanitized.replace('_', '') == '':
        sanitized = 'folder'
    
    return sanitized

def get_all_folders_with_files(root_path: pathlib.Path) -> List[pathlib.Path]:
    """
    递归获取根目录下所有包含文件的文件夹。

    参数:
        root_path (pathlib.Path): 根目录路径。

    返回:
        List[pathlib.Path]: 包含文件的文件夹路径列表。
    """
    print(f"\n--- 扫描文件夹结构 '{root_path}' ---")
    
    folders_with_files = []
    total_folders = 0
    total_files = 0
    
    try:
        # 递归遍历所有文件夹
        for folder_path in root_path.rglob('*'):
            if folder_path.is_dir():
                total_folders += 1
                
                # 检查文件夹是否包含文件（非隐藏文件）
                files_in_folder = [
                    f for f in folder_path.iterdir()
                    if f.is_file() and not f.name.startswith('.')
                ]
                
                if files_in_folder:
                    folders_with_files.append(folder_path)
                    total_files += len(files_in_folder)
        
        print(f"扫描完成:")
        print(f"- 总文件夹数: {total_folders}")
        print(f"- 包含文件的文件夹数: {len(folders_with_files)}")
        print(f"- 总文件数: {total_files}")
        
        return folders_with_files
        
    except OSError as e:
        print(f"错误：无法扫描文件夹 '{root_path}': {e}")
        return []

def rename_files_in_folder(folder_path: pathlib.Path) -> Tuple[int, int]:
    """
    重命名指定文件夹内的所有文件，采用两阶段重命名策略。

    参数:
        folder_path (pathlib.Path): 要处理的文件夹路径。

    返回:
        Tuple[int, int]: (成功重命名的文件数量, 失败的文件数量)
    """
    try:
        # 获取文件夹内的所有文件（排除隐藏文件）
        files = [
            f for f in folder_path.iterdir()
            if f.is_file() and not f.name.startswith('.')
        ]
        
        if not files:
            return 0, 0
        
        # 清理文件夹名称
        folder_name = sanitize_folder_name(folder_path.name)
        
        success_count = 0
        failed_count = 0
        
        print(f"\n  处理文件夹: {folder_path}")
        print(f"  文件夹名称: {folder_name}")
        print(f"  文件数量: {len(files)}")
        
        # 第一阶段：重命名为临时名称
        temp_files = []
        for i, file_path in enumerate(files):
            try:
                temp_name = f"temp_{i:03d}_{file_path.suffix}"
                temp_path = folder_path / temp_name
                
                # 确保临时文件名不冲突
                counter = 1
                while temp_path.exists():
                    temp_name = f"temp_{i:03d}_{counter}_{file_path.suffix}"
                    temp_path = folder_path / temp_name
                    counter += 1
                
                file_path.rename(temp_path)
                temp_files.append((temp_path, file_path.suffix))
                
            except Exception as e:
                print(f"    ✗ 第一阶段失败: {file_path.name} - {e}")
                failed_count += 1
        
        # 第二阶段：重命名为最终目标名称
        for i, (temp_path, original_suffix) in enumerate(temp_files):
            try:
                final_name = f"{folder_name}_{i+1:03d}{original_suffix}"
                final_path = folder_path / final_name
                
                temp_path.rename(final_path)
                success_count += 1
                print(f"    ✓ {temp_path.name} → {final_name}")
                
            except Exception as e:
                print(f"    ✗ 第二阶段失败: {temp_path.name} - {e}")
                failed_count += 1
        
        return success_count, failed_count
        
    except Exception as e:
        print(f"    错误：处理文件夹 '{folder_path}' 时发生异常: {e}")
        return 0, len(files) if 'files' in locals() else 0

def process_all_folders(folders: List[pathlib.Path]) -> Dict[str, int]:
    """
    批量处理所有文件夹，重命名其中的文件。

    参数:
        folders (List[pathlib.Path]): 要处理的文件夹路径列表。

    返回:
        Dict[str, int]: 包含统计信息的字典。
    """
    print(f"\n--- 开始批量重命名文件 ---")
    
    total_success = 0
    total_failed = 0
    processed_folders = 0
    
    for i, folder_path in enumerate(folders, 1):
        progress = (i / len(folders)) * 100
        print(f"\n[进度: {progress:.1f}%] 处理文件夹 {i}/{len(folders)}")
        
        success, failed = rename_files_in_folder(folder_path)
        total_success += success
        total_failed += failed
        
        if success > 0 or failed > 0:
            processed_folders += 1
    
    return {
        'total_success': total_success,
        'total_failed': total_failed,
        'processed_folders': processed_folders,
        'total_folders': len(folders)
    }

def main():
    """
    主函数：控制程序的执行流程。
    """
    print("文件批量重命名工具")
    print("功能：递归重命名文件夹内所有文件为统一格式")
    print("=" * 50)
    
    # 记录脚本开始时间
    start_time = time.time()
    
    try:
        # 1. 获取用户输入：顶层文件夹路径
        root_folder = get_valid_folder_path_from_user(
            "请输入要处理的顶层文件夹路径: "
        )
        
        # 2. 扫描所有包含文件的文件夹
        folders_with_files = get_all_folders_with_files(root_folder)
        
        if not folders_with_files:
            print("\n未找到任何包含文件的文件夹。")
            return
        
        print(f"\n配置确认:")
        print(f"- 根目录: {root_folder}")
        print(f"- 待处理文件夹数: {len(folders_with_files)}")
        print(f"- 重命名规则: 文件夹名_编号.扩展名")
        print(f"- 编号格式: 001, 002, 003...")
        
        # 显示前几个文件夹作为示例
        print("\n待处理文件夹示例:")
        for folder in folders_with_files[:5]:
            relative_path = folder.relative_to(root_folder)
            print(f"  - {relative_path}")
        
        if len(folders_with_files) > 5:
            print(f"  ... 还有 {len(folders_with_files) - 5} 个文件夹")
        
        # 警告提示
        print("\n⚠️  重要提示:")
        print("- 此操作将永久重命名文件，建议先备份重要文件")
        print("- 重命名采用两阶段策略，确保不会出现文件名冲突")
        print("- 隐藏文件和系统文件将被跳过")
        
        # 确认处理
        confirm = input("\n确认开始处理？(y/N): ").strip().lower()
        if confirm not in ['y', 'yes', '是']:
            print("用户取消操作。")
            return
        
        # 3. 执行批量处理
        stats = process_all_folders(folders_with_files)
        
        # 4. 输出统计信息
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"\n{'='*60}")
        print("文件重命名完成统计报告:")
        print(f"{'='*60}")
        print(f"成功重命名文件数量: {stats['total_success']}")
        print(f"重命名失败文件数量: {stats['total_failed']}")
        print(f"处理的文件夹数量: {stats['processed_folders']}")
        print(f"扫描的文件夹总数: {stats['total_folders']}")
        print(f"总执行时间: {execution_time:.2f} 秒")
        
        if stats['total_success'] > 0:
            print(f"平均处理速度: {stats['total_success']/execution_time:.2f} 文件/秒")
        
        total_files = stats['total_success'] + stats['total_failed']
        if total_files > 0:
            success_rate = (stats['total_success'] / total_files) * 100
            print(f"成功率: {success_rate:.1f}%")
        
        print(f"{'='*60}")
        
        if stats['total_failed'] > 0:
            print("\n注意：部分文件重命名失败，可能原因：")
            print("- 文件被其他程序打开")
            print("- 文件权限不足")
            print("- 目标文件名已存在")
            print("- 文件名包含特殊字符")
            print("建议检查失败的文件并重试。")
        
        print("\n程序执行完毕。")
        
    except KeyboardInterrupt:
        print("\n\n用户中断程序执行。")
    except Exception as e:
        print(f"\n程序执行过程中发生意外错误: {e}")
        print("请检查输入参数和文件权限后重试。")

if __name__ == "__main__":
    main()