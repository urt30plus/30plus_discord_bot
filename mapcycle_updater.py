import asyncio
import datetime
import logging
from typing import Dict

import aiofiles
import discord

import bot30
from bot30.clients import Bot30Client
from bot30.models import QuakeGameType

logger = logging.getLogger('bot30.mapcycle')

EMBED_MAPCYCLE_TITLE = 'Map Cycle'
EMBED_MAPCYCLE_COLOR = discord.Color.dark_blue()


def map_mode(map_opts: Dict[str, str]) -> str:
    if map_opts.get('mod_gungame', '0') == '1':
        result = QuakeGameType.GUNGAME.name + ' d3mod'
    elif map_opts.get('mod_ctf', '0') == '1':
        result = QuakeGameType.CTF.name + ' d3mod'
    else:
        game_type = map_opts.get('g_gametype', '7')
        result = QuakeGameType(game_type).name
    if map_opts.get('g_instagib') == '1':
        result += ' Instagib'
    if result == QuakeGameType.CTF.name:
        return ''
    else:
        return f'({result})'


async def parse_mapcycle(mapcycle_file: str) -> Dict[str, Dict]:
    result = {}
    map_opts = None
    last_map = None
    async with aiofiles.open(mapcycle_file, mode='r', encoding='utf-8') as f:
        async for line in f:
            line = line.strip()
            if not line or line.startswith('//'):
                continue
            elif line == '{':
                map_opts = {}
            elif line == '}':
                result[last_map] = map_opts
                map_opts = None
            elif map_opts is None:
                last_map = line
                result[last_map] = {}
            else:
                k, v = line.split(' ', maxsplit=1)
                map_opts[k.strip()] = v.strip().strip('"\'')
    return result


async def create_mapcycle_embed(mapcycle_file: str) -> discord.Embed:
    logger.info('Creating map cycle embed using file [%s]', mapcycle_file)
    cycle = await parse_mapcycle(mapcycle_file)
    description = '\n'.join(
        [f'{k.rstrip("_")} {map_mode(v)}' for k, v in cycle.items()]
    )
    embed = discord.Embed(
        title=EMBED_MAPCYCLE_TITLE,
        description=description,
        color=EMBED_MAPCYCLE_COLOR,
    )
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    embed.set_footer(
        text=(
            f'\nTotal Maps: {len(cycle)}'
            f'\nLast Updated: {now.strftime("%Y-%m-%d %H:%M %Z")}'
        )
    )
    return embed


async def update_mapcycle(client: Bot30Client) -> None:
    await client.login(bot30.BOT_TOKEN)
    channel_message, embed = await asyncio.gather(
        client.fetch_embed_message(bot30.CHANNEL_NAME_MAPCYCLE,
                                   EMBED_MAPCYCLE_TITLE),
        create_mapcycle_embed(bot30.MAPCYCLE_FILE),
    )
    channel, message = channel_message
    if message:
        logger.info('Updating existing message: %s', message.id)
        await message.edit(embed=embed)
    else:
        logger.info('Sending new message')
        await channel.send(embed=embed)


async def async_main() -> None:
    logger.info('Map Cycle Updater Start')

    client = Bot30Client(bot30.BOT_USER, bot30.BOT_SERVER_NAME)
    logger.info('%s', client)
    try:
        await asyncio.wait_for(update_mapcycle(client), timeout=30)
    except Exception as exc:
        logger.exception(exc)
        raise
    finally:
        await asyncio.wait_for(client.close(), timeout=10)

    await asyncio.sleep(0.5)
    logger.info('Map Cycle Updater End')


if __name__ == '__main__':
    asyncio.run(async_main())
