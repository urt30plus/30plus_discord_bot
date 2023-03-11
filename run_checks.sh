set -xe

echo "CI is set to [${CI}]"
if [[ $CI != "true" ]]; then
    pre-commit run --all-files
fi

mypy --version
mypy

export BOT_USER=30+Bot#TEST
export BOT_SERVER_NAME=30+ Urban Test
export BOT_TOKEN=sekret
export MAPCYCLE_EMBED_TITLE=Map Cycle
export CHANNEL_NAME_MAPCYCLE=test-mapcycle
export MAPCYCLE_FILE=./tests/data/mapcycle.txt
export CURRENT_MAP_EMBED_TITLE=Current Map

python -V
python -m unittest
