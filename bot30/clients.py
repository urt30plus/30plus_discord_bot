import asyncio
import logging
from types import TracebackType
from typing import Any, Self

import asyncio_dgram
import discord

from bot30.models import Server

logger = logging.getLogger(__name__)


class Bot30ClientError(Exception):
    pass


class Bot30Client(discord.Client):
    def __init__(
        self,
        bot_user: str,
        server_name: str,
        **kwargs: Any,
    ) -> None:
        if "intents" not in kwargs:
            kwargs["intents"] = discord.Intents.all()
        super().__init__(**kwargs)
        self.bot_user = bot_user
        self.server_name = server_name
        self._guild: discord.Guild | None = None

    async def login(self, token: str) -> None:
        await super().login(token)
        async for guild in super().fetch_guilds():
            if guild.name == self.server_name:
                self._guild = guild
                break
        else:
            raise Bot30ClientError("SERVER_NOT_FOUND", self.server_name)

    async def _channel_by_name(self, name: str) -> discord.TextChannel:
        logger.info("Looking for channel named [%s]", name)
        if self._guild is None:
            raise RuntimeError("GUILD_NOT_SET")
        channels = await self._guild.fetch_channels()
        for ch in channels:
            if ch.name == name:
                logger.info("Found channel: %s [%s]", ch.name, ch.id)
                if isinstance(ch, discord.TextChannel):
                    return ch
                raise Bot30ClientError("INVALID_CHANNEL_TYPE", name, type(ch))

        raise Bot30ClientError("CHANNEL_NOT_FOUND", name)

    async def _last_messages(
        self,
        channel: discord.TextChannel,
        limit: int = 1,
    ) -> list[discord.Message]:
        messages = []
        logger.info(
            "Fetching last %s messages if posted by %r in channel %s",
            limit,
            self.bot_user,
            channel.name,
        )
        async for msg in channel.history(limit=limit):
            author = msg.author
            author_user = f"{author.name}#{author.discriminator}"
            if author.bot and author_user == self.bot_user:
                messages.append(msg)
        logger.info("Found [%s] messages", len(messages))
        return messages

    async def _find_message_by_embed_title(
        self,
        channel: discord.TextChannel,
        embed_title: str,
        limit: int = 5,
    ) -> discord.Message | None:
        messages = await self._last_messages(channel, limit=limit)
        logger.info("Looking for message with the %r embed title", embed_title)
        for msg in messages:
            for embed in msg.embeds:
                if embed.title == embed_title:
                    return msg
        return None

    async def fetch_embed_message(
        self,
        channel_name: str,
        embed_title: str,
        limit: int = 5,
    ) -> tuple[discord.TextChannel, discord.Message | None]:
        channel = await self._channel_by_name(channel_name)
        message = await self._find_message_by_embed_title(
            channel=channel,
            embed_title=embed_title,
            limit=limit,
        )
        return channel, message

    def __str__(self) -> str:
        return (
            "Bot30Client("
            f"bot_user={self.bot_user!r}, server={self.server_name!r}"
            ")"
        )


class RCONClientError(Exception):
    pass


class RCONClient:
    CMD_PREFIX = b"\xFF" * 4
    REPLY_PREFIX = CMD_PREFIX + b"print\n"
    ENCODING = "latin-1"

    def __init__(self, host: str, port: int, rcon_pass: str) -> None:
        self.host = host
        self.port = port
        self.rcon_pass = rcon_pass
        self.stream: asyncio_dgram.DatagramClient | None = None

    async def connect(self) -> None:
        if self.stream is None:
            self.stream = await asyncio_dgram.connect((self.host, self.port))

    def _check_stream(self) -> None:
        if self.stream is None:
            raise RuntimeError("STEAM_NOT_CONNECTED")

    def _create_rcon_cmd(self, cmd: str) -> bytes:
        return self.CMD_PREFIX + f'rcon "{self.rcon_pass}" {cmd}\n'.encode(
            self.ENCODING
        )

    async def _send_rcon(self, cmd: str, timeout: float, retries: int) -> str:
        self._check_stream()
        rcon_cmd = self._create_rcon_cmd(cmd)
        for i in range(1, retries + 1):
            await self.stream.send(rcon_cmd)
            data = await self._receive(timeout=timeout)
            if data:
                return data.decode(self.ENCODING)

            logger.warning("RCON %s: no data on try %s", cmd, i)
            await asyncio.sleep(timeout * i + 1)

        raise RCONClientError("NO_DATA", cmd)

    async def _receive(self, timeout: float = 0.5) -> bytearray:
        self._check_stream()
        result = bytearray()
        while True:
            try:
                data, _ = await asyncio.wait_for(
                    self.stream.recv(),
                    timeout=timeout,
                )
                result += data.replace(self.REPLY_PREFIX, b"", 1)
            except asyncio.TimeoutError:
                break
        return result

    async def server_info(
        self,
        *,
        timeout: float = 0.75,
        retries: int = 3,
    ) -> Server:
        cmd = "players"
        data = await self._send_rcon(cmd, timeout, retries)
        logger.debug("RCON %s payload:\n%s", cmd, data)
        return Server.from_string(data)

    async def close(self) -> None:
        if self.stream is not None:
            self.stream.close()

    async def __aenter__(self) -> Self:
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException,
        exc_tb: TracebackType,
    ) -> None:
        await self.close()
