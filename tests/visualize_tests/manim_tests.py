import pathlib
import unittest

# 运行场景并捕获输出
from manim import Scene, Write, config, MathTex, Text, RED

temp = "temp/manim"
pathlib.Path(temp).mkdir(parents=True, exist_ok=True)


class TestManimPlots(unittest.TestCase):
    def setUp(self):
        pass

    def test_txt(self):
        # config.disable_caching = True
        config.frame_rate = 30

        class Hellow(Scene):
            def construct(self):
                self.play(Write(Text("Hello World!")))
                self.wait(1)
                self.clear()
                self.play(Write(MathTex("E = mc^2", color=RED)))
                self.wait()

        scene = Hellow()
        scene.render()


if __name__ == "__main__":
    unittest.main()
