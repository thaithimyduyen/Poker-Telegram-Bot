#!/usr/bin/env python3

import sys
from signal import signal, SIGINT, SIGTERM

from app.pokerbot import PokerBot

TOKEN_FILE = "./token.txt"


def main() -> None:
    with open(TOKEN_FILE, 'r') as f:
        token = f.read()
    bot = PokerBot(token=token)

    def gracefull_handler(signal, frame):
        bot.flush()
        sys.exit(0)
    signal(SIGINT, gracefull_handler)
    signal(SIGTERM, gracefull_handler)

    try:
        bot.run()
    finally:
        bot.flush()


if __name__ == "__main__":
    main()
