import logging

logger = logging.getLogger(__name__)


class MapCycleParser:

    def parse_lines(self, lines):
        result = {}
        map_opts = None
        last_map = None
        for line in lines:
            line = line.strip()
            if not line or line.startswith('//'):
                continue
            elif line == '{':
                map_opts = {}
            elif line == '}':
                result[last_map] = map_opts
                map_opts = None
            elif map_opts is None:
                last_map = line
                result[last_map] = None
            else:
                k, v = line.split(' ', maxsplit=1)
                map_opts[k.strip()] = v.strip().strip('"').strip("'")
        return result

    def parse(self, path):
        with open(path, mode='r', encoding='utf-8') as f:
            lines = f.readlines()
        return self.parse_lines(lines)
