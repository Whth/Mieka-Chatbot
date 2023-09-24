import json
import pathlib
from difflib import get_close_matches
from typing import Any, List, Dict


class FuzzyDictionary:
    def __init__(self, save_path: str):
        self._save_path = save_path

        self._dictionary: Dict[str, List[str]] = {}
        if pathlib.Path(self._save_path).exists():
            self.load_from_json()

    @property
    def dictionary(self) -> Dict[str, List[str]]:
        return self._dictionary

    def register_key_value(self, key: str, value: Any):
        """
        Registers a key-value pair in the dictionary.

        Args:
            key: The key to be registered.
            value: The value to be associated with the key.

        Returns:
            None
        """
        if key not in self._dictionary:
            self._dictionary[key] = []
        self._dictionary[key].append(value)

    def search(self, key: str) -> List[str]:
        matches = get_close_matches(key, list(self._dictionary.keys()), n=1)
        if matches:
            return self._dictionary.get(matches[0])
        else:
            return []

    def save_to_json(self) -> None:
        with open(self._save_path, "w", encoding="utf-8") as file:
            json.dump(
                self._dictionary,
                file,
                ensure_ascii=False,
                indent=2,
            )

    def load_from_json(self) -> None:
        with open(self._save_path, "r", encoding="utf-8") as file:
            self._dictionary.update(json.load(file))


if __name__ == "__main__":
    # 创建FuzzyDictionary对象
    fuzzy_dict = FuzzyDictionary("./fuzzy_dictionary.json")

    # 模糊搜索键值
    result = fuzzy_dict.search("我喜欢你！？")
    if result:
        print(result)  # 输出: "苹果"
    else:
        print("未找到匹配的键值")

    # 持久化保存为json文件
    fuzzy_dict.save_to_json()
