import unittest


class MyTestCase(unittest.TestCase):
    def test_something(self):
        from enum import Enum

        class AbstractEnum(Enum):
            def __str__(self):
                return self.name

            def __repr__(self):
                return f"{self.__class__.__name__}.{self.name}"

            def export(self):
                return self.name

        class Color(AbstractEnum):
            RED = 1
            GREEN = 2
            BLUE = 3

        print(Color.RED)  # 输出：Color.RED
        print(Color.GREEN)  # 输出：Color.GREEN
        print(Color.BLUE)  # 输出：Color.BLUE
        print(Color.RED.export())  # 输出：RED


if __name__ == "__main__":
    unittest.main()
