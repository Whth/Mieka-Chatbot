import pathlib
from enum import Enum

import requests

from modules.file_manager import explore_folder


class EmojiMerge:
    """
    EmojiMerge
    """

    class API(Enum):
        HOST = "https://www.gstatic.com/android/keyboard/emojikitchen/20201001"

    def __init__(self, cache_dir: str):
        pathlib.Path(cache_dir).mkdir(parents=True, exist_ok=True)

        self._cache_dir = cache_dir

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
        uni_emoji_1 = f"u{hex(ord(emoji_1))[2:]}"
        uni_emoji_2 = f"u{hex(ord(emoji_2))[2:]}"
        fname = f"{uni_emoji_1}_{uni_emoji_2}.png"
        url = f"{self.API.HOST.value}/{uni_emoji_1}/{fname}"

        cached_file = explore_folder(self._cache_dir, max_depth=1)
        matched = [file for file in cached_file if fname in file]

        if matched:
            return matched[0]

        ret = requests.get(url)
        if ret.ok:
            save_path = f"{self._cache_dir}/{fname}"
            with open(save_path, "wb") as f:
                f.write(ret.content)
            return save_path
        return None
