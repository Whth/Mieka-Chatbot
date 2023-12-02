import pathlib
import unittest
from io import StringIO

from bokeh.models import ColumnDataSource, TableColumn, DataTable
from bokeh.plotting import figure, show, output_file

temp_dir = "temp"
pathlib.Path(temp_dir).mkdir(parents=True, exist_ok=True)


class TestBokeh(unittest.TestCase):
    def test_lineplot(self):
        data = {"x": [1, 2, 3, 4, 5], "y": [6, 7, 2, 4, 5]}
        source = ColumnDataSource(data=data)
        p = figure(title="Line plot example", x_axis_label="x", y_axis_label="y")
        p.line("x", "y", source=source, line_width=2)
        output_file(f"{temp_dir}/lineplot.html")
        show(p)

    def test_barplot(self):
        data = {"fruits": ["apples", "oranges", "bananas"], "counts": [5, 3, 4]}
        source = ColumnDataSource(data=data)
        p = figure(x_range=data["fruits"], height=250, title="Bar plot example", toolbar_location=None, tools="")
        p.vbar(x="fruits", top="counts", width=0.9, source=source)
        output_file(f"{temp_dir}/barplot.html")
        show(p)

    def test_table(self):
        data = {"A": [1, 2, 3], "B": [4, 5, 6], "C": [7, 8, 9]}
        source = ColumnDataSource(data=data)

        p = DataTable(
            source=source,
            columns=[
                TableColumn(field="A", title="A"),
                TableColumn(field="B", title="B"),
                TableColumn(field="C", title="C"),
            ],
            width=400,
            height=280,
        )

        show(p)

    def test_complexplot(self):
        data = {"x": [1, 2, 3, 4, 5], "y": [6, 7, 2, 4, 5], "colors": ["red", "green", "blue", "orange", "purple"]}
        source = ColumnDataSource(data=data)
        p = figure(title="Complex plot example", x_axis_label="x", y_axis_label="y")
        p.circle("x", "y", color="colors", size=20, source=source)
        output_file(f"{temp_dir}/complexplot.html")
        show(p)

    def test_specialplot(self):
        data = {
            "x": [1, 2, 3, 4, 5],
            "y": [6, 7, 2, 4, 5],
            "sizes": [10, 15, 5, 20, 25],
            "angles": [0, 45, 90, 135, 180],
        }
        source = ColumnDataSource(data=data)
        p = figure(title="Special plot example", x_axis_label="x", y_axis_label="y")
        p.wedge(
            x=0,
            y=0,
            radius=0.4,
            start_angle="angles",
            end_angle="angles",
            fill_color="colors",
            legend_field="colors",
            source=source,
        )
        output_file(f"{temp_dir}/specialplot.html")
        show(p)


if __name__ == "__main__":
    test_cases = [
        TestBokeh("test_lineplot"),
        TestBokeh("test_barplot"),
        TestBokeh("test_table"),
        TestBokeh("test_complexplot"),
        TestBokeh("test_specialplot"),
    ]
    results = []
    for case in test_cases:
        result = unittest.TextTestRunner(stream=StringIO()).run(case)
        results.append((case._testMethodName, "Pass" if result.wasSuccessful() else "Fail"))
    print(results)
