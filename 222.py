import os
import shutil

folder_path = r"D:\Downloads\live\小红书发布图\万达店"

# 检查目录是否存在
if os.path.exists(folder_path) and os.path.isdir(folder_path):
    # 遍历删除文件夹中的所有内容
    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        if os.path.isfile(item_path):
            os.remove(item_path)
        elif os.path.isdir(item_path):
            shutil.rmtree(item_path)
    print(f"已删除'{folder_path}'目录下的所有子文件夹及文件")
else:
    print(f"目录'{folder_path}'不存在")
