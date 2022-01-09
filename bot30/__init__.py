import datetime
import logging.config
import os

import dotenv

dotenv.load_dotenv()

LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

BOT_USER = os.environ['BOT_USER']
BOT_SERVER_NAME = os.environ['BOT_SERVER_NAME']
BOT_TOKEN = os.environ['BOT_TOKEN']

# Max time in secs to allow this process to run
BOT_MAX_RUN_TIME = int(os.getenv('BOT_MAX_RUN_TIME', '60'))

CHANNEL_NAME_MAPCYCLE = os.environ['CHANNEL_NAME_MAPCYCLE']
MAPCYCLE_FILE = os.environ['MAPCYCLE_FILE']

GAME_SERVER_IP = os.getenv('GAME_SERVER_IP', '127.0.0.1')
GAME_SERVER_PORT = int(os.getenv('GAME_SERVER_PORT', '27960'))
GAME_SERVER_RCON_PASS = os.getenv('GAME_SERVER_RCON_PASS')

# Delay in fractional seconds between updates when there are players online
CURRENT_MAP_UPDATE_DELAY = float(os.getenv('CURRENT_MAP_UPDATE_DELAY', '5.0'))

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        },
    },
    'handlers': {
        'default': {
            'level': LOG_LEVEL,
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
        },
    },
    'loggers': {
        '': {
            'handlers': ['default'],
            'level': 'WARNING',
            'propagate': False,
        },
        'bot30': {
            'handlers': ['default'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        '__main__': {  # if __name__ == '__main__'
            'handlers': ['default'],
            'level': 'DEBUG',
            'propagate': False,
        },
    }
}

logging.config.dictConfig(LOGGING_CONFIG)


def utc_now_str(secs: bool = False) -> str:
    utc_now = datetime.datetime.now(tz=datetime.timezone.utc)
    if secs:
        fmt = '%Y-%m-%d %H:%M:%S %Z'
    else:
        fmt = '%Y-%m-%d %H:%M %Z'
    return utc_now.strftime(fmt)
