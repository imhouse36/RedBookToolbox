import os
import hashlib
import random
import time
import pathlib
from typing import Optional, Tuple  # 导入 Optional 和 Tuple

# ==============================================================================
# 脚本功能核心备注 (Script Core Functionality Notes)
# ==============================================================================
#
# 脚本名称 (Script Name):
#   renew_md5.py
#
# 主要目的 (Main Purpose):
#   本脚本用于修改指定根目录及其所有子目录下特定类型图片文件的MD5哈希值。
#   修改MD5值是通过在每个图片文件的末尾附加少量随机字节来实现的。
#
# 工作流程 (Workflow):
#   1. 提示用户输入一个包含图片文件的根目录路径。
#   2. 验证用户输入的路径是否为有效文件夹。
#   3. 显示一个警告信息，告知用户脚本将直接修改文件内容，并建议备份。
#   4. （可选，当前已注释掉）在开始处理前暂停几秒，给用户中止脚本的机会。
#   5. 递归遍历指定根目录及其所有子目录。
#   6. 对于每个目录，查找所有符合 `image_extensions` 定义的图片文件。
#   7. 对每个找到的图片文件：
#      a. 计算原始文件的MD5值。
#      b. 生成1到16个随机字节。
#      c. 以追加模式打开图片文件，并将这些随机字节写入文件末尾。
#      d. 计算修改后文件的新MD5值。
#      e. 打印原始MD5和新MD5，并报告MD5是否已更改。
#   8. 报告处理结果，包括扫描到的文件总数、成功修改MD5的文件数以及处理失败或MD5未改变的文件数。
#
# 配置项 (Key Configurations):
#   - `image_extensions`: 定义了脚本会识别和处理的图片文件扩展名。
#   - 随机附加字节的数量：在1到16字节之间随机选择。
#
# 注意事项 (Important Notes):
#   - 直接修改文件内容：此脚本会**直接修改原始图片文件**。强烈建议在运行前备份您的数据！
#   - MD5变化：附加随机字节通常会导致MD5值改变。如果MD5未改变，脚本会报告警告。
#   - 文件损坏风险：虽然追加少量字节到大多数图片格式末尾通常不会导致文件损坏或无法查看，
#     但对于某些严格格式或特定查看器，仍存在潜在风险。
#   - 权限：脚本需要对目标文件具有写入权限。
#
# ==============================================================================

# --- 配置常量 ---
IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff')
MIN_BYTES_TO_APPEND = 1
MAX_BYTES_TO_APPEND = 16
MD5_CHUNK_SIZE = 4096


# --- /配置常量 ---

def get_file_md5(filepath: pathlib.Path) -> Optional[str]:  # 修改: str | None -> Optional[str]
    """计算文件的MD5值"""
    hash_md5 = hashlib.md5()
    try:
        with filepath.open("rb") as f:
            for chunk in iter(lambda: f.read(MD5_CHUNK_SIZE), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except FileNotFoundError:
        print(f"错误：文件 {filepath} 未找到。")
        return None
    except Exception as e:
        print(f"计算MD5时发生错误 ({filepath}): {e}")
        return None


def modify_image_md5(filepath: pathlib.Path) -> Tuple[
    Optional[str], Optional[str]]:  # 修改: tuple[str | None, str | None] -> Tuple[Optional[str], Optional[str]]
    """
    通过在文件末尾附加随机字节来修改文件的MD5值。
    返回 (旧MD5, 新MD5) 或 (None, None) 如果获取旧MD5失败,
    或 (旧MD5, None) 如果修改步骤失败。
    """
    original_md5 = get_file_md5(filepath)
    if original_md5 is None:
        return None, None  # original_md5已经是Optional[str], new_md5也会是Optional[str]

    try:
        num_bytes_to_append = random.randint(MIN_BYTES_TO_APPEND, MAX_BYTES_TO_APPEND)
        random_bytes = os.urandom(num_bytes_to_append)

        with filepath.open("ab") as f:
            f.write(random_bytes)

        new_md5 = get_file_md5(filepath)
        return original_md5, new_md5
    except PermissionError:
        print(f"权限错误：无法写入文件 {filepath}。请检查文件权限。")
        return original_md5, None
    except Exception as e:
        print(f"修改文件MD5时发生错误 ({filepath}): {e}")
        return original_md5, None


def process_directory_recursively(root_directory_path_str: str):
    """处理指定目录及其所有子目录下的图片文件"""
    root_path = pathlib.Path(root_directory_path_str)

    print(f"\n开始递归处理目录: {root_path}\n")
    modified_count = 0
    failed_count = 0
    processed_files_count = 0

    for dirpath_str, _, filenames in os.walk(root_path):
        dir_path = pathlib.Path(dirpath_str)
        print(f"--- 正在扫描目录: {dir_path} ---")
        for filename in filenames:
            if filename.lower().endswith(IMAGE_EXTENSIONS):
                filepath = dir_path / filename
                if filepath.is_file():
                    processed_files_count += 1
                    print(f"处理文件: {filepath}")

                    original_md5, new_md5 = modify_image_md5(filepath)

                    if original_md5 and new_md5:  # Both are not None
                        if original_md5 != new_md5:
                            print(f"  原MD5: {original_md5}")
                            print(f"  新MD5: {new_md5} (已更改)")
                            modified_count += 1
                        else:
                            print(f"  警告: MD5未改变! 原MD5: {original_md5}, 新MD5: {new_md5}")
                            failed_count += 1
                    elif original_md5 and new_md5 is None:  # Modification failed but original_md5 known
                        print(f"  修改失败或无法获取新MD5。原MD5: {original_md5}")
                        failed_count += 1
                    else:  # original_md5 is None (implies initial get_file_md5 failed)
                        print(f"  无法获取原始MD5。")
                        failed_count += 1
                    print("-" * 20)

    print(f"\n处理完成。")
    print(f"总共扫描到 {processed_files_count} 个符合条件的图片文件。")
    print(f"成功修改 {modified_count} 个文件的MD5。")
    if failed_count > 0:
        print(f"{failed_count} 个文件处理失败或MD5未改变。")


if __name__ == "__main__":
    while True:
        target_directory_input_str = input(
            "请输入要处理的图片根目录路径 (例如: D:\\Downloads\\live\\小红书发布图\\万达店 ): ").strip()

        target_path_obj = pathlib.Path(target_directory_input_str)

        if not target_directory_input_str:
            print("错误：未输入路径，请重新输入。")
        elif not target_path_obj.is_dir():
            print(f"错误：路径 '{target_directory_input_str}' 不是一个有效的目录或目录不存在。请重新输入。")
        else:
            break

    print("\n！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！")
    print("警告：此脚本将直接修改指定目录及其所有子目录下的图片文件内容以更改其MD5值。")
    print("强烈建议在运行此脚本前备份您的原始图片！")
    print(f"您指定的目标根目录是: \"{target_path_obj}\"")
    print("脚本将立即开始处理，没有额外的确认步骤 (除了下面的5秒延迟)。")
    print("如果您不确定，请在5秒内按 Ctrl+C 中止脚本。")
    print("！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！\n")

    print("将在5秒后开始处理...")
    try:
        time.sleep(5)
    except KeyboardInterrupt:
        print("\n操作已由用户中止。")
        exit()

    process_directory_recursively(str(target_path_obj))
    print("\n所有操作已完成。")