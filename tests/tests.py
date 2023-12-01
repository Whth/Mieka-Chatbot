# 导入所需的库和模块
import pathlib
from typing import List
from unittest import TestCase


class VisualizationTestCase(TestCase):
    def setUp(self):
        self.temp_file_list: List[str] = []

    def test_echarts(self):
        from pyecharts import options as opts
        from pyecharts.charts import Bar

        # 创建一个Bar对象，设置图表的标题、副标题、数据等属性
        bar = (
            Bar()
            .add_xaxis(["衬衫", "羊毛衫", "雪纺衫", "裤子", "高跟鞋", "袜子"])
            .add_yaxis("商家A", [5, 20, 36, 10, 75, 90])
            .add_yaxis("商家B", [15, 6, 45, 20, 65, 55])
            .set_global_opts(title_opts=opts.TitleOpts(title="柱状图示例"))
        )

        save_path = "bar_example.html"
        # 使用render()方法将图表渲染为HTML文件
        bar.render(save_path)
        self.temp_file_list.append(save_path)

    def test_manim(self):
        from manim import Scene, config, Text, Write

        class ArtTextScene(Scene):
            def construct(self):
                art_text = Text("艺术字", font="SimHei", font_size=48)
                self.play(Write(art_text))
                self.wait()

        # 保存为png文件
        config.media_dir = "."
        config.output_file = "art_text_video"
        config.format = "png"
        config.enable_gui = True
        config.write_to_movie = True
        # 运行脚本
        scene = ArtTextScene()
        scene.render()

        self.temp_file_list.append(str(pathlib.Path("./images").absolute()))
        self.temp_file_list.append(str(pathlib.Path("./texts").absolute))

    def test_selenium(self):
        from selenium import webdriver
        from PIL import Image
        from io import BytesIO
        import time

        # 启动浏览器并打开网页
        url = r"www.baidu.com"
        driver = webdriver.Edge()
        driver.set_window_size(1000, 800)
        driver.get(url)

        # 等待页面加载完成
        time.sleep(3)

        # 截取整个网页的屏幕快照
        screenshot = driver.get_screenshot_as_png()

        # 将截图转换为Image对象
        image = Image.open(BytesIO(screenshot))

        img_path = "screenshot.png"
        # 保存图片到本地文件
        image.save(img_path)
        self.temp_file_list.append(img_path)

        # 关闭浏览器
        driver.quit()

    def tearDown(self):
        import pathlib
        from shutil import rmtree

        for path in self.temp_file_list:
            path = pathlib.Path(path)
            path.unlink(missing_ok=True)
            if path.exists():
                rmtree(path)

    def test_async(self):
        import asyncio

        async def inner_coroutine():
            # 这里是你的异步代码
            pass

        async def outer_coroutine():
            try:
                await inner_coroutine()
            except Exception as e:
                print(f"捕获到内部异常： {e}")

        async def main():
            task = asyncio.create_task(outer_coroutine())
            await task

        asyncio.run(main())
