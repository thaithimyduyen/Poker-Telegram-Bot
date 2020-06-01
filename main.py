#!/usr/bin/env python3

import logging
import sys
from signal import signal, SIGINT

from app.pokerbot import PokerBot

TOKEN_FILE = "./token.txt"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


def main() -> None:
    with open(TOKEN_FILE, 'r') as f:
        token = f.read()
    bot = PokerBot(token=token)

    def keyboard_interrupt(signal, frame):
        bot.flush()
        # KeyboardInterrupt sends code 130.
        sys.exit(130)
    signal(SIGINT, keyboard_interrupt)

    bot.run()


if __name__ == "__main__":
    main()
