import asyncio
import logging
import time

import discord

import bot30
from bot30.clients import Bot30Client, RCONClient
from bot30.models import Player, Server

logger = logging.getLogger("bot30.current_map")

START_TICK = time.monotonic()

# Max embed field length is roughly 48. We use 18 to display the
# ` [K../D./A.] 123ms` scores, and we want to leave a few chars
# for it to fit comfortably
EMBED_NO_PLAYERS = "```\n" + " " * (24 + 18) + "\n```"


def format_player(p: Player) -> str:
    ping = f"{p.ping:3}ms" if p.ping > 0 else ""
    return f"{p.name[:24]:24} [{p.kills:3}/{p.deaths:2}/{p.assists:2}] {ping}"


def player_score_display(players: list[Player]) -> str | None:
    if not players:
        return None

    return "```\n" + "\n".join([format_player(p) for p in players]) + "\n```"


def add_player_fields(embed: discord.Embed, server: Server) -> None:
    team_r = player_score_display(server.team_red)
    team_b = player_score_display(server.team_blue)
    if team_r or team_b:
        embed.add_field(
            name=f"Red ({server.score_red})",
            value=team_r or EMBED_NO_PLAYERS,
            inline=False,
        )
        embed.add_field(
            name=f"Blue ({server.score_blue})",
            value=team_b or EMBED_NO_PLAYERS,
            inline=False,
        )
    elif team_free := player_score_display(server.team_free):
        embed.add_field(name="Players", value=team_free, inline=False)

    if server.spectators:
        specs = "```\n" + "\n".join(p.name for p in server.spectators) + "\n```"
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

    last_updated = f"updated <t:{int(time.time())}:R>"
    connect_info = f"`/connect game.urt-30plus.org:{bot30.GAME_SERVER_PORT}`"

    if server:
        if game_type := server.game_type:
            description = f"{server.map_name} ({game_type})"
        else:
            description = server.map_name
        embed.description = f"```\n{description}\n```"
        if server.players:
            embed.colour = discord.Colour.green()
            add_mapinfo_field(embed, server)
            add_player_fields(embed, server)
            embed.add_field(name=connect_info, value=last_updated, inline=False)
        else:
            embed.colour = discord.Colour.light_grey()
            # do not add a field to make updating based on description only
            embed.description += "\n*No players online*\n"
            embed.description += f"\n{connect_info}\n{last_updated}"
    else:
        embed.colour = discord.Colour.red()
        embed.description = "*Unable to retrieve server information*"
        # add last updated as a field to trigger updating
        embed.add_field(name=connect_info, value=last_updated, inline=False)

    return embed


async def server_info() -> Server | None:
    if not (rcon_pass := bot30.GAME_SERVER_RCON_PASS):
        raise RuntimeError("RCON password is not set")
    async with RCONClient(
        host=bot30.GAME_SERVER_IP,
        port=bot30.GAME_SERVER_PORT,
        rcon_pass=rcon_pass,
    ) as c:
        try:
            return await c.server_info()
        except Exception:
            logger.exception("Failed to get server info")
            return None


def should_update_embed(message: discord.Message, embed: discord.Embed) -> bool:
    current_embed = message.embeds[0]
    # embed fields indicate that either players are connected or there was an
    # error getting server info, in either case we want to continue updating
    if current_embed.fields or embed.fields:
        return True
    curr_txt = current_embed.description if current_embed.description else ""
    new_txt = embed.description if embed.description else ""
    # ignore the last line that has the updated timestamp embedded, at this
    # point the messages are `no players online` and we only want to update
    # if the map has changed
    return new_txt.rsplit("\n", maxsplit=1)[0] != curr_txt.rsplit("\n", maxsplit=1)[0]


def same_map_and_specs(s1: Server | None, s2: Server | None) -> bool:
    """
    Used to determine if both server instances reference the same map and
    have the same spectators with no current players. In case we can skip
    updating the embedded message.
    """
    return (
        s1 is not None
        and s2 is not None
        and s1.map_name == s2.map_name
        and s1.player_count == s2.player_count
        and len(s1.spectators) == s1.player_count
        and len(s2.spectators) == s2.player_count
        and sorted(s1.spectators) == sorted(s2.spectators)
    )


async def update_message_embed_periodically(
    message: discord.Message,
    server: Server | None,
) -> None:
    delay = bot30.CURRENT_MAP_UPDATE_DELAY
    stop_at = START_TICK + (bot30.BOT_MAX_RUN_TIME - delay - 1.5)
    while time.monotonic() < stop_at:
        await asyncio.sleep(delay)
        prev_server = server
        server = await server_info()
        if same_map_and_specs(prev_server, server):
            break
        embed = create_server_embed(server)
        logger.debug("Updating message: %s", message.id)
        await message.edit(embed=embed)
        if not embed.fields:
            break


async def update_current_map(client: Bot30Client) -> None:
    await client.login(bot30.BOT_TOKEN)
    channel_name = bot30.CHANNEL_NAME_MAPCYCLE
    embed_title = bot30.CURRENT_MAP_EMBED_TITLE
    channel_message, server = await asyncio.gather(
        client.fetch_embed_message(channel_name, embed_title),
        server_info(),
    )
    channel, message = channel_message
    embed = create_server_embed(server)
    if message:
        if should_update_embed(message, embed):
            logger.info("Updating existing message: %s", message.id)
            await message.edit(embed=embed)
            await update_message_embed_periodically(message, server)
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
            await update_message_embed_periodically(message, server)


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
