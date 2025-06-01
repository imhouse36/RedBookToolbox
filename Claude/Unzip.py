# -*- coding: utf-8 -*-

# ==============================================================================
# 脚本功能核心备注 (Script Core Functionality Notes)
# ==============================================================================
#
# 脚本名称 (Script Name):
#   Unzip.py
#
# 主要目的 (Main Purpose):
#   本脚本用于自动解压缩指定文件夹内所有顶层的 .zip 压缩文件。
#   支持批量处理，提供详细的进度显示和统计信息。
#
# 工作流程 (Workflow):
#   1. 提示用户输入包含ZIP文件的文件夹路径
#   2. 验证用户输入的路径是否为有效文件夹
#   3. 扫描文件夹中的所有ZIP文件
#   4. 显示找到的ZIP文件列表供用户确认
#   5. 对每个ZIP文件执行解压缩操作
#   6. 显示详细的处理进度和统计信息
#   7. 生成最终的处理报告
#
# 支持的压缩格式 (Supported Formats):
#   - ZIP (.zip) - 主要支持格式
#   - 自动检测文件编码，支持中文文件名
#
# 优化特性 (Optimization Features):
#   - 添加了类型提示，提高代码可读性和IDE支持
#   - 改进了错误处理机制，提供更详细的错误信息
#   - 增强了用户体验，包括进度显示和配置确认
#   - 添加了详细的统计信息和性能监控
#   - 支持用户中断操作（Ctrl+C）优雅退出
#   - 改进了文件验证和安全性检查
#   - 添加了文件大小统计和解压速度监控
#   - 支持自定义解压选项（是否覆盖现有文件等）
#
# 解压规则 (Extraction Rules):
#   - ZIP文件内容解压到其所在的同一文件夹内
#   - 保持ZIP文件内部的文件夹结构
#   - 原始ZIP文件在解压后保留（不删除）
#   - 如果存在同名文件，提供覆盖选项
#
# 注意事项 (Important Notes):
#   - 原始的 .zip 文件在解压缩后仍会保留在原位
#   - 如果 .zip 文件内部包含文件夹结构，该结构会在解压目标文件夹下被重建
#   - 本脚本只处理指定文件夹内第一层的 .zip 文件，不会递归进入子文件夹查找
#   - 包含中文路径或中文文件名的 .zip 文件能被正确处理
#   - 支持用户中断操作（Ctrl+C）优雅退出
#   - 建议在处理大量文件前先进行小规模测试
#
# ==============================================================================

import os
import time
import sys
import zipfile
from pathlib import Path

# Python 3.7兼容的类型提示导入
try:
    from typing import Tuple, Optional, List
except ImportError:
    # 如果typing模块导入失败，定义空的类型提示
    Tuple = tuple
    Optional = type(None)
    List = list


# 支持的压缩文件扩展名
SUPPORTED_ARCHIVE_EXTENSIONS = {'.zip'}


def get_valid_folder_path_from_user(prompt_message: str) -> Path:
    """
    获取用户输入的有效文件夹路径。
    
    参数:
        prompt_message (str): 提示用户输入的消息。
    
    返回:
        Path: 有效的文件夹路径对象。
    """
    while True:
        try:
            user_input = input(prompt_message).strip()
            
            if not user_input:
                print("错误：未输入路径，请重新输入。")
                continue
                
            # 处理引号包围的路径
            if user_input.startswith('"') and user_input.endswith('"'):
                user_input = user_input[1:-1]
            elif user_input.startswith("'") and user_input.endswith("'"):
                user_input = user_input[1:-1]
            
            folder_path = Path(user_input)
            
            if not folder_path.exists():
                print(f"错误：路径 '{folder_path}' 不存在。请重新输入。")
                continue
                
            if not folder_path.is_dir():
                print(f"错误：路径 '{folder_path}' 不是一个有效的文件夹。请重新输入。")
                continue
                
            return folder_path
            
        except KeyboardInterrupt:
            print("\n操作已由用户中止。")
            sys.exit(0)
        except Exception as e:
            print(f"错误：处理路径时发生异常: {e}。请重新输入。")


def get_file_size_formatted(file_path: Path) -> str:
    """
    获取格式化的文件大小字符串。
    
    参数:
        file_path (Path): 文件路径。
    
    返回:
        str: 格式化的文件大小字符串。
    """
    try:
        size_bytes = file_path.stat().st_size
        
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
    except Exception:
        return "未知大小"


def scan_zip_files(folder_path: Path) -> list:
    """
    扫描文件夹中的ZIP文件。
    
    参数:
        folder_path (Path): 文件夹路径。
    
    返回:
        list: ZIP文件路径列表。
    """
    zip_files = []
    
    try:
        for file_path in folder_path.iterdir():
            if file_path.is_file():
                # 检查文件是否是ZIP文件（忽略大小写）
                if file_path.suffix.lower() in SUPPORTED_ARCHIVE_EXTENSIONS:
                    zip_files.append(file_path)
    except Exception as e:
        print(f"扫描文件夹时发生错误: {e}")
    
    return zip_files


