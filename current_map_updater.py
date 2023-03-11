import asyncio
import logging
import time

# noinspection PyPackageRequirements
import discord

import bot30
from bot30.clients import Bot30Client, RCONClient
from bot30.models import Player, Server

logger = logging.getLogger("bot30.current_map")

START_TICK = time.monotonic()

EMBED_NO_PLAYERS = "```\n" + "." * (17 + 12) + "\n```"


def player_score_display(players: list[Player]) -> str | None:
    if not players:
        return None
    return (
        "```\n"
        + "\n".join(
            [
                f"{p.name[:17]:17} [{p.kills:3}/{p.deaths:2}/{p.assists:2}]"
                for p in players
            ]
        )
        + "\n```"
    )


def add_player_fields(embed: discord.Embed, server: Server) -> None:
    team_r = player_score_display(server.team_red)
    team_b = player_score_display(server.team_blue)
    if team_r or team_b:
        embed.add_field(
            name=f"Red ({server.score_red})",
            value=team_r or EMBED_NO_PLAYERS,
            inline=True,
        )
        embed.add_field(
            name=f"Blue ({server.score_blue})",
            value=team_b or EMBED_NO_PLAYERS,
            inline=True,
        )
    elif team_free := player_score_display(server.team_free):
        embed.add_field(name="Players", value=team_free, inline=False)

    if team_spec := [f"{p.name}" for p in server.spectators]:
        specs = "```\n" + "\n".join(team_spec) + "\n```"
        embed.add_field(name="Spectators", value=specs, inline=False)


def add_mapinfo_field(embed: discord.Embed, server: Server) -> None:
    info = f"{server.game_time} / Total:{server.player_count:2}"
    if (spec_count := len(server.spectators)) != server.player_count:
        if (free_count := len(server.team_free)) > 0:
            if spec_count:
                info += f"  F:{free_count:2}"
        else:
            info += f"  R:{len(server.team_red):2}  B:{len(server.team_blue):2}"
        if spec_count:
            info += f"  S:{spec_count:2}"
    info = f"```\n{info}\n```"
    embed.add_field(name="Game Time / Player Counts", value=info, inline=False)


def create_server_embed(server: Server | None) -> discord.Embed:
    embed = discord.Embed(title=bot30.CURRENT_MAP_EMBED_TITLE)

    if server:
        if game_type := server.game_type:
            description = f"{server.map_name} ({game_type})"
        else:
            description = server.map_name
        embed.description = f"```\n{description:60}\n```"
        if server.players:
            embed.colour = discord.Colour.green()
            add_mapinfo_field(embed, server)
            add_player_fields(embed, server)
        else:
            embed.description += "\n*No players online*"
            embed.colour = discord.Colour.light_grey()
    else:
        embed.colour = discord.Colour.red()
        embed.description = "*Unable to retrieve server information*"

    embed.add_field(
        name=f"Last updated <t:{int(time.time())}:R>",
        value="",
        inline=False,
    )

    return embed


async def get_server_info() -> Server:
    if not (rcon_pass := bot30.GAME_SERVER_RCON_PASS):
        raise RuntimeError("RCON password is not set")
    async with RCONClient(
        host=bot30.GAME_SERVER_IP,
        port=bot30.GAME_SERVER_PORT,
        rcon_pass=rcon_pass,
    ) as c:
        return await c.server_info()


async def create_embed() -> discord.Embed:
    try:
        server = await get_server_info()
    except Exception:
        logger.exception("Failed to get server info")
        server = None
    return create_server_embed(server)


def should_update_embed(message: discord.Message, embed: discord.Embed) -> bool:
    current_embed = message.embeds[0]
    if (current_embed.fields or embed.fields) and (
        len(current_embed.fields) > 1 or len(embed.fields) > 1
    ):
        # check fields len to ignore our last updated field
        return True
    curr_txt = current_embed.description if current_embed.description else ""
    new_txt = embed.description if embed.description else ""
    return curr_txt.strip() != new_txt.strip()


async def update_message_embed_periodically(message: discord.Message) -> None:
    delay = bot30.CURRENT_MAP_UPDATE_DELAY
    stop_at = START_TICK + (bot30.BOT_MAX_RUN_TIME - delay - 1.5)
    while time.monotonic() < stop_at:
        await asyncio.sleep(delay)
        embed = await create_embed()
        await message.edit(embed=embed)
        if not embed.fields:
            break


async def update_current_map(client: Bot30Client) -> None:
    await client.login(bot30.BOT_TOKEN)
    embed: discord.Embed
    channel_message, embed = await asyncio.gather(
        client.fetch_embed_message(
            bot30.CHANNEL_NAME_MAPCYCLE, bot30.CURRENT_MAP_EMBED_TITLE
        ),
        create_embed(),
    )
    message: discord.Message
    channel, message = channel_message
    if message:
        if should_update_embed(message, embed):
            logger.info("Updating existing message: %s", message.id)
            await message.edit(embed=embed)
            await update_message_embed_periodically(message)
        else:
            logger.info("Existing message embed is up to date")
    else:
        logger.info("Sending new message")
        await channel.send(embed=embed)
        # in case players are connected when we create the message, keep
        # updating it if needed
        _, message = await client.fetch_embed_message(
            bot30.CHANNEL_NAME_MAPCYCLE, bot30.CURRENT_MAP_EMBED_TITLE
        )
        if message:
            await update_message_embed_periodically(message)


async def async_main() -> None:
    logger.info("Current Map Updater Start")

    client = Bot30Client(bot30.BOT_USER, bot30.BOT_SERVER_NAME)
    logger.info("%s", client)
    try:
        await asyncio.wait_for(
            update_current_map(client),
            timeout=bot30.BOT_MAX_RUN_TIME,
        )
    except Exception:
        logger.exception("Failed to update current map")
        raise
    finally:
        await asyncio.wait_for(client.close(), timeout=5)

    await asyncio.sleep(0.5)
    logger.info("Current Map Updater End")


if __name__ == "__main__":
    asyncio.run(async_main())
