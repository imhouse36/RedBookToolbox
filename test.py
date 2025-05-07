import os
import hashlib
import random
from PIL import Image

def modify_image_md5(image_path):
    """修改图片的MD5值，通过修改一个像素点实现"""
    try:
        # 计算原始MD5值
        with open(image_path, 'rb') as f:
            original_data = f.read()
            original_md5 = hashlib.md5(original_data).hexdigest()

        # 打开图片并修改一个像素点
        img = Image.open(image_path)
        width, height = img.size
        # 选择一个随机位置的像素
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)

        # 获取当前像素值
        pixel = list(img.getpixel((x, y)))

        # 修改像素值（RGB或RGBA中的一个通道）
        channel = random.randint(0, len(pixel) - 1)
        pixel[channel] = (pixel[channel] + 1) % 256

        # 设置修改后的像素
        img.putpixel((x, y), tuple(pixel))

        # 保存修改后的图片
        img.save(image_path)
        # 计算并返回新的MD5值
        with open(image_path, 'rb') as f:
            new_md5 = hashlib.md5(f.read()).hexdigest()
        return original_md5, new_md5
    except Exception as e:
        return f"处理图片出错: {str(e)}"

def process_directory(directory):
    """处理指定目录及其子目录下的所有图片文件"""
    # 支持的图片格式
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']

    # 处理结果统计
    total_images = 0
    modified_images = 0
    failed_images = 0

    # 遍历目录及子目录
    for root, dirs, files in os.walk(directory):
        for file in files:
            # 检查文件是否为图片
            if any(file.lower().endswith(ext) for ext in image_extensions):
                total_images += 1
                image_path = os.path.join(root, file)
                print(f"正在处理: {image_path}")

                # 修改图片MD5
                result = modify_image_md5(image_path)
                if isinstance(result, str) and result.startswith("处理图片出错"):
                    print(f"  失败: {result}")
                    failed_images += 1
                else:
                    original_md5, new_md5 = result
                    print(f"  成功: 原MD5值 = {original_md5}")
                    print(f"        新MD5值 = {new_md5}")
                    modified_images += 1

    # 打印处理结果统计
    print("\n处理完成！")
    print(f"总共图片数: {total_images}")
    print(f"成功修改的图片数: {modified_images}")
    print(f"失败的图片数: {failed_images}")

if __name__ == "__main__":
    # 设置要处理的目录
    target_directory = r"D:\Downloads\live\小红书发布图\万达店"

    if os.path.exists(target_directory):
        print(f"开始处理目录: {target_directory}")
        process_directory(target_directory)
    else:
        print(f"错误: 目录 {target_directory} 不存在!")