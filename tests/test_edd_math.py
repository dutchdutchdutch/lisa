import unittest
from src.math import add

class TestEDDMath(unittest.TestCase):
    def test_add(self):
        self.assertEqual(add(1, 1), 2)
