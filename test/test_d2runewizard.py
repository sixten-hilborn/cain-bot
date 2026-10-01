from cainbot.d2runewizard import D2RunewizardClient
from cainbot.cainbot import all_zones_flat
import unittest


class TestCainbot(unittest.TestCase):

    def test_get_terror_zone(self):
        client = D2RunewizardClient(contact_email="test@example.com")
        current_zone = client.get_terror_zone()
        assert current_zone is not None
        self.assertIn(current_zone.name, all_zones_flat())
