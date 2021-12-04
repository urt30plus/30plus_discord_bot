import asyncio
import datetime
import logging

import discord

import bot30
from bot30.clients import Bot30Client, QuakeClient
from bot30.models import QuakePlayers

logger = logging.getLogger('bot30.current_map')

EMBED_CURRENT_MAP_TITLE = 'Current Map'
EMBED_CURRENT_MAP_COLOR = discord.Color.dark_red()


def create_mapcycle_embed(players: QuakePlayers) -> discord.Embed:
    embed = discord.Embed(
        title=EMBED_CURRENT_MAP_TITLE,
        description=players.mapname,
        color=EMBED_CURRENT_MAP_COLOR,
    )
    info = f'{players.gametime} / {players.player_count}'
    embed.add_field(name='Game Time / Players', value=info, inline=False)
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
            embed.add_field(name=f'Red ({players.score_red})', value=team_r,
                            inline=True)
            embed.add_field(name=f'Blue ({players.score_blue})', value=team_b,
                            inline=True)
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
    channel = await client.channel_by_name(bot30.CHANNEL_NAME_MAPCYCLE)
    message = await client.find_message_by_embed_title(
        channel=channel,
        embed_title=EMBED_CURRENT_MAP_TITLE,
        limit=3,
    )
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