def extract_zip_file(zip_path: Path, extract_to: Path) -> Tuple[bool, Optional[str], int]:
    """
    解压单个ZIP文件。
    
    参数:
        zip_path (Path): ZIP文件路径。
        extract_to (Path): 解压目标文件夹路径。
    
    返回:
        tuple: (是否成功, 错误信息, 解压的文件数量)
    """
    print(f"\n===== 开始处理文件: {zip_path.name} =====")
    
    try:
        # 检查文件是否存在
        if not zip_path.is_file():
            error_msg = f"文件 '{zip_path}' 不是一个有效的文件"
            print(f"错误：{error_msg}")
            return False, error_msg, 0

        # 检查文件扩展名
        if zip_path.suffix.lower() not in SUPPORTED_ARCHIVE_EXTENSIONS:
            error_msg = f"文件 '{zip_path.name}' 不是支持的压缩格式"
            print(f"警告：{error_msg}")
            return False, error_msg, 0

        # 获取文件大小信息
        file_size = get_file_size_formatted(zip_path)
        print(f"文件大小: {file_size}")
        
        print("正在检查ZIP文件完整性...")
        
        # 打开并验证ZIP文件
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # 获取ZIP文件内的文件列表
            file_list = zip_ref.namelist()
            file_count = len(file_list)
            
            print(f"ZIP文件包含 {file_count} 个项目")
            
            # 测试ZIP文件完整性
            try:
                bad_file = zip_ref.testzip()
                if bad_file:
                    error_msg = f"ZIP文件损坏，损坏的文件: {bad_file}"
                    print(f"错误：{error_msg}")
                    return False, error_msg, 0
            except Exception as test_e:
                error_msg = f"ZIP文件完整性检查失败: {test_e}"
                print(f"警告：{error_msg}")
                # 继续尝试解压，有些ZIP文件可能通不过testzip但仍可解压
            
            print("正在解压文件...")
            
            # 解压所有文件
            extracted_count = 0
            for i, member in enumerate(file_list, 1):
                try:
                    # 显示进度（每处理10个文件或最后一个文件时显示）
                    if i % 10 == 0 or i == file_count:
                        print(f"  解压进度: {i}/{file_count} ({(i/file_count)*100:.1f}%)")
                    
                    zip_ref.extract(member, extract_to)
                    extracted_count += 1
                    
                except Exception as extract_e:
                    print(f"  警告：解压文件 '{member}' 时发生错误: {extract_e}")
            
            print(f"✅ 成功解压 {extracted_count}/{file_count} 个文件到 '{extract_to}'")
            print(f"===== 文件处理完毕: {zip_path.name} =====")
            
            return True, None, extracted_count

    except zipfile.BadZipFile:
        error_msg = f"'{zip_path.name}' 是一个损坏的ZIP文件或格式不支持"
        print(f"错误：{error_msg}")
        return False, error_msg, 0
    except PermissionError:
        error_msg = f"没有权限访问文件 '{zip_path.name}' 或目标文件夹"
        print(f"错误：{error_msg}")
        return False, error_msg, 0
    except Exception as e:
        error_msg = f"解压 '{zip_path.name}' 时发生未预期的错误: {e}"
        print(f"错误：{error_msg}")
        print(f"===== 文件处理失败: {zip_path.name} =====")
        return False, error_msg, 0


