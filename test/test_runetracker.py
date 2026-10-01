from cainbot import cainbot
import datetime
import unittest


class DummyBotClient():
    def __init__(self):
        self.tracking = {"users": {}}
        self.writes = 0

    def get_or_add_user(self, user):
        if str(user.id) not in self.tracking["users"]:
            self.tracking["users"][str(user.id)] = {
                "track_list": [],
                "notify": cainbot.Notify.MENTION.value,
                "name": str(user)
            }
        return self.tracking["users"][str(user.id)]

    def try_get_user(self, user):
        return self.tracking["users"].get(str(user.id))

    def write_tracking(self):
        self.writes += 1


class TestUser():
    def __init__(self, id):
        self.id = id

    def __str__(self):
        return f"test#{self.id%1000}"


class TestRuneTracker(unittest.TestCase):

    def setUp(self):
        self.client = DummyBotClient()
        self.rune_tracker = cainbot.RuneTracker(self.client)
        self.user = TestUser(1234)

    def test_rune_tracker_add_one(self):
        rune, date = self.rune_tracker.add(self.user, ':gul:', datetime.date(2022, 11, 16))
        self.assertEqual(rune, "gul")
        self.assertEqual(date, datetime.date(2022, 11, 16))
        self.assertIn(rune, cainbot.runes)

    def test_rune_tracker_add_and_list(self):
        list = self.rune_tracker.list_for(self.user)
        self.assertFalse(list)

        self.rune_tracker.add(self.user, ':ist:', datetime.date(2026, 11, 16))
        (entry,) = self.rune_tracker.list_for(self.user)
        self.assertEqual(entry["rune"], "ist")
        self.assertEqual(entry["date"], "2026-11-16")
        self.assertIn(entry["rune"], cainbot.runes)

    def test_rune_tracker_add_and_list_old_season(self):
        list = self.rune_tracker.list_for(self.user)
        self.assertFalse(list)

        self.rune_tracker.add(self.user, ':ist:', datetime.date(2022, 11, 16))
        self.assertFalse(list)
