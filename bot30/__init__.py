import logging
import os
import sys

import dotenv

dotenv.load_dotenv()

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_LEVEL_ASYNC_DGRAM = os.getenv("LOG_LEVEL_ASYNC_DGRAM", "ERROR")
LOG_LEVEL_DISCORD = os.getenv("LOG_LEVEL_DISCORD", "ERROR")

BOT_USER = os.environ["BOT_USER"]
BOT_SERVER_NAME = os.environ["BOT_SERVER_NAME"]
BOT_TOKEN = os.environ["BOT_TOKEN"]

# Max time in secs to allow this process to run
BOT_MAX_RUN_TIME = int(os.getenv("BOT_MAX_RUN_TIME", "60"))

MAPCYCLE_EMBED_TITLE = os.environ["MAPCYCLE_EMBED_TITLE"]
CHANNEL_NAME_MAPCYCLE = os.environ["CHANNEL_NAME_MAPCYCLE"]
MAPCYCLE_FILE = os.environ["MAPCYCLE_FILE"]

GAME_SERVER_IP = os.getenv("GAME_SERVER_IP", "127.0.0.1")
GAME_SERVER_PORT = int(os.getenv("GAME_SERVER_PORT", "27960"))
GAME_SERVER_RCON_PASS = os.getenv("GAME_SERVER_RCON_PASS")

CURRENT_MAP_EMBED_TITLE = os.environ["CURRENT_MAP_EMBED_TITLE"]
# Delay in fractional seconds between updates when there are players online
CURRENT_MAP_UPDATE_DELAY = float(os.getenv("CURRENT_MAP_UPDATE_DELAY", "5.0"))

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logging.getLogger("bot30").setLevel(LOG_LEVEL)
logging.getLogger("asyncio_dgram").setLevel(LOG_LEVEL_ASYNC_DGRAM)
logging.getLogger("discord").setLevel(LOG_LEVEL_DISCORD)
