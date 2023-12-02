import pathlib
import unittest
from io import StringIO

import plotly.graph_objects as go
from plotly.subplots import make_subplots

temp_dir = "temp"
pathlib.Path(temp_dir).mkdir(parents=True, exist_ok=True)


class TestPlotly(unittest.TestCase):
    def test_lineplot(self):
        data = [1, 2, 3, 4, 5]
        fig = go.Figure(data=go.Scatter(y=data, mode="lines"))
        with open(f"{temp_dir}/lineplot.html", "w", encoding="utf-8") as f:
            f.write(fig.to_html())

    def test_barplot(self):
        data = {"Fruit": ["Apples", "Oranges", "Bananas"], "Count": [5, 3, 4]}
        fig = go.Figure(data=[go.Bar(x=data["Fruit"], y=data["Count"])])
        with open(f"{temp_dir}/barplot.html", "w", encoding="utf-8") as f:
            f.write(fig.to_html())

    def test_table(self):
        data = {"A": [1, 2, 3], "B": [4, 5, 6], "C": [7, 8, 9]}
        fig = go.Figure(
            data=[go.Table(header=dict(values=["A", "B", "C"]), cells=dict(values=[data["A"], data["B"], data["C"]]))]
        )
        with open(f"{temp_dir}/table.html", "w", encoding="utf-8") as f:
            f.write(fig.to_html())

    def test_complexplot(self):
        data = {"x": [1, 2, 3, 4, 5], "y": [6, 7, 2, 4, 5], "colors": ["red", "green", "blue", "orange", "purple"]}
        fig = make_subplots()
        fig.add_trace(go.Scatter(x=data["x"], y=data["y"], mode="markers", marker=dict(color=data["colors"])))
        with open(f"{temp_dir}/complexplot.html", "w", encoding="utf-8") as f:
            f.write(fig.to_html())

    def test_specialplot(self):
        data = {
            "x": [1, 2, 3, 4, 5],
            "y": [6, 7, 2, 4, 5],
            "sizes": [10, 15, 5, 20, 25],
            "angles": [0, 45, 90, 135, 180],
        }
        fig = make_subplots()
        fig.add_trace(
            go.Pie(labels=data["x"], values=data["y"], textinfo="label+percent", insidetextorientation="radial")
        )
        with open(f"{temp_dir}/specialplot.html", "w", encoding="utf-8") as f:
            f.write(fig.to_html())


if __name__ == "__main__":
    test_cases = [
        TestPlotly("test_lineplot"),
        TestPlotly("test_barplot"),
        TestPlotly("test_table"),
        TestPlotly("test_complexplot"),
        TestPlotly("test_specialplot"),
    ]
    results = []
    for case in test_cases:
        result = unittest.TextTestRunner(stream=StringIO()).run(case)
        results.append((case._testMethodName, "Pass" if result.wasSuccessful() else "Fail"))
    print(results)
