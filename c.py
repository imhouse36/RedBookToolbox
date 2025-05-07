import os
import random
import shutil

source_folder = r"D:\Downloads\live\小红书发布图\万达店"
all_images = []

# Get all image files from the source folder
for file in os.listdir(source_folder):
    if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
        all_images.append(file)

# Get all subdirectories
subdirectories = [d for d in os.listdir(source_folder) if os.path.isdir(os.path.join(source_folder, d))]

if not subdirectories:
    print("No subdirectories found.")
else:
    for subdir in subdirectories:
        subdir_path = os.path.join(source_folder, subdir)

        # Randomly select 4 images
        if len(all_images) >= 4:
            selected_images = random.sample(all_images, 4)
        else:
            selected_images = all_images[:]
            print(f"Warning: Only {len(all_images)} images available.")

        # Copy selected images to subdirectory
        for img in selected_images:
            source_file = os.path.join(source_folder, img)
            destination_file = os.path.join(subdir_path, img)
            shutil.copy2(source_file, destination_file)

        print(f"Copied 4 random images to {subdir}")
