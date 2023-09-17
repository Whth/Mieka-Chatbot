import json
import os
import time
from types import MappingProxyType
from typing import Optional, Dict, List


class ImageRegistry(object):
    def __init__(self, save_path: str, max_size: Optional[int] = None) -> None:
        self._save_path = save_path
        self._max_size = max_size
        self._images_registry: Dict[int, List[str, float]] = {}
        if os.path.exists(self._save_path):
            self.load()
        self._images_registry_proxy: MappingProxyType[str, List[str, float]] = MappingProxyType(self._images_registry)

    def register(self, key: int, image_path: str) -> None:
        self._images_registry[key] = [image_path, time.time()]
        if self._max_size and len(self._images_registry) > self._max_size:
            num_to_remove = len(self._images_registry) - self._max_size
            for _ in range(num_to_remove):
                self._remove_oldest()

    def get(self, key: int) -> str:
        return self._images_registry[key][0]

    def remove(self, key: int) -> None:
        del self._images_registry[key]

    def _remove_oldest(self) -> None:
        oldest_key = min(self._images_registry, key=lambda k: self._images_registry[k][1])
        del self._images_registry[oldest_key]

    def save(self) -> None:
        with open(self._save_path, "w", encoding="utf-8") as f:
            json.dump(self._images_registry, f)

    def load(self) -> None:
        with open(self._save_path, "r", encoding="utf-8") as f:
            temp: Dict[int, List[str, float]] = json.loads(f.read())
        self._images_registry.update(temp)
