import os
import random


def modify_file_md5(file_path):
    """修改单个文件的MD5值"""
    try:
        # 生成1-10个随机字节
        random_bytes = bytes([random.randint(0, 255) for _ in range(random.randint(1, 10))])

        # 以追加模式写入随机字节
        with open(file_path, 'ab') as f:
            f.write(random_bytes)
        return True
    except Exception as e:
        print(f"修改失败: {file_path} - {str(e)}")
        return False


def batch_modify_images(root_dir):
    """递归处理目录及子目录"""
    supported_ext = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')
    modified_count = 0

    for foldername, subfolders, filenames in os.walk(root_dir):
        for filename in filenames:
            # 检查文件扩展名
            if filename.lower().endswith(supported_ext):
                file_path = os.path.join(foldername, filename)
                if modify_file_md5(file_path):
                    print(f"成功修改: {file_path}")
                    modified_count += 1

    print(f"\n完成！共修改 {modified_count} 个文件")


if __name__ == "__main__":
    # 需要修改的目录路径（根据你的需求修改）
    target_dir = r"D:\Downloads\live\小红书发布图\万达店"

    # 开始批量处理
    batch_modify_images(target_dir)