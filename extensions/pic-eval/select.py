import hashlib
import hmac
import os
import pickle
import warnings
from random import choice
from typing import List, Any, Sequence

from modules.file_manager import explore_folder


def sign_and_pickle(data: Any, key: bytes, file_path: str):
    """
    Sign and pickle the given data using the provided key, and save it to the specified file path.

    Parameters:
        data (Any): The data to be pickled.
        key (bytes): The key to be used for signing.
        file_path (str): The path of the file to save the pickled data and signature.

    Returns:
        None
    """
    pickled_data = pickle.dumps(data)
    signature = hmac.new(key, pickled_data, hashlib.sha256).digest()
    with open(file_path, "wb") as f:
        f.write(pickled_data + signature)


def unpickle_and_verify(file_path: str, key: bytes) -> Any:
    """
    Unpickle and verify a pickled object from a file.

    This function takes a file path and a key as input. It reads the file using
    the given file path and unpickles the data. The function then verifies the
    integrity of the data using a signature calculated with the given key. If
    the signature is valid, the function returns the unpickled object. Otherwise,
    it raises a ValueError with the message "Invalid signature".

    Parameters:
        file_path (str): The path of the file to read the pickled data and signature.
        key (bytes): The key used for signing the data.

    Returns:
        Any: The unpickled object.

    """
    with open(file_path, "rb") as file:
        pickled_data = file.read()
        data = pickled_data[:-32]
        signature = pickled_data[-32:]
        calculated_signature = hmac.new(key, data, hashlib.sha256).digest()
        if not hmac.compare_digest(signature, calculated_signature):
            warnings.warn(f"Invalid signature of pickle at {file_path}")
            return None

        return pickle.loads(data)


class Selector(object):
    __cache_file = "file_index_cache.pkl"
    __PICKLE_KEY = b"asdjnbskjdvlbkjb"

    def __init__(self, asset_dir: str, cache_dir: str, ignore_dirs: Sequence[str] = tuple()):
        """
        Initializes the Selector object.

        Args:
            asset_dir (str): The directory path containing the assets.
            cache_dir (str): The directory path to store the cache.
            ignore_dirs (Sequence[str], optional): A sequence of directory names to ignore. Defaults to an empty tuple.

        Raises:
            FileNotFoundError: If the asset_dir does not exist.
            FileNotFoundError: If the file_index is empty after updating.
        """
        if not os.path.exists(asset_dir):
            raise FileNotFoundError("asset_dir not exists")
        self._asset_dir: str = asset_dir
        self._cache_dir: str = cache_dir
        os.makedirs(self._cache_dir, exist_ok=True)
        self._ignore_dirs: Sequence[str] = ignore_dirs
        self._file_index: List[str] = []
        if os.path.exists(f"{self._cache_dir}/{self.__cache_file}"):
            self._file_index: List[str] = unpickle_and_verify(
                file_path=f"{self._cache_dir}/{self.__cache_file}", key=self.__PICKLE_KEY
            )

        if self._file_index:
            temp = self._file_index[0]
            if asset_dir not in temp:
                self._update_index()
        else:
            self._update_index()

        if len(self._file_index) == 0:
            raise FileNotFoundError("file_index is empty")

    def _update_index(self):
        self._file_index: List[str] = explore_folder(self._asset_dir, ignore_list=self._ignore_dirs)
        sign_and_pickle(
            data=self._file_index, key=self.__PICKLE_KEY, file_path=f"{self._cache_dir}/{self.__cache_file}"
        )

    def random_select(self) -> str:
        while True:
            selected = choice(self._file_index)
            if os.path.exists(selected):
                return selected
            else:
                self._update_index()

    # TODO imp more other selector
