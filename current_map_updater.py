import asyncio
import datetime
import logging
from typing import List, Optional

import discord

import bot30
from bot30.clients import Bot30Client, QuakeClient
from bot30.models import QuakePlayers

logger = logging.getLogger('bot30.current_map')

EMBED_MAPCYCLE_TITLE = 'Current Map'
EMBED_MAPCYCLE_COLOR = discord.Color.dark_red()


def find_mapcycle_message(
        messages: List[discord.Message]
) -> Optional[discord.Message]:
    for msg in messages:
        for embed in msg.embeds:
            if embed.title == EMBED_MAPCYCLE_TITLE:
                return msg
    return None


def create_mapcycle_embed(players: QuakePlayers) -> discord.Embed:
    embed = discord.Embed(
        title=EMBED_MAPCYCLE_TITLE,
        description=players.mapname,
        color=EMBED_MAPCYCLE_COLOR,
    )
    info = f'{players.player_count} ({players.gametime})'
    embed.add_field(name='Player Count (Game Time)', value=info, inline=False)
    if players.players:
        team_r = [
            f'{p.name} ({"/".join(p.score)})'
            for p in players.players if p.team == 'RED'
        ]
        team_b = [
            f'{p.name} ({"/".join(p.score)})'
            for p in players.players if p.team == 'BLUE'
        ]
        if team_r or team_b:
            team_r = '\n'.join(team_r) if team_r else '...'
            team_b = '\n'.join(team_b) if team_b else '...'
            embed.add_field(name=f'Red ({players.score_red})', value=team_r, inline=True)
            embed.add_field(name=f'Blue ({players.score_blue})', value=team_b, inline=True)
        else:
            team_free = [
                f'{p.name} ({"/".join(p.score)})'
                for p in players.players if p.team == 'FREE'
            ]
            if team_free:
                team_free = '\n'.join(team_free)
                embed.add_field(name='Players', value=team_free, inline=False)
        team_spec = [
            f'{p.name}'
            for p in players.players if p.team == 'SPECTATOR'
        ]
        if team_spec:
            team_spec = '\n'.join(team_spec)
            embed.add_field(name='Spec', value=team_spec, inline=False)
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    embed.set_footer(
        text=(
            f'\nLast Updated: {now.strftime("%Y-%m-%d %H:%M %Z")}'
        )
    )
    return embed


async def update_current_map(client: Bot30Client) -> None:
    logger.info('Looking for channel named [%s]', bot30.CHANNEL_NAME_MAPCYCLE)
    channel = await client.channel_by_name(bot30.CHANNEL_NAME_MAPCYCLE)
    logger.info('Found channel: %s [%s]', channel.name, channel.id)
    logger.info('Fetching last 2 messages if posted by %r', bot30.BOT_USER)
    last_messages = await client.last_messages(channel, limit=2)
    logger.info('Found [%s] messages', len(last_messages))
    logger.info('Looking for last message with the %r embed title',
                EMBED_MAPCYCLE_TITLE)
    message = find_mapcycle_message(last_messages)
    logger.info('Creating current map embed')
    async with QuakeClient(bot30.GAME_SERVER_IP, bot30.GAME_SERVER_PORT) as qc:
        players = await qc.players(bot30.GAME_SERVER_RCON_PASS)
    embed = create_mapcycle_embed(players)
    if message:
        logger.info('Updating existing message: %s', message.id)
        await message.edit(embed=embed)
    else:
        logger.info('Sending new message')
        await channel.send(embed=embed)


async def async_main() -> None:
    logger.info('Current Map Updater Start')

    client = Bot30Client(bot30.BOT_USER, bot30.BOT_SERVER_NAME)
    logger.info('%s', client)
    await client.login(bot30.BOT_TOKEN)
    try:
        await update_current_map(client)
    except Exception as exc:
        logger.exception(exc)
        raise
    finally:
        await client.close()

    await asyncio.sleep(0.5)
    logger.info('Current Map Updater End')


if __name__ == '__main__':
    asyncio.run(async_main())
