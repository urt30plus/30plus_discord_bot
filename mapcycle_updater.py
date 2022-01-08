import asyncio
import logging

import aiofiles
import discord

import bot30
from bot30.clients import Bot30Client
from bot30.models import QuakeGameType

logger = logging.getLogger('bot30.mapcycle')

EMBED_MAPCYCLE_TITLE = 'Map Cycle'


def map_mode(map_opts: dict[str, str]) -> str:
    if map_opts.get('mod_gungame', '0') == '1':
        result = QuakeGameType.GUNGAME.name + ' d3mod'
    elif map_opts.get('mod_ctf', '0') == '1':
        result = QuakeGameType.CTF.name + ' d3mod'
    else:
        game_type = map_opts.get('g_gametype', QuakeGameType.CTF.value)
        result = QuakeGameType(game_type).name
    if map_opts.get('g_instagib') == '1':
        result += ' Instagib'

    return '' if result == QuakeGameType.CTF.name else f'({result})'


def parse_mapcycle_lines(lines: list[str]) -> dict[str, dict]:
    result = {}
    map_name = None
    map_config = None
    for line in lines:
        line = line.strip()
        if not line or line.startswith('//'):
            continue
        elif line == '{':
            map_config = result[map_name]
        elif line == '}':
            map_config = None
        elif map_config is None:
            map_name = line
            result[map_name] = {}
        else:
            k, v = line.split(' ', maxsplit=1)
            map_config[k.strip()] = v.strip().strip('"\'')
    return result


async def parse_mapcycle(mapcycle_file: str) -> dict[str, dict]:
    async with aiofiles.open(mapcycle_file, mode='r', encoding='utf-8') as f:
        lines = await f.readlines()
    return parse_mapcycle_lines(lines)


def create_mapcycle_embed(cycle: dict[str, dict]) -> discord.Embed:
    if cycle:
        descr = '```\n' + '\n'.join(
            [f'{k:25} {map_mode(v)}' for k, v in cycle.items()]
        ) + '\n```'
        color = discord.Colour.blue()
    else:
        descr = '*Unable to retrieve map cycle*'
        color = discord.Colour.red()
    embed = discord.Embed(
        title=EMBED_MAPCYCLE_TITLE,
        description=descr,
        colour=color,
    )
    embed.set_footer(
        text=(
            f'\n\nTotal Maps: {len(cycle)}'
            f'\nLast Updated: {bot30.utc_now_str()}'
        )
    )
    return embed


async def create_embed() -> discord.Embed:
    logger.info('Creating map cycle embed from: %s', bot30.MAPCYCLE_FILE)
    try:
        cycle = await parse_mapcycle(bot30.MAPCYCLE_FILE)
    except Exception:
        logger.exception('Failed to parse mapcycle file')
        cycle = {}
    return create_mapcycle_embed(cycle)


def should_update_embed(message: discord.Message, embed: discord.Embed) -> bool:
    current_embed = message.embeds[0]
    return current_embed.description.strip() != embed.description.strip()


async def update_mapcycle(client: Bot30Client) -> None:
    await client.login(bot30.BOT_TOKEN)
    channel_message, embed = await asyncio.gather(
        client.fetch_embed_message(bot30.CHANNEL_NAME_MAPCYCLE,
                                   EMBED_MAPCYCLE_TITLE),
        create_embed(),
    )
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
