import pathlib
import zipfile
from typing import List, Iterable

from graia.ariadne.message.element import ForwardNode, Forward, Image

from modules.shared import download_file, rename_image_with_hash


async def extract_images_from_forward(forward: Forward) -> List[Image]:
    ret_images: List[Image] = []
    search_stack: List[ForwardNode] = []
    search_stack.extend(forward.node_list)
    while search_stack:
        node = search_stack.pop(0)
        if node.message_chain.has(Forward):
            for sub_forward in node.message_chain.get(Forward):
                search_stack.extend(sub_forward.node_list)
        if node.message_chain.has(Image):
            ret_images.extend(node.message_chain.get(Image))

    return ret_images


def make_zip(source_files: Iterable[str], output_filename: str):
    pathlib.Path(output_filename).parent.mkdir(parents=True, exist_ok=True)
    # 创建一个zip文件
    with zipfile.ZipFile(output_filename, "w") as zipf:
        # 遍历源文件列表

        for file in source_files:
            path_obj = pathlib.Path(file)
            # 将每个文件添加到zip文件中
            zipf.write(file, path_obj.name)


async def make_image_zipper(images: List[Image], save_dir) -> str:
    image_files: List[str] = await download_file([image.url for image in images], save_dir)

    print(f"Downloaded images: {image_files}")
    temp_file_path = f"{save_dir}/temp.zip"
    # make zipfile

    make_zip(image_files, temp_file_path)
    pathlib.Path(temp_file_path).unlink()
    # rename zipfile with hash
    save_path = rename_image_with_hash(temp_file_path)

    return save_path
