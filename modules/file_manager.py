import asyncio
import base64
import hashlib
import inspect
import json
import os
import pathlib
import random
import string
import time
from functools import singledispatch
from json import JSONDecodeError
from pathlib import Path
from typing import List, Sequence, Any, Dict, TypeVar
from typing import Tuple

import aiohttp
from PIL import Image
from aiohttp import ClientResponse
from pydantic import BaseModel, Field


class PersistentDict(BaseModel):
    class Config:
        validate_assignment = True
        allow_mutation = False

    container: Dict[Any, Any] = Field(default_factory=dict, const=True)

    def load(self, path: str | Path) -> bool:
        with open(path, "r", encoding="utf-8") as f:
            try:
                self.container.update(json.load(f))
                return True
            except JSONDecodeError:
                return False

    def save(self, path: str | Path) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.container, f, indent=2, ensure_ascii=False)


def get_current_file_path() -> str:
    """
    get current file path
    Returns:

    """
    import inspect

    return inspect.getabsfile(inspect.currentframe())


def explore_folder(root_path: str, ignore_list: Sequence[str] = tuple(), max_depth: int = -1) -> List[str]:
    """
    Recursively explores a folder and returns a list of all file paths up to the specified depth.

    Args:
        root_path (str): The root path of the folder to explore.
        ignore_list (Sequence[str]): A list of folder names to ignore.
        max_depth (int): The maximum depth to explore. If -1, explore all levels.

    Returns:
        List[str]: A list of all file paths found in the folder up to the specified depth.
    """
    # Store all file paths
    file_paths = []

    # Traverse all files and subdirectories in the directory
    for path in Path(root_path).rglob("*"):
        if path.is_file():
            # Process each file
            file_paths.append(str(path))

    # Exclude folders in the ignored list
    ignored_paths = [Path(root_path) / ignore_folder for ignore_folder in ignore_list]
    file_paths = [
        file_path
        for file_path in file_paths
        if not any(str(ignored_path) in file_path for ignored_path in ignored_paths)
    ]

    # Return the list of all file paths up to the specified depth
    if max_depth == -1:
        return file_paths
    else:
        current_depth = len(Path(root_path).relative_to(Path(root_path)).parts)
        return [file_path for file_path in file_paths if current_depth <= max_depth]


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

    folder_path = Path(folder_path)
    current_time = time.time()

    for file_path in folder_path.iterdir():
        if file_path.is_file():
            modify_time = file_path.stat().st_mtime
            file_time = current_time - modify_time

            if file_time > time_limit:
                file_size = file_path.stat().st_size
                file_path.unlink()
                clean_file_num += 1
                clean_file_size += file_size
                print(f"清理文件：{file_path}，大小：{file_size/1024/1024} MB")

    print(f"清理文件个数：{clean_file_num}，清理文件大小：{clean_file_size/1024/1024} MB")


def is_image(file_path) -> bool:
    """
    Check if a file is an image.

    Parameters:
        file_path (str): The path to the file.

    Returns:
        bool: True if the file is an image, False otherwise.
    """
    try:
        img = Image.open(file_path)
        img.close()
        return True
    except IOError:
        return False


T_Generic = TypeVar("T_Generic")


@singledispatch
async def download_file(url: T_Generic, save_dir: str, force_download: bool = False) -> T_Generic:
    """
    Downloads a file from the given URL and saves it to the specified directory.

    Args:
        url (str): The URL of the file to download.
        save_dir (str): The directory to save the downloaded file.
        force_download (bool, optional): Whether to force re-download it even it already exists.Defaults to False.


    Returns:
        str: The path to the downloaded file.
    """


@download_file.register(str)
async def download_sigle_file(url: str, save_dir: str, force_download: bool = False) -> str:
    # Generate the file name using the MD5 hash of the URL
    url_hash = sha256_string(url)

    path = pathlib.Path(f"{save_dir}/{url_hash}.png")
    path.parent.mkdir(parents=True, exist_ok=True)
    # Check if the file already exists and force_download is False
    if not force_download and path.exists():
        return str(path)

    # Download the file using aiohttp
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                raise aiohttp.ClientResponseError(response.request_info, history=response.history)
            with open(path, "wb") as f:
                f.write(await response.read())
    return str(path)