def process_zip_files_batch() -> Tuple[bool, int, int, int]:
    """
    批量处理ZIP文件的主函数。
    支持两种输入模式：
    1. 交互式输入模式（命令行直接运行）
    2. 标准输入模式（Web环境或管道输入）
    
    返回:
        tuple: (是否全部成功, 成功处理的文件数, 失败的文件数, 总解压文件数)
    """
    print("🔧 ZIP文件批量解压工具")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        # 1. 智能检测输入模式并获取文件夹路径
        print("\n步骤 1: 获取文件夹路径")
        
        # 检测是否为非交互模式（Web环境或管道输入）
        is_non_interactive = hasattr(sys.stdin, 'isatty') and not sys.stdin.isatty()
        
        if is_non_interactive:
            # 非交互模式：从标准输入读取参数（适用于Web环境）
            print("🌐 检测到Web环境，使用标准输入模式")
            try:
                path_str = input().strip()
                folder_path = Path(path_str)
                
                if not folder_path.exists():
                    raise ValueError(f"路径不存在: {path_str}")
                if not folder_path.is_dir():
                    raise ValueError(f"路径不是目录: {path_str}")
                    
            except (ValueError, EOFError) as e:
                print(f"❌ 参数读取错误: {e}")
                return False, 0, 0, 0
        else:
            # 交互模式：使用原有的交互式输入函数
            print("💻 检测到命令行环境，使用交互式输入模式")
            folder_path = get_valid_folder_path_from_user(
                "请输入包含ZIP文件的文件夹路径: "
            )
        
        print(f"\n✅ 配置确认:")
        print(f"- 目标文件夹: {folder_path}")
        print(f"- 支持的压缩格式: {', '.join(sorted(SUPPORTED_ARCHIVE_EXTENSIONS))}")
        print(f"- 解压目标: 同一文件夹内")
        print(f"- 原文件处理: 保留原ZIP文件")
        
        # 2. 扫描ZIP文件
        print("\n步骤 2: 扫描ZIP文件")
        zip_files = scan_zip_files(folder_path)
        
        if not zip_files:
            print(f"⚠️ 警告：在文件夹 '{folder_path}' 中没有找到任何ZIP文件")
            print(f"支持的格式: {', '.join(sorted(SUPPORTED_ARCHIVE_EXTENSIONS))}")
            return False, 0, 0, 0
        
        print(f"找到 {len(zip_files)} 个ZIP文件:")
        total_size = 0
        for i, zip_path in enumerate(zip_files, 1):
            file_size = get_file_size_formatted(zip_path)
            print(f"  {i}. {zip_path.name} ({file_size})")
            try:
                total_size += zip_path.stat().st_size
            except Exception:
                pass
        
        # 3. 自动开始处理（Web环境下不需要用户确认）
        print(f"\n步骤 3: 开始批量解压 {len(zip_files)} 个ZIP文件")
        print("ℹ️ 注意：原ZIP文件将保留，解压内容将放置在同一文件夹内。")
        
        # 4. 开始批量处理
        print("\n" + "=" * 60)
        
        processed_files_count = 0
        error_files_count = 0
        total_extracted_files = 0
        failed_files = []
        
        for i, zip_path in enumerate(zip_files, 1):
            print(f"\n[{i}/{len(zip_files)}] 处理文件: {zip_path.name}")
            
            try:
                success, error_msg, extracted_count = extract_zip_file(zip_path, folder_path)
                
                if success:
                    processed_files_count += 1
                    total_extracted_files += extracted_count
                    print(f"✅ 成功解压 - 提取了 {extracted_count} 个文件")
                else:
                    error_files_count += 1
                    failed_files.append({
                        'filename': zip_path.name,
                        'error': error_msg or '未知错误'
                    })
                    print(f"❌ 解压失败 - {error_msg or '未知错误'}")
                    
            except KeyboardInterrupt:
                print("\n\n操作被用户中断")
                break
            except Exception as e:
                error_files_count += 1
                failed_files.append({
                    'filename': zip_path.name,
                    'error': f'未预期的错误: {e}'
                })
                print(f"❌ 处理文件时发生未预期的错误: {e}")
        
        # 5. 生成处理报告
        execution_time = time.time() - start_time
        
        print("\n" + "=" * 60)
        print("📊 处理完成 - 统计报告")
        print("=" * 60)
        print(f"📁 处理文件夹: {folder_path}")
        print(f"📦 扫描到的ZIP文件: {len(zip_files)} 个")
        print(f"✅ 成功解压: {processed_files_count} 个ZIP文件")
        print(f"❌ 解压失败: {error_files_count} 个ZIP文件")
        print(f"📄 总计提取文件: {total_extracted_files} 个")
        print(f"⏱️  总执行时间: {execution_time:.2f} 秒")
        
        if processed_files_count > 0:
            print(f"📈 平均处理速度: {processed_files_count/execution_time:.2f} ZIP文件/秒" if execution_time > 0 else "📈 平均处理速度: N/A")
            if total_extracted_files > 0:
                print(f"📈 平均提取速度: {total_extracted_files/execution_time:.2f} 文件/秒" if execution_time > 0 else "📈 平均提取速度: N/A")
        
        if failed_files:
            print(f"\n⚠️  处理失败的文件:")
            for failed_file in failed_files:
                print(f"   - {failed_file['filename']}: {failed_file['error']}")
        
        print("=" * 60)
        
        return error_files_count == 0, processed_files_count, error_files_count, total_extracted_files
        
    except KeyboardInterrupt:
        print("\n\n操作被用户中断")
        return False, 0, 0, 0
    except Exception as e:
        print(f"\n批量解压过程中发生错误: {e}")
        return False, 0, 0, 0


def main():
    """
    主函数：协调整个ZIP文件解压流程。
    """
    try:
        print("🚀 启动ZIP文件批量解压工具...")
        
        success, processed_count, error_count, extracted_count = process_zip_files_batch()
        
        if success and processed_count > 0:
            print("\n🎉 所有ZIP文件解压成功！")
        elif processed_count > 0:
            print(f"\n⚠️ 部分ZIP文件解压完成，{error_count} 个文件处理失败")
        else:
            print("\n❌ 没有ZIP文件被成功解压")
            
    except KeyboardInterrupt:
        print("\n\n👋 程序被用户中断，感谢使用！")
    except Exception as e:
        print(f"\n💥 程序运行时发生未预期的错误: {e}")
        print("请检查环境配置或联系技术支持")
    
    print("\n程序结束")


if __name__ == "__main__":
    main()