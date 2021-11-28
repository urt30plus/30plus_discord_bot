import enum
import re
from typing import Optional, Tuple


class QuakeGameType(enum.Enum):
    FFA = '0'
    LMS = '1'
    TDM = '3'
    TS = '4'
    FTL = '5'
    CAH = '6'
    CTF = '7'
    BOMB = '8'
    JUMP = '9'
    FREEZETAG = '10'
    GUNGAME = '11'


class QuakePlayer:

    RE_COLOR = re.compile(r'(\^\d)')

    RE_PLAYER = re.compile(r'^(?P<slot>[0-9]+):(?P<name>.*)\s+'
                           r'TEAM:(?P<team>RED|BLUE|SPECTATOR|FREE)\s+'
                           r'KILLS:(?P<kill>[0-9]+)\s+'
                           r'DEATHS:(?P<death>[0-9]+)\s+'
                           r'ASSISTS:(?P<assist>[0-9]+)\s+'
                           r'PING:(?P<ping>[0-9]+|CNCT|ZMBI)\s+'
                           r'AUTH:(?P<auth>.*)\s+IP:(?P<ip>.*)$', re.IGNORECASE)

    def __init__(self, name: str, team: str, score: Tuple[str, ...], ping: str) -> None:
        self.name = name
        self.team = team
        self.score = score
        self.ping = ping

    @staticmethod
    def from_string(data: str) -> 'QuakePlayer':
        m = re.match(QuakePlayer.RE_PLAYER, data.strip())
        if not m:
            raise ValueError(f'Invalid data: {data}')
        player = QuakePlayer(
            name=re.sub(QuakePlayer.RE_COLOR, '', m['name']),
            team=m['team'],
            score=(m['kill'], m['death'], m['assist']),
            ping=m['ping']
        )
        return player

    def __repr__(self) -> str:
        return (
            'QuakePlayer('
            f'name={self.name}, team={self.team}, score={self.score}, ping={self.ping}'
            ')'
        )


class QuakePlayers:

    RE_SCORES = re.compile(r'\s*R:(?P<red>[\d]+)\s+B:(?P<blue>[\d]+)')

    def __init__(self) -> None:
        self.settings = {}
        self.players = []

    @property
    def mapname(self) -> str:
        return self.settings['Map']

    @property
    def player_count(self) -> int:
        return int(self.settings['Players'])

    @property
    def gametype(self) -> str:
        return self.settings['GameType']

    @property
    def scores(self) -> Optional[str]:
        return self.settings.get('Scores')

    @property
    def gametime(self) -> str:
        return self.settings['GameTime']

    @property
    def score_red(self) -> Optional[str]:
        if not self.scores:
            return None
        if m := re.match(self.RE_SCORES, self.scores):
            return m['red']
        return None

    @property
    def score_blue(self) -> Optional[str]:
        if not self.scores:
            return None
        if m := re.match(self.RE_SCORES, self.scores):
            return m['blue']
        return None

    @staticmethod
    def from_string(data: str) -> 'QuakePlayers':
        lines = data.splitlines()
        assert lines.pop(0) == 'print'
        players = QuakePlayers()
        while line := lines.pop(0):
            k, v = line.split(':', maxsplit=1)
            players.settings[k] = v.strip()
            if k == 'GameTime':
                break
        for line in lines:
            prefix, _ = line.split(':', maxsplit=1)
            if prefix.isnumeric():
                players.players.append(QuakePlayer.from_string(line))
        return players

    def __str__(self) -> str:
        return (
            'QuakePlayers('
            f'map={self.mapname}, '
            f'gametype={self.gametype}, '
            f'players={self.player_count}'
            ')'
        )
