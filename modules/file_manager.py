import os
from typing import List


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
