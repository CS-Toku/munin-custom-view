
import unittest


def f(x):
    return x+1


class TestSample(unittest.TestCase):
    def setUp(self):
        print('setUp')

    def test_add(self):
        self.assertEqual(f(3), 4)
        print('test_add')

    def test_add2(self):
        self.assertEqual(f(3), 5)
        print('test_add2')

    def tearDown(self):
        print('tearDown')


