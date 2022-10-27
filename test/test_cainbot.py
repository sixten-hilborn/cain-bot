from cainbot import cainbot
import unittest


class TestCainbot(unittest.TestCase):

    def test_rune_list(self):
        self.assertEqual(cainbot.runes[0], "el")
        self.assertEqual(cainbot.runes[-1], "zod")


if __name__ == '__main__':
    unittest.main()
