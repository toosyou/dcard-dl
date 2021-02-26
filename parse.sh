#!/bin/bash

PATH=/mnt/nas/homes/toosyou/.local/bin:$PATH

cd /mnt/nas/homes/toosyou/projects/dcard-dl
timeout 5m pipenv run python3 generate_proxy.py
timeout 15m pipenv run python3 dcard.py -c -t 32 -f data/
find data -mindepth 1 -mtime +2 -type d -exec rm -rv {} +
pipenv run python3 telegram_bot.py >> ./data/telegram.log 2>&1
