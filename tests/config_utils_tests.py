import unittest

from modules.config_utils import get_all_config_chains


class TestGetAllConfigChains(unittest.TestCase):
    def test_flatten_dictionary(self):
        body = {"foo": 1, "bar": {"baz": 2, "qux": {"quux": 3}}, "hello": "world"}
        expected_output = [["foo"], ["bar", "baz"], ["bar", "qux", "quux"], ["hello"]], [1, 2, 3, "world"]
        self.assertEqual(get_all_config_chains(body), expected_output)

    def test_nested_dictionaries(self):
        body = {"a": {"b": {"c": {"d": {"e": 1}}}}}
        expected_output = ([["a", "b", "c", "d", "e"]], [1])
        self.assertEqual(get_all_config_chains(body), expected_output)

    def test_empty_dictionary(self):
        body = {}
        expected_output = [], []
        self.assertEqual(get_all_config_chains(body), expected_output)


if __name__ == "__main__":
    unittest.main()
