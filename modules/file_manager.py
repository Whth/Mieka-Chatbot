import base64
import datetime
import hashlib
import os
import time
from datetime import datetime
from typing import List, Sequence

import requests


def get_current_file_path() -> str:
    """
    get current file path
    Returns:

    """
    import inspect

    return inspect.getabsfile(inspect.currentframe())


def explore_folder(root_path: str, ignore_list: Sequence[str] = tuple()) -> List[str]:
    """
    Recursively explores a folder and returns a list of all file paths.

    Args:
        root_path (str): The root path of the folder to explore.
        ignore_list (Sequence[str]): A list of folder names to ignore.

    Returns:
        List[str]: A list of all file paths found in the folder.
    """
    # Store all file paths
    file_paths = []

    # Traverse all files and subdirectories in the directory
    for root, dirs, files in os.walk(root_path):
        # Exclude folders in the ignored list
        dirs[:] = [d for d in dirs if d not in ignore_list]

        for file in files:
            # Process each file
            file_path = os.path.join(root, file)
            # Add a file path to the list
            file_paths.append(file_path)

        for directory in dirs:
            # Process each subdirectory
            subdir = os.path.join(root, directory)
            # Recursively explore the subdirectory and add file paths to the list
            file_paths.extend(explore_folder(subdir, ignore_list))

    # Return the list of all file paths
    return file_paths


def get_all_sub_dirs(directory: str) -> List[str]:
    """

    Args:
        directory (str):

    Returns:

    """
    subdirectories = [name for name in os.listdir(directory) if os.path.isdir(os.path.join(directory, name))]
    return subdirectories


def clean_files(folder_path, time_limit):
    """
    清理文件夹中超过指定时长的文件
    :param folder_path: 文件夹路径
    :param time_limit: 时长限制，单位为秒
    :return: 清理文件个数与清理掉的文件所占的储存空间大小
    """
    clean_file_num = 0
    clean_file_size = 0

    files = os.listdir(folder_path)

    for file in files:
        file_path = os.path.join(folder_path, file)
        modify_time = os.path.getmtime(file_path)
        current_time = time.time()
        file_time = current_time - modify_time

        if file_time > time_limit:
            file_size = os.path.getsize(file_path)
            os.remove(file_path)
            clean_file_num += 1
            clean_file_size += file_size
            print(f"清理文件：{file_path}，大小：{file_size/1024/1024} MB")

    print(f"清理文件个数：{clean_file_num}，清理文件大小：{clean_file_size/1024/1024} MB")


def download_image(url: str, save_dir: str) -> str:
    """
    Downloads an image from the given URL and saves it to the specified directory.

    Args:
        url (str): The URL of the image.
        save_dir (str): The directory where the image should be saved.

    Returns:
        str: The path where the image is saved, or None if the download fails.
    """
    img_name = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    response = requests.get(url)
    if response.status_code == 200:
        os.makedirs(save_dir, exist_ok=True)
        path = os.path.join(save_dir, f"{img_name}.png")
        with open(path, "wb") as f:
            f.write(response.content)
        return path
    return ""


def img_to_base64(file_path: str) -> str:
    """
    Convert an image file to base64 encoding.

    :param file_path: The path to the image file.
    :return: The base64 encoded string.
    :raises FileNotFoundError: If the file does not exist.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"{file_path} does not exist")

    with open(file_path, "rb") as f:
        data = f.read()

    return base64.b64encode(data).decode()


def base64_to_img(base64_string: str, output_path: str) -> None:
    """
    Convert a base64 encoded string back to an image file and save it to the specified output path.

    :param base64_string: The base64 encoded string.
    :param output_path: The path to save the image file.
    :raises FileExistsError: If the output path already exists as a file.
    """
    if not os.path.exists(os.path.dirname(output_path)):
        raise FileNotFoundError(f"{os.path.dirname(output_path)} does not exist")

    # Decode the base64 string
    image_data = base64.b64decode(base64_string)

    # Write the image data to the output path
    with open(output_path, "wb") as f:
        f.write(image_data)


def rename_image_with_hash(image_path: str) -> str:
    """
    Renames the image file at the specified path by appending a 6-character hash value
    derived from the image content.
    Returns the renamed image path.
    """
    # Check if the image file exists
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"{image_path} does not exist")

    # Get the image file name
    image_name = os.path.basename(image_path)

    # Get the image file name prefix and suffix
    image_name_prefix, image_name_suffix = os.path.splitext(image_name)

    # Read the image file
    with open(image_path, "rb") as f:
        image_content = f.read()

    # Calculate the hash value of the image file content
    image_hash = hashlib.md5(image_content).hexdigest()[:6]

    # Rename the image file
    new_image_name = f"{image_name_prefix}_{image_hash}{image_name_suffix}"
    image_dir = os.path.dirname(image_path)
    new_image_path = os.path.join(image_dir, new_image_name)
    os.rename(image_path, new_image_path)

    # Return the renamed image path
    return new_image_path
