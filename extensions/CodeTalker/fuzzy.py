import json
import pathlib
from difflib import get_close_matches
from typing import Any


class FuzzyDictionary:
    def __init__(self, save_path: str):
        self._save_path = save_path

        self.dictionary = {}
        if pathlib.Path(self._save_path).exists():
            self.load_from_json()

    def register_key_value(self, key: str, value: Any):
        """
        Registers a key-value pair in the dictionary.

        Args:
            key: The key to be registered.
            value: The value to be associated with the key.

        Returns:
            None
        """
        self.dictionary[key] = value

    def search(self, key: str) -> Any:
        matches = get_close_matches(key, self.dictionary.keys())
        if matches:
            return self.dictionary[matches[0]]
        else:
            return None

    def save_to_json(self):
        with open(self._save_path, "w") as file:
            json.dump(self.dictionary, file, ensure_ascii=False, indent=2)

    def load_from_json(self):
        with open(self._save_path, "r") as file:
            self.dictionary = json.load(file)


if __name__ == "__main__":
    # 创建FuzzyDictionary对象
    fuzzy_dict = FuzzyDictionary("dictionary.json")

    # 注册键值对
    fuzzy_dict.register_key_value("apple", "苹果")
    fuzzy_dict.register_key_value("banana", "香蕉")
    fuzzy_dict.register_key_value("orange", "橙子")

    # 模糊搜索键值
    result = fuzzy_dict.search("app")
    if result:
        print(result)  # 输出: "苹果"
    else:
        print("未找到匹配的键值")

    # 持久化保存为json文件
    fuzzy_dict.save_to_json()
