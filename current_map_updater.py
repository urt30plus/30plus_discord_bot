import asyncio
import logging

import discord

import bot30
from bot30.clients import Bot30Client, QuakeClient
from bot30.models import QuakePlayers, QuakePlayer

logger = logging.getLogger('bot30.current_map')

EMBED_CURRENT_MAP_TITLE = 'Current Map'
EMBED_CURRENT_MAP_COLOR = discord.Color.dark_red()
EMBED_NO_TEAM = '.' * (15 + 12)


def player_score_display(players: list[QuakePlayer]) -> list[str]:
    return [
        f'{p.name[:15]:15} '
        f'[{p.kills:3}/{p.deaths:2}/{p.assists:2}]'
        for p in players
    ]


def add_player_fields(embed: discord.Embed, players: QuakePlayers) -> None:
    team_r = player_score_display(players.team_red)
    team_b = player_score_display(players.team_blue)
    if team_r or team_b:
        team_r = '\n'.join(team_r) if team_r else EMBED_NO_TEAM
        team_b = '\n'.join(team_b) if team_b else EMBED_NO_TEAM
        team_r = f"```{team_r}```"
        team_b = f"```{team_b}```"
        embed.add_field(name=f'Red ({players.score_red})', value=team_r,
                        inline=True)
        embed.add_field(name=f'Blue ({players.score_blue})', value=team_b,
                        inline=True)
    else:
        team_free = player_score_display(players.team_free)
        if team_free:
            team_free = '\n'.join(team_free)
            team_free = f"```{team_free}```"
            embed.add_field(name='Players', value=team_free, inline=False)
    team_spec = [f'{p.name}' for p in players.spectators]
    if team_spec:
        team_spec = '\n'.join(team_spec)
        team_spec = f"```{team_spec}```"
        embed.add_field(name='Spectators', value=team_spec, inline=False)


async def get_players() -> QuakePlayers:
    async with QuakeClient(
            host=bot30.GAME_SERVER_IP,
            port=bot30.GAME_SERVER_PORT,
            rcon_pass=bot30.GAME_SERVER_RCON_PASS,
    ) as c:
        return await c.players()


def create_players_embed(players: QuakePlayers) -> discord.Embed:
    description = players.mapname if players else '*Error retrieving map info*'
    embed = discord.Embed(
        title=EMBED_CURRENT_MAP_TITLE,
        description=description,
        color=EMBED_CURRENT_MAP_COLOR,
    )
    embed.set_footer(text=f'\n\nLast Updated: {bot30.utc_now_str()}')
    if players:
        if players.players:
            info = f'{players.gametime} / {players.player_count}'
            embed.add_field(name='Game Time / Player Count', value=info,
                            inline=False)
            add_player_fields(embed, players)
        else:
            embed.description += '\n\n*No players online*'
    return embed


async def create_embed() -> discord.Embed:
    logger.info('Creating current map embed')
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
