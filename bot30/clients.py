import asyncio
import logging
from typing import List

import asyncio_dgram
import discord

from bot30.models import QuakePlayers

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


class QuakeClient:

    CMD_PREFIX = b'\xFF' * 4
    ENCODING = 'latin-1'

    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self.stream = None

    async def connect(self) -> None:
        if not self.stream:
            self.stream = await asyncio_dgram.connect((self.host, self.port))

    async def players(self, rcon_pass: str, timeout: float = 2.0) -> QuakePlayers:
        await self.connect()
        cmd = f'rcon {rcon_pass} players'.encode(self.ENCODING)
        await self.stream.send(self.CMD_PREFIX + cmd)
        data, _ = await asyncio.wait_for(self.stream.recv(), timeout=timeout)
        data = data[len(self.CMD_PREFIX):].decode(self.ENCODING)
        logger.debug('RCON players payload:\n%s', data)
        return QuakePlayers.from_string(data)

    async def close(self) -> None:
        self.stream.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
