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


def add_player_fields(embed: discord.Embed, players: QuakePlayers) -> None:
    team_r = [f'{p.name} ({"/".join(p.score)})' for p in players.team_red]
    team_b = [f'{p.name} ({"/".join(p.score)})' for p in players.team_blue]
    if team_r or team_b:
        team_r = '\n'.join(team_r) if team_r else '...'
        team_b = '\n'.join(team_b) if team_b else '...'
        embed.add_field(name=f'Red ({players.score_red})', value=team_r,
                        inline=True)
        embed.add_field(name=f'Blue ({players.score_blue})', value=team_b,
                        inline=True)
    else:
        team_free = [f'{p.name} ({"/".join(p.score)})' for p in players.team_free]
        if team_free:
            team_free = '\n'.join(team_free)
            embed.add_field(name='Players', value=team_free, inline=False)
    team_spec = [f'{p.name}' for p in players.spectators]
    if team_spec:
        team_spec = '\n'.join(team_spec)
        embed.add_field(name='Spec', value=team_spec, inline=False)


async def create_mapcycle_embed() -> discord.Embed:
    logger.info('Creating current map embed')
    async with QuakeClient(bot30.GAME_SERVER_IP, bot30.GAME_SERVER_PORT) as qc:
        players = await qc.players(bot30.GAME_SERVER_RCON_PASS)
    embed = discord.Embed(
        title=EMBED_CURRENT_MAP_TITLE,
        description=players.mapname,
        color=EMBED_CURRENT_MAP_COLOR,
    )
    if players.players:
        info = f'{players.gametime} / {players.player_count}'
        embed.add_field(name='Game Time / Player Count', value=info, inline=False)
        add_player_fields(embed, players)
    else:
        embed.description += '\n\n*No players online*'
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    embed.set_footer(
        text=(
            f'\nLast Updated: {now.strftime("%Y-%m-%d %H:%M %Z")}'
        )
    )
    return embed


async def update_current_map(client: Bot30Client) -> None:
    await client.login(bot30.BOT_TOKEN)
    channel_message, embed = await asyncio.gather(
        client.fetch_embed_message(bot30.CHANNEL_NAME_MAPCYCLE,
                                   EMBED_CURRENT_MAP_TITLE),
        create_mapcycle_embed(),
    )
    channel, message = channel_message
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
    try:
        await asyncio.wait_for(update_current_map(client), timeout=30)
    except Exception as exc:
        logger.exception(exc)
        raise
    finally:
        await asyncio.wait_for(client.close(), timeout=10)

    await asyncio.sleep(0.5)
    logger.info('Current Map Updater End')


if __name__ == '__main__':
    asyncio.run(async_main())
