import dataclasses
import enum
import functools
import re
from typing import Any, NamedTuple, Self


class PlayerScore(NamedTuple):
    kills: int
    deaths: int
    assists: int


class GameType(enum.Enum):
    FFA = "0"
    LMS = "1"
    TDM = "3"
    TS = "4"
    FTL = "5"
    CAH = "6"
    CTF = "7"
    BOMB = "8"
    JUMP = "9"
    FREEZETAG = "10"
    GUNGAME = "11"


@functools.total_ordering
@dataclasses.dataclass
class Player:
    RE_COLOR = re.compile(r"(\^\d)")

    RE_PLAYER = re.compile(
        r"^(?P<slot>[0-9]+):(?P<name>.*)\s+"
        r"TEAM:(?P<team>RED|BLUE|SPECTATOR|FREE)\s+"
        r"KILLS:(?P<kills>-?[0-9]+)\s+"
        r"DEATHS:(?P<deaths>[0-9]+)\s+"
        r"ASSISTS:(?P<assists>[0-9]+)\s+"
        r"PING:(?P<ping>[0-9]+|CNCT|ZMBI)\s+"
        r"AUTH:(?P<auth>.*)\s+"
        r"IP:(?P<ip_address>.*)$",
        re.IGNORECASE,
    )

    name: str
    team: str
    score: PlayerScore
    ping: int
    auth: str
    ip_address: str

    @property
    def kills(self) -> int:
        return self.score.kills

    @property
    def deaths(self) -> int:
        return self.score.deaths

    @property
    def assists(self) -> int:
        return self.score.assists

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, Player):
            return NotImplemented
        return (self.kills, self.deaths * -1, self.assists, self.name) < (
            other.kills,
            other.deaths * -1,
            other.assists,
            other.name,
        )

    @classmethod
    def from_string(cls, data: str) -> Self:
        if m := re.match(Player.RE_PLAYER, data.strip()):
            name = re.sub(Player.RE_COLOR, "", m["name"])
            score = PlayerScore._make(int(m[x]) for x in PlayerScore._fields)
            ping = -1 if m["ping"] in ("CNCT", "ZMBI") else int(m["ping"])
            return cls(
                name=name,
                team=m["team"],
                score=score,
                ping=ping,
                auth=m["auth"],
                ip_address=m["ip_address"],
            )
        raise ValueError(data)

    def __repr__(self) -> str:
        return (
            "Player("
            f"name={self.name}, team={self.team}, score={self.score}, "
            f"ping={self.ping}, auth={self.auth}, ip_address={self.ip_address}"
            ")"
        )


class Server:
    RE_SCORES = re.compile(r"\s*R:(?P<red>\d+)\s+B:(?P<blue>\d+)")

    def __init__(self) -> None:
        self.settings: dict[str, str] = {}
        self.players: list[Player] = []

    @property
    def map_name(self) -> str:
        return self.settings.get("Map", "Unknown")

    @property
    def player_count(self) -> int:
        return int(self.settings.get("Players", 0))

    @property
    def game_type(self) -> str:
        if game_type := self.settings.get("GameType"):
            return "Gun Game/FFA" if game_type == "FFA" else game_type
        return "Unknown"

    @property
    def scores(self) -> str | None:
        return self.settings.get("Scores")

    @property
    def game_time(self) -> str:
        return self.settings["GameTime"]

    @property
    def score_red(self) -> str | None:
        if not self.scores:
            return None
        if m := re.match(self.RE_SCORES, self.scores):
            return m["red"]
        return None

    @property
    def score_blue(self) -> str | None:
        if not self.scores:
            return None
        if m := re.match(self.RE_SCORES, self.scores):
            return m["blue"]
        return None

    def _get_team(self, team_name: str) -> list[Player]:
        return [p for p in self.players if p.team == team_name]

    @property
    def spectators(self) -> list[Player]:
        return self._get_team("SPECTATOR")

    @property
    def team_free(self) -> list[Player]:
        return self._get_team("FREE")

    @property
    def team_red(self) -> list[Player]:
        return self._get_team("RED")

    @property
    def team_blue(self) -> list[Player]:
        return self._get_team("BLUE")

    @classmethod
    def from_string(cls, data: str) -> Self:
        server = cls()
        in_header = True
        for line in data.splitlines():
            k, v = line.split(":", maxsplit=1)
            if in_header:
                server.settings[k] = v.strip()
                if k == "GameTime":
                    in_header = False
            elif k.isnumeric():
                player = Player.from_string(line)
                server.players.append(player)
            elif k == "Map":
                # back-to-back messages, start over
                server.settings[k] = v.strip()
                in_header = True

        if server.player_count != len(server.players):
            msg = (
                f"Player count {server.player_count} does not match "
                f"players {len(server.players)}"
                f"\n\n{data}"
            )
            raise RuntimeError(msg)

        if not server.map_name:
            raise RuntimeError("MAP_NOT_SET", data)

        server.players.sort(reverse=True)
        return server

    def __str__(self) -> str:
        return (
            "Server("
            f"map_name={self.map_name}, "
            f"game_type={self.game_type}, "
            f"players={self.player_count}"
            ")"
        )
