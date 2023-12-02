import pathlib
import unittest

from pyecharts import options as opts
from pyecharts.charts import Bar, Pie, Line, Scatter, Map, Radar
from pyecharts.faker import Faker

temp_dir = "temp"
pathlib.Path(temp_dir).mkdir(parents=True, exist_ok=True)


class EChartsExample(unittest.TestCase):
    def test_bar(self):
        bar = Bar()
        bar.add_xaxis(Faker.choose())
        bar.add_yaxis("数量", Faker.values())
        bar.set_global_opts(title_opts=opts.TitleOpts(title="Bar示例"))
        bar.render(f"{temp_dir}/bar.html")

    def test_pie(self):
        pie = Pie()
        pie.add("", [list(z) for z in zip(Faker.choose(), Faker.values())])
        pie.set_global_opts(title_opts=opts.TitleOpts(title="Pie示例"))
        pie.render(f"{temp_dir}/pie.html")

    def test_line(self):
        line = Line()
        line.add_xaxis(Faker.choose())
        line.add_yaxis("数量", Faker.values())
        line.set_global_opts(title_opts=opts.TitleOpts(title="Line示例"))
        line.render(f"{temp_dir}/line.html")

    def test_scatter(self):
        scatter = Scatter()
        scatter.add_xaxis(Faker.choose())
        scatter.add_yaxis("数量", Faker.values())
        scatter.set_global_opts(title_opts=opts.TitleOpts(title="Scatter示例"))
        scatter.render(f"{temp_dir}/scatter.html")

    def test_map(self):
        map = Map()
        map.add("中国地图", [list(z) for z in zip(Faker.provinces, Faker.values())], "china")
        map.set_global_opts(title_opts=opts.TitleOpts(title="Map示例"))
        map.render(f"{temp_dir}/map.html")

    def test_radar(self):
        # 传入多维数据,数据点最多6个
        v1 = [[17.2, 7.9, 1.6, 0.8, 0.8]]
        v2 = [[5.4, 2.6, 1.2, 1.0, 0.5]]
        v3 = [[28.0, 8.4, 6.1, 1.9, 0.8]]
        v4 = [[22.3, 5.0, 4.5, 1.7, 1.3]]
        v5 = [[10.2, 2.9, 3.6, 1.4, 0.2]]

        # 调整雷达各维度的范围大小,维度要求四维以上
        x_schema = [
            {"name": "Point", "max": 30, "min": 0, "color": "black", "font_size": 18},
            {"name": "Rebounds", "max": 15, "min": 0, "color": "black", "font_size": 18},
            {"name": "Assists", "max": 8, "min": 0, "color": "black", "font_size": 18},
            {"name": "Steals", "max": 5, "min": 0, "color": "black", "font_size": 18},
            {"name": "Blocks", "max": 2, "min": 0, "color": "black", "font_size": 18},
        ]

        # 画图
        radar_x = Radar()
        radar_x.add_schema(x_schema)
        radar_x.add("Chris Bosh", v1, color="red").set_colors(["red"])
        radar_x.add("Shane Battier", v2, color="green").set_colors(["green"])
        radar_x.add("LeBorn James", v3, color="orange").set_colors(["orange"])
        radar_x.add("Dwayne Wade", v4, color="blue").set_colors(["blue"])
        radar_x.add("Mario Chalmers", v5, color="purple").set_colors(["purple"])

        radar_x.set_global_opts(
            title_opts=opts.TitleOpts(title="Miami Heat Starting Lineup", pos_right="center"),
            legend_opts=opts.LegendOpts(
                legend_icon="roundRect", align="left", pos_left="7%", pos_bottom="14%", orient="vertical"
            ),
        )

        radar_x.render(f"{temp_dir}/radar.html")
