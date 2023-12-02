import pathlib
import unittest
from io import StringIO

import matplotlib.pyplot as plt
import seaborn as sns

temp_dir = "temp"
pathlib.Path(temp_dir).mkdir(parents=True, exist_ok=True)


class TestSeaborn(unittest.TestCase):
    def test_lineplot(self):
        data = sns.load_dataset("flights")
        plt.figure()
        sns.lineplot(x="year", y="passengers", data=data)
        plt.savefig(f"{temp_dir}/lineplot.png")

    def test_barplot(self):
        data = sns.load_dataset("titanic")
        plt.figure()
        sns.barplot(x="class", y="fare", data=data)
        plt.savefig(f"{temp_dir}/barplot.png")

    def test_table(self):
        data = sns.load_dataset("tips")
        print(data.head())

    def test_complexplot(self):
        data = sns.load_dataset("iris")
        plt.figure()
        sns.pairplot(data, hue="species")
        plt.savefig(f"{temp_dir}/complexplot.png")

    def test_specialplot(self):
        data = sns.load_dataset("diamonds")
        plt.figure()
        sns.scatterplot(x="carat", y="price", size="depth", hue="cut", data=data)
        plt.savefig(f"{temp_dir}/specialplot.png")


if __name__ == "__main__":
    test_cases = [
        TestSeaborn("test_lineplot"),
        TestSeaborn("test_barplot"),
        TestSeaborn("test_table"),
        TestSeaborn("test_complexplot"),
        TestSeaborn("test_specialplot"),
    ]
    results = []
    for case in test_cases:
        result = unittest.TextTestRunner(stream=StringIO()).run(case)
        results.append((case._testMethodName, "Pass" if result.wasSuccessful() else "Fail"))
    print(results)
