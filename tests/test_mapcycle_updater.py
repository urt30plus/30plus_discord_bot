import unittest

from mapcycle_updater import (
    map_mode,
    parse_mapcycle,
)
from tests import TEST_DATA_DIR


class MapModeTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.test_opts = {
            "mod_ctf": "0",
            "mod_gungame": "0",
            "g_instagib": "0",
            "g_gametype": "7",
        }

    def test_ctf_is_default(self):
        r = map_mode(self.test_opts)
        self.assertEqual(r, "")

    def test_gungame_mod(self):
        self.test_opts["mod_gungame"] = "1"
        r = map_mode(self.test_opts)
        self.assertEqual(r, "(GUNGAME d3mod)")

    def test_ctf_mod(self):
        self.test_opts["mod_ctf"] = "1"
        r = map_mode(self.test_opts)
        self.assertEqual(r, "(CTF d3mod)")

    def test_ctf_mod_with_instagib(self):
        self.test_opts["mod_ctf"] = "1"
        self.test_opts["g_instagib"] = "1"
        r = map_mode(self.test_opts)
        self.assertEqual(r, "(CTF d3mod Instagib)")

    def test_gungame(self):
        self.test_opts["g_gametype"] = "11"
        r = map_mode(self.test_opts)
        self.assertEqual(r, "(GUNGAME)")


class ParseMapCycleTestCase(unittest.IsolatedAsyncioTestCase):
    async def _parse(self, file_name):
        return await parse_mapcycle(str(TEST_DATA_DIR / file_name))

    async def test_parse(self):
        cycle = await self._parse("mapcycle.txt")
        self.assertEqual(len(cycle), 16)
        self.assertEqual(cycle["ut4_casa"]["mod_gameType"], "11")

    async def test_parse_plain(self):
        cycle = await self._parse("mapcycle_plain.txt")
        self.assertEqual(len(cycle), 3)
        expect = {"ut4_casa": {}, "ut4_abbey": {}, "ut4_paris": {}}
        self.assertDictEqual(cycle, expect)
