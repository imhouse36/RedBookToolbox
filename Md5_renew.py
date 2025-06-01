# -*- coding: utf-8 -*-

# ==============================================================================
# 脚本功能核心备注 (Script Core Functionality Notes)
# ==============================================================================
#
# 脚本名称 (Script Name):
#   Md5_renew_Claude4.py (Claude4优化版)
#
# 主要目的 (Main Purpose):
#   本脚本用于批量修改指定文件夹内图片文件的MD5值，通过在文件末尾附加随机字节来实现。
#   这种方法不会影响图片的显示效果，但会改变文件的MD5哈希值。
#
# 工作流程 (Workflow):
#   1. 提示用户输入包含图片文件的文件夹路径
#   2. 验证用户输入的路径是否为有效文件夹
#   3. 扫描文件夹中的所有支持的图片文件
#   4. 对每个图片文件在末尾附加随机字节
#   5. 显示详细的处理进度和统计信息
#   6. 生成最终的处理报告，包括MD5值变化对比
#
# 支持的图片格式 (Supported Image Formats):
#   - JPEG (.jpg, .jpeg)
#   - PNG (.png)
#   - BMP (.bmp)
#   - GIF (.gif)
#   - TIFF (.tiff, .tif)
#   - WEBP (.webp)
#
# 优化特性 (Optimization Features):
#   - 添加了类型提示，提高代码可读性和IDE支持
#   - 改进了错误处理机制，提供更详细的错误信息
#   - 增强了用户体验，包括进度显示和配置确认
#   - 添加了详细的统计信息和性能监控
#   - 支持用户中断操作（Ctrl+C）优雅退出
#   - 改进了文件验证和安全性检查
#   - 添加了MD5值变化对比功能
#   - 支持自定义随机字节数量
#
# 注意事项 (Important Notes):
#   - 此操作会直接修改原始图片文件，请确保在操作前备份重要数据
#   - 修改后的图片文件大小会略微增加（增加的字节数等于附加的随机字节数）
#   - 图片的视觉效果不会受到影响，但文件的MD5值会发生变化
#   - 支持用户中断操作（Ctrl+C）优雅退出
#   - 建议在处理大量文件前先进行小规模测试
#
# ==============================================================================

import os
import time
import sys
import hashlib
import random
from pathlib import Path

# Python 3.7兼容的类型提示导入
try:
    from typing import Tuple, Optional, Set
except ImportError:
    # 如果typing模块导入失败，定义空的类型提示
    Tuple = tuple
    Optional = type(None)
    Set = set


# 支持的图片文件扩展名
SUPPORTED_IMAGE_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.tif', '.webp'
}

# 默认附加的随机字节数
DEFAULT_RANDOM_BYTES = 16


def calculate_file_md5(file_path: Path) -> Optional[str]:
    """
    计算文件的MD5哈希值。
    
    参数:
        file_path (Path): 文件路径。
    
    返回:
        str 或 None: 文件的MD5哈希值，如果计算失败则返回None。
    """
    try:
        hash_md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            # 分块读取文件以处理大文件
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        print(f"计算文件 '{file_path.name}' 的MD5时发生错误: {e}")
        return None


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


def get_random_bytes_count() -> int:
    """
    获取用户指定的随机字节数量。
    
    返回:
        int: 随机字节数量。
    """
    while True:
        try:
            user_input = input(f"请输入要附加的随机字节数量 (默认: {DEFAULT_RANDOM_BYTES}, 范围: 1-1024): ").strip()
            
            if not user_input:
                return DEFAULT_RANDOM_BYTES
            
            bytes_count = int(user_input)
            
            if bytes_count < 1 or bytes_count > 1024:
                print("错误：随机字节数量必须在1-1024之间。请重新输入。")
                continue
                
            return bytes_count
            
        except ValueError:
            print("错误：请输入有效的数字。")
        except KeyboardInterrupt:
            print("\n操作已由用户中止。")
            sys.exit(0)
        except Exception as e:
            print(f"错误：处理输入时发生异常: {e}。请重新输入。")


