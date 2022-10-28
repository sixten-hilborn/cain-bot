from cainbot.d2runewizard import D2RunewizardClient
from cainbot.cainbot import all_zones_flat
import unittest


class TestCainbot(unittest.TestCase):

    def test_get_terror_zone(self):
        current_zone = D2RunewizardClient.get_terror_zone()
        self.assertIsNotNone(current_zone)
        self.assertIn(current_zone['terrorZone']['zone'], all_zones_flat())
