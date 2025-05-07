import os
import errno

base_dir = r"D:\Downloads\live\小红书发布图\万达店"

try:
    # 确保基础目录存在
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)

    # 创建10个文件夹，命名从1到10
    for i in range(1, 11):
        folder_path = os.path.join(base_dir, str(i))
        if not os.path.exists(folder_path):
            os.mkdir(folder_path)
            print(f"创建文件夹: {folder_path}")
        else:
            print(f"文件夹已存在: {folder_path}")

    print("所有文件夹创建完成")

except OSError as e:
    if e.errno != errno.EEXIST:
        print(f"创建文件夹时出错: {e}")
        raise

