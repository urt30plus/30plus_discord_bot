import asyncio
import logging
import time
from typing import Optional

import discord

import bot30
from bot30.clients import Bot30Client, QuakeClient
from bot30.models import QuakePlayers, QuakePlayer

logger = logging.getLogger('bot30.current_map')

START_TICK = time.monotonic()

EMBED_CURRENT_MAP_TITLE = 'Current Map'
EMBED_NO_PLAYERS = '```\n' + '.' * (17 + 12) + '\n```'


def player_score_display(players: list[QuakePlayer]) -> Optional[str]:
    if not players:
        return None
    return '```\n' + '\n'.join([
        f'{p.name[:17]:17} '
        f'[{p.kills:3}/{p.deaths:2}/{p.assists:2}]'
        for p in players
    ]) + '\n```'


def add_player_fields(embed: discord.Embed, players: QuakePlayers) -> None:
    team_r = player_score_display(players.team_red)
    team_b = player_score_display(players.team_blue)
    if team_r or team_b:
        embed.add_field(name=f'Red ({players.score_red})',
                        value=team_r or EMBED_NO_PLAYERS,
                        inline=True)
        embed.add_field(name=f'Blue ({players.score_blue})',
                        value=team_b or EMBED_NO_PLAYERS,
                        inline=True)
    else:
        if team_free := player_score_display(players.team_free):
            embed.add_field(name='Players', value=team_free, inline=False)
    if team_spec := [f'{p.name}' for p in players.spectators]:
        team_spec = '```\n' + '\n'.join(team_spec) + '\n```'
        embed.add_field(name='Spectators', value=team_spec, inline=False)


def add_mapinfo_field(embed: discord.Embed, players: QuakePlayers) -> None:
    info = f'{players.game_time} / Total:{players.player_count:2}'
    if (spec_count := len(players.spectators)) != players.player_count:
        if (free_count := len(players.team_free)) > 0:
            if spec_count:
                info += f'  F:{free_count:2}'
        else:
            info += f'  R:{len(players.team_red):2}  B:{len(players.team_blue):2}'
        if spec_count:
            info += f'  S:{spec_count:2}'
    info = f'```\n{info}\n```'
    embed.add_field(name='Game Time / Player Counts', value=info, inline=False)


def create_players_embed(players: QuakePlayers) -> discord.Embed:
    embed = discord.Embed(title=EMBED_CURRENT_MAP_TITLE)

    if players:
        if game_type := players.game_type:
            description = f'{players.map_name} ({game_type})'
        else:
            description = players.map_name
        embed.description = f'```\n{description:60}\n```'
        if players.players:
            embed.colour = discord.Colour.green()
            add_mapinfo_field(embed, players)
            add_player_fields(embed, players)
        else:
            embed.description += '\n*No players online*'
            embed.colour = discord.Colour.light_gray()
    else:
        embed.colour = discord.Colour.red()
        embed.description = '*Unable to retrieve map information*'

    embed.set_footer(text=f'\n\nLast Updated: {bot30.utc_now_str(secs=True)}')
    return embed


async def get_players() -> QuakePlayers:
    async with QuakeClient(
            host=bot30.GAME_SERVER_IP,
            port=bot30.GAME_SERVER_PORT,
            rcon_pass=bot30.GAME_SERVER_RCON_PASS,
    ) as c:
        return await c.players()


async def create_embed() -> discord.Embed:
    try:
        players = await get_players()
    except Exception:
        logger.exception('Failed to get Players')
        players = None
    return create_players_embed(players)


def should_update_embed(message: discord.Message, embed: discord.Embed) -> bool:
    current_embed = message.embeds[0]
    return (
            current_embed.fields or
            embed.fields or
            current_embed.description.strip() != embed.description.strip()
    )


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
        client.fetch_embed_message(bot30.CHANNEL_NAME_MAPCYCLE,
                                   EMBED_CURRENT_MAP_TITLE),
        create_embed(),
    )
    message: discord.Message
    channel, message = channel_message
    if message:
        if should_update_embed(message, embed):
            logger.info('Updating existing message: %s', message.id)
            await message.edit(embed=embed)
            await update_message_embed_periodically(message)
        else:
            logger.info('Existing message embed is up to date')
    else:
        logger.info('Sending new message')
        await channel.send(embed=embed)


async def async_main() -> None:
    logger.info('Current Map Updater Start')

    client = Bot30Client(bot30.BOT_USER, bot30.BOT_SERVER_NAME)
    logger.info('%s', client)
    try:
        await asyncio.wait_for(
            update_current_map(client),
            timeout=bot30.BOT_MAX_RUN_TIME,
        )
    except Exception as exc:
        logger.exception(exc)
        raise
    finally:
        await asyncio.wait_for(client.close(), timeout=5)

    await asyncio.sleep(0.5)
    logger.info('Current Map Updater End')


if __name__ == '__main__':
    asyncio.run(async_main())
