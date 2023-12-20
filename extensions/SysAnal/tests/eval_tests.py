import unittest

from ..eval_tools import EvalMapping, Entity, disp_evaler_constructor


class MyTestCase(unittest.TestCase):
    def test_valid_input(self):
        score_level = [1, 2, 3, 4]
        baselines = [0, 5, 10]
        evaler = disp_evaler_constructor(score_level, baselines)
        self.assertEqual(1, evaler(-5))
        self.assertEqual(1, evaler(0))
        self.assertEqual(2, evaler(3))
        self.assertEqual(2, evaler(5))
        self.assertEqual(3, evaler(7))
        self.assertEqual(3, evaler(10))
        self.assertEqual(4, evaler(15))

        evaler = disp_evaler_constructor(score_level, sorted(baselines, reverse=True))
        self.assertEqual(4, evaler(-5))
        self.assertEqual(3, evaler(0))
        self.assertEqual(3, evaler(3))
        self.assertEqual(2, evaler(5))
        self.assertEqual(2, evaler(7))
        self.assertEqual(1, evaler(10))
        self.assertEqual(1, evaler(15))

    def test_something(self):
        a1 = [
            Entity(dimensions=[1400.0, 4.1, 22.0, 115.0, 4.0]),
            Entity(dimensions=[1800.0, 4.8, 35.0, 125.0, 4.0]),
            Entity(dimensions=[2150.0, 6.5, 52.0, 90.0, 2.0]),
        ]

        score_level = [0, 1, 2, 3, 4, 5]
        mapping = EvalMapping(
            eval_funcs=[
                disp_evaler_constructor(score_level=score_level, baselines=[1000, 1300, 1600, 1900, 2200]),
                disp_evaler_constructor(score_level=score_level, baselines=[7, 6, 5, 4, 3]),
                disp_evaler_constructor(score_level=score_level, baselines=[60, 50, 40, 30, 20]),
                disp_evaler_constructor(score_level=score_level, baselines=[60, 80, 100, 120, 140]),
                disp_evaler_constructor(score_level=score_level, baselines=[1, 2, 3, 4, 5]),
            ],
            dimensions_type=[float] * 5,
            dimensions_score_weight=[0.25, 0.25, 0.1, 0.2, 0.2],
        )
        shall_scores = [2.85, 3.2, 1.95]
        for en, score in zip(a1, shall_scores):
            en: Entity
            mapping.eval_entity(en)
            self.assertEqual(score, en.score)

            print(en)


if __name__ == "__main__":
    unittest.main()
