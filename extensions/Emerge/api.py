import json
import pathlib
from typing import Dict, List

import requests

from modules.file_manager import explore_folder
from .fetch import fetch_src


class EmojiMerge:
    """
    EmojiMerge
    """

    SRC_URL = "https://backend.emojikitchen.dev"

    def __init__(self, cache_dir: str, data_path_file: str):
        pathlib.Path(cache_dir).mkdir(parents=True, exist_ok=True)
        self._db_file = data_path_file
        self._data_base: Dict[str, str] = {}
        self._cache_dir = cache_dir

    async def init_data_base(self):
        if pathlib.Path(self._db_file).exists():
            self.load_data_base(self._db_file)
        self._data_base.update(await self.download_src(self._db_file))
        print(f"Data base init finished.")

    def load_data_base(self, data_file: str):
        self._data_base.update(json.load(open(data_file, "r", encoding="utf-8")))

    async def download_src(self, save_path: str) -> Dict[str, str]:
        """
        Downloads the source data from the specified URL and saves it to the given file path.

        Args:
            save_path (str): The path to the file where the downloaded data will be saved.

        Returns:
            Dict[str, str]: A dictionary containing the downloaded data, where the keys are the emoji names and the values are the URLs of the corresponding emoji images.
        """
        content: str = await fetch_src(self.SRC_URL)
        content_obj = json.loads(content)
        data_seq: List[Dict] = raw_getter(content_obj)
        index: Dict[str, str] = make_index(data_seq)
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
        return index

    def seach_cache(self, emoji_1: str, emoji_2: str) -> str | None:
        cached_file = explore_folder(self._cache_dir, max_depth=1)
        matched = [file for file in cached_file if f"{emoji_1}{emoji_2}" in file and f"{emoji_2}{emoji_1}" in file]

        if matched:
            return matched[0]

    def seach_db(self, emoji_1: str, emoji_2: str) -> str | None:
        key1, key2 = (emoji_1 + emoji_2), (emoji_2 + emoji_1)
        src_url = self._data_base.get(key1) or self._data_base.get(key2)
        if src_url is None:
            return None
        ret = requests.get(src_url)
        save_path = pathlib.Path(self._cache_dir).joinpath(f"{emoji_1}{emoji_2}.png")
        save_path.write_bytes(ret.content)
        return save_path.as_posix()

    def merge(self, emoji_1: str, emoji_2: str) -> str | None:
        """
        Merge two emojis into a single image file and return the file path.

        Args:
            emoji_1 (str): The first emoji to merge.
            emoji_2 (str): The second emoji to merge.

        Returns:
            str: The file path of the merged emoji image.

        Raises:
            None.
        """
        if cached := self.seach_cache(emoji_1, emoji_2):
            return cached
        return self.seach_db(emoji_1, emoji_2)


def raw_getter(data_file: Dict) -> List[Dict]:
    all_data: Dict[str, Dict] = data_file["data"]
    asm = []
    for data_pack in all_data.values():
        asm.extend(data_pack["combinations"])
    return asm


def make_index(emojis_dict: List[Dict]) -> Dict[str, str]:
    return {(item["leftEmoji"] + item["rightEmoji"]): item["gStaticUrl"] for item in emojis_dict}
