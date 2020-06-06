#!/usr/bin/env python3

import sys
from signal import signal, SIGINT

from app.pokerbot import PokerBot

TOKEN_FILE = "./token.txt"


def main() -> None:
    with open(TOKEN_FILE, 'r') as f:
        token = f.read()
    bot = PokerBot(token=token)

    def keyboard_interrupt(signal, frame):
        bot.flush()
        # KeyboardInterrupt sends code 130.
        sys.exit(130)
    signal(SIGINT, keyboard_interrupt)

    try:
        bot.run()
    finally:
        bot.flush()


if __name__ == "__main__":
    main()
