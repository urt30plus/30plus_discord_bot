import dataclasses
import enum
import functools
import re
from typing import Optional


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


@functools.total_ordering
@dataclasses.dataclass()
class QuakePlayer:
    RE_COLOR = re.compile(r'(\^\d)')

    RE_PLAYER = re.compile(r'^(?P<slot>[0-9]+):(?P<name>.*)\s+'
                           r'TEAM:(?P<team>RED|BLUE|SPECTATOR|FREE)\s+'
                           r'KILLS:(?P<kill>[0-9]+)\s+'
                           r'DEATHS:(?P<death>[0-9]+)\s+'
                           r'ASSISTS:(?P<assist>[0-9]+)\s+'
                           r'PING:(?P<ping>[0-9]+|CNCT|ZMBI)\s+'
                           r'AUTH:(?P<auth>.*)\s+'
                           r'IP:(?P<ip>.*)$', re.IGNORECASE)

    name: str
    team: str
    score: tuple[str, ...]
    ping: str

    @property
    def kills(self) -> int:
        return int(self.score[0])

    @property
    def deaths(self) -> int:
        return int(self.score[1])

    @property
    def assists(self) -> int:
        return int(self.score[2])

    def __lt__(self, other) -> bool:
        if not isinstance(other, QuakePlayer):
            return NotImplemented
        return (
                (self.kills, self.deaths * -1, self.assists, self.name) <
                (other.kills, other.deaths * -1, other.assists, other.name)
        )

    @staticmethod
    def from_string(data: str) -> 'QuakePlayer':
        if m := re.match(QuakePlayer.RE_PLAYER, data.strip()):
            return QuakePlayer(
                name=re.sub(QuakePlayer.RE_COLOR, '', m['name']),
                team=m['team'],
                score=(m['kill'], m['death'], m['assist']),
                ping=m['ping'],
            )
        raise ValueError(f'Invalid data: {data}')

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
        return int(self.settings.get('Players', 0))

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

    def _get_team(self, team_name: str) -> list[QuakePlayer]:
        return [p for p in self.players if p.team == team_name]

    @property
    def spectators(self) -> list[QuakePlayer]:
        return self._get_team('SPECTATOR')

    @property
    def team_free(self) -> list[QuakePlayer]:
        return self._get_team('FREE')

    @property
    def team_red(self) -> list[QuakePlayer]:
        return self._get_team('RED')

    @property
    def team_blue(self) -> list[QuakePlayer]:
        return self._get_team('BLUE')

    @staticmethod
    def from_string(data: str) -> 'QuakePlayers':
        players = QuakePlayers()
        in_header = True
        for line in data.splitlines():
            k, v = line.split(':', maxsplit=1)
            if in_header:
                players.settings[k] = v.strip()
                if k == 'GameTime':
                    in_header = False
            else:
                if k.isnumeric():
                    player = QuakePlayer.from_string(line)
                    players.players.append(player)

        if players.player_count != len(players.players):
            raise RuntimeError(
                f'Player count {players.player_count} does not match '
                f'players {len(players.players)}'
                f'\n\n{data}'
            )

        players.players.sort(reverse=True)
        return players

    def __str__(self) -> str:
        return (
            'QuakePlayers('
            f'map={self.mapname}, '
            f'gametype={self.gametype}, '
            f'players={self.player_count}'
            ')'
        )
