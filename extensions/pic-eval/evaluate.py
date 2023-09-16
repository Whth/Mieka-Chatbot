import os
import shutil
from typing import List, Tuple

from modules.file_manager import explore_folder


class Evaluate(object):
    LEVEL_PREFIX = "level"
    LEVEL_SUFFIX = ""

    def __init__(self, store_dir_path: str, level_resolution: int):
        files: List[str] = explore_folder(store_dir_path)
        if files:
            raise FileExistsError("store dir must be empty")
        if level_resolution < 1 or level_resolution > 100:
            raise ValueError("the level resolution is too big")
        self._store_dir_path: str = store_dir_path
        self._level_dirs: List[str] = [
            f"{self.LEVEL_PREFIX}{level}{self.LEVEL_SUFFIX}" for level in list(range(1, level_resolution + 1))
        ]
        self._score_bound: Tuple[int, int] = (1, level_resolution)

    def mark(self, file_path: str, score: int):
        """
        Moves a file to a target directory based on its score.

        Parameters:
            file_path (str): The path of the file to be moved.
            score (int): The score of the file.

        Returns:
            None

        Raises:
            ValueError: If the score is not within the specified bounds.
        """
        if self._score_bound[0] <= score <= self._score_bound[1]:
            target_dir = f"{self._store_dir_path}/{self._level_dirs[score - 1]}"
            os.makedirs(target_dir, exist_ok=True)
            shutil.move(file_path, target_dir)
            return
        raise ValueError("bad score")
