import unittest

from tests import TEST_DATA_DIR

import bot30.parsers


class MapcycleParserTestCase(unittest.TestCase):

    def test_parser(self):
        mapcycle_file = TEST_DATA_DIR / 'mapcycle.txt'
        parser = bot30.parsers.MapCycleParser()
        rv = parser.parse(mapcycle_file)
        self.assertEqual(len(rv), 16)
        first_map = list(rv.keys())[0]
        self.assertEqual(first_map, 'ut4_casa')
