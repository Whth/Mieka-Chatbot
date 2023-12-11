import unittest

from ..value_conversion import Worth


class TestWorth(unittest.TestCase):
    def test_to_with_abs_sequential_index(self):
        worth = Worth(value=100, sequential_index=0, duration=1)

        new_worth = worth.to_(index_rate=0.1, abs_sequential_index=2)
        self.assertAlmostEqual(121.0, new_worth.value)
        self.assertEqual(2, new_worth.sequential_index)
        self.assertEqual(1, new_worth.duration)

        new_worth = worth.to_(index_rate=0.1, abs_sequential_index=20)
        self.assertAlmostEqual(672.75, new_worth.value, delta=0.01)
        self.assertEqual(20, new_worth.sequential_index)
        self.assertEqual(1, new_worth.duration)

        new_worth = worth.to_(index_rate=0.1, abs_sequential_index=-20)
        self.assertAlmostEqual(14.86, new_worth.value, delta=0.01)
        self.assertEqual(-20, new_worth.sequential_index)
        self.assertEqual(1, new_worth.duration)

    def test_to_with_rel_sequential_index(self):
        worth = Worth(value=100, sequential_index=0, duration=1)

        new_worth = worth.to_(index_rate=0.1, rel_sequential_index=2)
        self.assertAlmostEqual(121.0, new_worth.value)
        self.assertEqual(2, new_worth.sequential_index)
        self.assertEqual(1, new_worth.duration)

        new_worth = worth.to_(index_rate=0.1, rel_sequential_index=20)
        self.assertAlmostEqual(672.75, new_worth.value, delta=0.01)
        self.assertEqual(20, new_worth.sequential_index)
        self.assertEqual(1, new_worth.duration)

        new_worth = worth.to_(index_rate=0.1, rel_sequential_index=-20)
        self.assertAlmostEqual(14.86, new_worth.value, delta=0.01)
        self.assertEqual(-20, new_worth.sequential_index)
        self.assertEqual(1, new_worth.duration)

    def test_to_with_target_duration(self):
        worth = Worth(value=100, sequential_index=0, duration=1)
        new_worth1 = worth.to_(index_rate=0, target_duration=2)
        self.assertAlmostEqual(50.0, new_worth1.value)
        print(new_worth1)
        new_worth2 = worth.to_(index_rate=0.3, target_duration=4)
        self.assertAlmostEqual(35.50, new_worth2.value, delta=0.01)
        print(new_worth2)

        new_worth3 = worth.to_(index_rate=0.3, target_duration=1)
        self.assertAlmostEqual(100.0, new_worth3.value, delta=0.01)
        print(new_worth3)
        new_worth4 = worth.to_(index_rate=0.3, rel_sequential_index=2, target_duration=3)
        self.assertAlmostEqual(100.0, new_worth4.value, delta=0.01)
        print(new_worth4)

    def test_to_with_index_rate(self):
        worth = Worth(value=10, sequential_index=0, duration=1)
        new_worth = worth.to_(index_rate=0.5)
        self.assertEqual(new_worth.value, 10)
        self.assertEqual(new_worth.sequential_index, 0)
        self.assertEqual(new_worth.duration, 1)

    def test_to_with_both_abs_and_rel_sequential_index(self):
        worth = Worth(value=10, sequential_index=0, duration=1)
        with self.assertRaises(ValueError):
            worth.to_(index_rate=0.1, abs_sequential_index=2, rel_sequential_index=1)


if __name__ == "__main__":
    unittest.main()
