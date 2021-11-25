import asyncio
import enum
import logging
from typing import List

import asyncio_dgram
import discord

logger = logging.getLogger(__name__)


class Bot30Client(discord.Client):

    def __init__(
            self,
            bot_user: str,
            server_name: str,
            *args,
            **kwargs
    ) -> None:
        self.bot_user = bot_user
        self.server_name = server_name
        self._guild = None
        super().__init__(*args, **kwargs)

    async def login(self, token, *, bot=True):
        await super().login(token, bot=bot)
        async for guild in super().fetch_guilds():
            if guild.name == self.server_name:
                self._guild = guild
                break
        else:
            raise LookupError(f'Server {self.server_name} not found')

    async def channel_by_name(self, name: str) -> discord.TextChannel:
        channels = await self._guild.fetch_channels()
        for ch in channels:
            if ch.name == name:
                return ch
        else:
            raise LookupError(f'Channel {name} not found')

    async def last_messages(
            self,
            channel: discord.TextChannel,
            limit: int = 1,
    ) -> List[discord.Message]:
        messages = []
        async for msg in channel.history(limit=limit):
            author = msg.author
            author_user = f'{author.name}#{author.discriminator}'
            if author.bot and author_user == self.bot_user:
                messages.append(msg)
        return messages

    def __str__(self) -> str:
        return (
            'Bot30Client('
            f'bot_user={self.bot_user!r}, server={self.server_name!r}'
            ')'
        )


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
    def __init__(self, name: str, score: int, ping: int) -> None:
        self.name = name
        self.score = score
        self.ping = ping

    def __repr__(self) -> str:
        return (
            'QuakePlayer('
            f'name={self.name}, score={self.score}, ping={self.ping}'
            ')'
        )


class QuakeStatus:
    def __init__(self) -> None:
        self.settings = {}
        self.players = []

    @property
    def mapname(self) -> str:
        return self.settings.get('mapname')

    @property
    def gametype(self) -> QuakeGameType:
        code = self.settings.get('g_gametype')
        return QuakeGameType(code)

    @staticmethod
    def from_bytes(data: bytes) -> 'QuakeStatus':
        lines = data[4:].decode('latin-1').splitlines()
        assert lines[0] == 'statusResponse'
        opts = lines[1].split('\\')[1:]
        qstatus = QuakeStatus()
        qstatus.settings = dict(zip(opts[0::2], opts[1::2]))
        for entry in lines[2:]:
            score, ping, name = entry.split(maxsplit=2)
            player = QuakePlayer(name.strip('"'), int(score), int(ping))
            qstatus.players.append(player)
        return qstatus

    def __str__(self) -> str:
        return (
            'QuakeStatus('
            f'map={self.mapname}, '
            f'gametype={self.gametype}, '
            f'players={self.players}'
            ')'
        )


class QuakeClient:

    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self.stream = None

    async def connect(self) -> None:
        if not self.stream:
            self.stream = await asyncio_dgram.connect((self.host, self.port))

    async def status(self, timeout: float = 2.0) -> QuakeStatus:
        await self.connect()
        await self.stream.send(b"\xFF\xFF\xFF\xFFgetstatus")
        data, _ = await asyncio.wait_for(self.stream.recv(), timeout=timeout)
        return QuakeStatus.from_bytes(data)

    async def close(self) -> None:
        self.stream.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