@download_file.register(list)
async def download_list(url: List[str], save_dir: str, force_download: bool = False) -> List[str]:
    """
    该函数用于下载列表中所有URL对应的文件并保存到指定目录。

    参数：
    - url: 待下载文件的URL列表。
    - save_dir: 下载后保存文件的目录。
    - force_download: 是否强制下载文件，默认为False。

    返回值：
    - 下载完成后对应的文件路径列表。
    """
    save_dir = pathlib.Path(save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)

    file_list = [f"{save_dir}/{sha256_string(url_string)}.png" for url_string in url]
    original_file_list = file_list

    if not force_download:
        pack = [(url[i], file_list[i]) for i in range(len(url)) if not pathlib.Path(file_list[i]).exists()]
        url, file_list = zip(*pack)
    async with aiohttp.ClientSession() as session:
        responses: Tuple[ClientResponse] = await asyncio.gather(*[session.get(url_string) for url_string in url])
        for response, save_path in zip(responses, file_list):
            response: ClientResponse
            save_path: str
            if response.status != 200:
                raise aiohttp.ClientResponseError(response.request_info, history=response.history)
            with open(save_path, "wb") as f:
                f.write(await response.content.read())
    return original_file_list


def compress_image_max_res(input_image_path: str, output_image_path: str, size: Tuple[int, int]) -> None:
    """
    Compresses an image to a specified size.

    Args:
        input_image_path (str): The path to the input image file.
        size (Tuple[int, int]): The desired width and height of the output image.
        output_image_path (str): The path to save the compressed image.

    Returns:
        str: The path to the compressed image file.
    """

    # 打开图像
    image = Image.open(input_image_path)

    # 获取原始图像的宽度和高度
    width, height = image.size
    max_width, max_height = size
    if max_height > height and max_width > width:
        image.save(output_image_path, format="png")
        return None
    # 计算压缩比例
    ratio = min(max_width / width, max_height / height)

    # 计算压缩后的新宽度和高度
    new_width = int(width * ratio)
    new_height = int(height * ratio)

    # 压缩图像
    resized_image = image.resize((new_width, new_height), reducing_gap=2.0)

    # 保存压缩后的图像
    resized_image.save(output_image_path, format="png")


def compress_image_max_vol(
    input_image_path: str,
    output_image_path: str,
    max_file_size: int,
    search_best: bool = True,
    min_quality: int = 85,
) -> int:
    """
    Compresses an image to a maximum file size.

    Args:
        input_image_path (str): The path to the input image file.
        output_image_path (str): The path to save the compressed image file.
        max_file_size (int): The maximum file size in bytes.
        search_best (bool, optional): Whether to search for the best quality that meets the maximum
            file size requirement. Defaults to True.
        min_quality (int, optional): The minimum quality of the compressed image. Must be a multiple of 5.
            Defaults to 85.

    Returns:
        int: The quality of the compressed image that meets the maximum file size requirement.
    """
    step = 5
    if min_quality % step != 0:
        raise ValueError(f"min_quality must be a multiple of {step}")
    img = Image.open(input_image_path)
    compressed_img_vol = 0
    current_quality = min_quality
    while compressed_img_vol < max_file_size:
        img.save(output_image_path, quality=current_quality, bitmap_format="png")
        compressed_img_vol = os.path.getsize(output_image_path)
        if search_best:
            current_quality += step
        else:
            break

    return current_quality


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


def sha256_string(s: str) -> str:
    """
    Generates the SHA-256 hash of a given string.

    Args:
        s (str): The string to be hashed.

    Returns:
        str: The SHA-256 hash of the input string.
    """
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def rename_image_with_hash(image_path: str) -> str:
    """
    Renames the image file at the specified path by appending a 6-character hash value
    derived from the image content.
    Returns the renamed image path.
    """
    # Check if the image file exists
    image_path = Path(image_path)
    if not image_path.exists():
        raise FileNotFoundError(f"{image_path} does not exist")

    # Get the image file name prefix and suffix
    image_name_stem, image_name_suffix = image_path.stem, image_path.suffix

    # Read the image file
    with open(image_path, "rb") as f:
        # Calculate the hash value of the image file content
        image_hash = hashlib.md5(f.read()).hexdigest()[:6]

    # Rename the image file
    new_image_name = f"{image_name_stem}_{image_hash}.{image_name_suffix}"
    new_image_path = image_path.parent / new_image_name
    if not new_image_path.exists():
        image_path.rename(new_image_path)

    # Return the renamed image path
    return str(new_image_path)


def generate_random_string(length: int) -> str:
    """
    Generate a random string of a specified length.

    Parameters:
        length (int): The desired length of the random string.

    Returns:
        str: A random string consisting of letters from the ASCII alphabet.
    """
    letters = string.ascii_letters
    return "".join(random.choice(letters) for _ in range(length))


def get_pwd() -> str:
    current_frame = inspect.currentframe()
    caller_frame = inspect.getouterframes(current_frame, 2)
    caller_file = caller_frame[1][1]
    return str(pathlib.Path(caller_file).parent)