def modify_image_md5(file_path: Path, random_bytes_count: int = DEFAULT_RANDOM_BYTES) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    通过在文件末尾附加随机字节来修改图片文件的MD5值。
    
    参数:
        file_path (Path): 图片文件路径。
        random_bytes_count (int): 要附加的随机字节数量。
    
    返回:
        tuple: (是否成功, 原始MD5值, 新MD5值)
    """
    print(f"\n===== 开始处理文件: {file_path.name} =====")
    
    try:
        # 检查文件是否存在
        if not file_path.is_file():
            print(f"错误：文件 '{file_path}' 不是一个有效的文件。跳过...")
            return False, None, None

        # 检查文件扩展名
        if file_path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
            print(f"警告：文件 '{file_path.name}' 不是支持的图片格式。跳过...")
            return False, None, None

        # 计算原始MD5值
        print("正在计算原始MD5值...")
        original_md5 = calculate_file_md5(file_path)
        if original_md5 is None:
            print(f"错误：无法计算文件 '{file_path.name}' 的原始MD5值")
            return False, None, None
        
        print(f"原始MD5值: {original_md5}")

        # 生成随机字节
        print(f"正在生成 {random_bytes_count} 个随机字节...")
        random_bytes = bytes([random.randint(0, 255) for _ in range(random_bytes_count)])

        # 获取原始文件大小
        original_size = file_path.stat().st_size

        # 在文件末尾附加随机字节
        print("正在修改文件...")
        with open(file_path, 'ab') as f:
            f.write(random_bytes)

        # 计算新的MD5值
        print("正在计算新MD5值...")
        new_md5 = calculate_file_md5(file_path)
        if new_md5 is None:
            print(f"错误：无法计算文件 '{file_path.name}' 的新MD5值")
            return False, original_md5, None
        
        print(f"新MD5值: {new_md5}")
        
        # 验证文件大小变化
        new_size = file_path.stat().st_size
        size_increase = new_size - original_size
        
        if size_increase == random_bytes_count:
            print(f"✅ 成功！文件大小增加了 {size_increase} 字节")
            print(f"MD5值已从 {original_md5} 变更为 {new_md5}")
            print(f"===== 文件处理完毕: {file_path.name} =====")
            return True, original_md5, new_md5
        else:
            print(f"警告：文件大小变化异常，预期增加 {random_bytes_count} 字节，实际增加 {size_increase} 字节")
            return False, original_md5, new_md5

    except PermissionError:
        print(f"错误：没有权限修改文件 '{file_path.name}'")
        return False, None, None
    except Exception as e:
        print(f"\n处理文件 '{file_path.name}' 时发生错误：{e}")
        print("请检查文件是否被其他程序占用、是否有读写权限。将跳过此文件。")
        print(f"===== 文件处理失败: {file_path.name} =====")
        return False, None, None


def scan_image_files(folder_path: Path) -> list:
    """
    扫描文件夹中的图片文件。
    
    参数:
        folder_path (Path): 文件夹路径。
    
    返回:
        list: 图片文件路径列表。
    """
    image_files = []
    
    try:
        for file_path in folder_path.iterdir():
            if file_path.is_file():
                # 检查文件是否是支持的图片格式（忽略大小写）
                if file_path.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS:
                    image_files.append(file_path)
    except Exception as e:
        print(f"扫描文件夹时发生错误: {e}")
    
    return image_files


def process_images_batch() -> Tuple[bool, int, int, int]:
    """
    批量处理图片文件的主函数。
    
    返回:
        tuple: (是否全部成功, 成功处理的文件数, 失败的文件数, 总字节增加量)
    """
    print("图片MD5值修改工具 (Claude4优化版)")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        # 1. 获取用户输入的文件夹路径
        print("\n步骤 1: 获取文件夹路径")
        folder_path = get_valid_folder_path_from_user(
            "请输入包含图片文件的文件夹目录路径: "
        )
        
        # 2. 获取随机字节数量
        print("\n步骤 2: 配置随机字节数量")
        random_bytes_count = get_random_bytes_count()
        
        print(f"\n配置确认:")
        print(f"- 目标文件夹: {folder_path}")
        print(f"- 支持的图片格式: {', '.join(sorted(SUPPORTED_IMAGE_EXTENSIONS))}")
        print(f"- 随机字节数量: {random_bytes_count} 字节")
        print(f"- 操作内容: 在每个图片文件末尾附加随机字节以修改MD5值")
        
        # 3. 扫描图片文件
        print("\n步骤 3: 扫描图片文件")
        image_files = scan_image_files(folder_path)
        
        if not image_files:
            print(f"警告：在文件夹 '{folder_path}' 中没有找到任何支持的图片文件")
            print(f"支持的格式: {', '.join(sorted(SUPPORTED_IMAGE_EXTENSIONS))}")
            return False, 0, 0, 0
        
        print(f"找到 {len(image_files)} 个图片文件:")
        for i, file_path in enumerate(image_files, 1):
            file_size = file_path.stat().st_size
            print(f"  {i}. {file_path.name} ({file_size:,} 字节)")
        
        # 4. 用户确认
        print(f"\n步骤 4: 确认处理")
        print("⚠️  警告：此操作将直接修改图片文件内容，建议先备份重要数据！")
        print(f"每个文件将增加 {random_bytes_count} 字节，总计将增加 {len(image_files) * random_bytes_count:,} 字节")
        
        try:
            confirm = input(f"\n确认处理这 {len(image_files)} 个文件吗？(y/N): ").strip().lower()
            if confirm not in ['y', 'yes', '是']:
                print("操作已取消")
                return False, 0, 0, 0
        except KeyboardInterrupt:
            print("\n操作已由用户中止")
            return False, 0, 0, 0
        
        # 5. 开始批量处理
        print(f"\n步骤 5: 开始批量处理")
        print("=" * 60)
        
        processed_files_count = 0
        error_files_count = 0
        total_bytes_added = 0
        failed_files = []
        md5_changes = []  # 存储MD5变化记录
        
        for i, file_path in enumerate(image_files, 1):
            print(f"\n[{i}/{len(image_files)}] 处理文件: {file_path.name}")
            
            try:
                success, original_md5, new_md5 = modify_image_md5(file_path, random_bytes_count)
                
                if success:
                    processed_files_count += 1
                    total_bytes_added += random_bytes_count
                    md5_changes.append({
                        'filename': file_path.name,
                        'original_md5': original_md5,
                        'new_md5': new_md5
                    })
                    print(f"✅ 成功处理 - MD5已变更")
                else:
                    error_files_count += 1
                    failed_files.append(file_path.name)
                    print(f"❌ 处理失败")
                    
            except KeyboardInterrupt:
                print("\n\n操作被用户中断")
                break
            except Exception as e:
                error_files_count += 1
                failed_files.append(file_path.name)
                print(f"❌ 处理文件时发生未预期的错误: {e}")
        
        # 6. 生成处理报告
        execution_time = time.time() - start_time
        
        print("\n" + "=" * 60)
        print("📊 处理完成 - 统计报告")
        print("=" * 60)
        print(f"📁 处理文件夹: {folder_path}")
        print(f"🖼️  扫描到的图片文件: {len(image_files)} 个")
        print(f"✅ 成功处理: {processed_files_count} 个文件")
        print(f"❌ 处理失败: {error_files_count} 个文件")
        print(f"📈 总计增加字节数: {total_bytes_added:,} 字节")
        print(f"🔧 每文件增加字节数: {random_bytes_count} 字节")
        print(f"⏱️  总执行时间: {execution_time:.2f} 秒")
        
        if processed_files_count > 0:
            print(f"📈 平均处理速度: {processed_files_count/execution_time:.2f} 文件/秒" if execution_time > 0 else "📈 平均处理速度: N/A")
        
        if failed_files:
            print(f"\n⚠️  处理失败的文件:")
            for failed_file in failed_files:
                print(f"   - {failed_file}")
        
        # 显示MD5变化详情（最多显示前10个）
        if md5_changes:
            print(f"\n🔐 MD5值变化详情 (显示前{min(10, len(md5_changes))}个):")
            for i, change in enumerate(md5_changes[:10], 1):
                print(f"   {i}. {change['filename']}")
                print(f"      原始: {change['original_md5']}")
                print(f"      新值: {change['new_md5']}")
            
            if len(md5_changes) > 10:
                print(f"   ... 还有 {len(md5_changes) - 10} 个文件的MD5值已变更")
        
        print("=" * 60)
        
        return error_files_count == 0, processed_files_count, error_files_count, total_bytes_added
        
    except KeyboardInterrupt:
        print("\n\n操作被用户中断")
        return False, 0, 0, 0
    except Exception as e:
        print(f"\n批量处理过程中发生错误: {e}")
        return False, 0, 0, 0


def main():
    """
    主函数：协调整个图片MD5修改流程。
    """
    try:
        print("🚀 启动图片MD5值修改工具...")
        
        success, processed_count, error_count, total_bytes = process_images_batch()
        
        if success and processed_count > 0:
            print("\n🎉 所有文件处理成功！")
        elif processed_count > 0:
            print(f"\n⚠️  部分文件处理完成，{error_count} 个文件处理失败")
        else:
            print("\n❌ 没有文件被成功处理")
            
    except KeyboardInterrupt:
        print("\n\n👋 程序被用户中断，感谢使用！")
    except Exception as e:
        print(f"\n💥 程序运行时发生未预期的错误: {e}")
        print("请检查环境配置或联系技术支持")
    finally:
        print("\n程序结束")


if __name__ == "__main__":
    main()