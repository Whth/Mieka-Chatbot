import datetime
import os
import time
from typing import List

import requests


def get_current_file_path() -> str:
    """
    get current file path
    Returns:

    """
    import inspect

    return inspect.getabsfile(inspect.currentframe())


def explore_folder(root_path: str) -> List[str]:
    """

    Args:
        root_path (str):

    Returns:

    """
    # 存储所有文件的路径
    file_paths = []

    # 遍历目录下所有文件和子目录
    for root, dirs, files in os.walk(root_path):
        for file in files:
            # 处理每个文件
            file_path = os.path.join(root, file)
            # 存储文件路径到列表
            file_paths.append(file_path)

        for dir in dirs:
            # 处理每个子目录
            subdir = os.path.join(root, dir)
            # 递归遍历子目录，并将子目录中的文件路径加到列表中
            file_paths.extend(explore_folder(subdir))

    # 返回所有文件的路径列表
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
    # Generate a unique image name based on the current timestamp
    img_name = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

    print(f"Downloading image from: {url}")

    # Send a GET request to download the image
    response = requests.get(url)

    if response.status_code == 200:
        # Create the save directory if it doesn't exist
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        # Construct the path where the image will be saved
        path = os.path.join(save_dir, f"{img_name}.png")

        # Write the image content to a file
        with open(path, "wb") as f:
            f.write(response.content)

        print(f"Downloaded image successfully. Saved at: {path}")
        return path

    return None
