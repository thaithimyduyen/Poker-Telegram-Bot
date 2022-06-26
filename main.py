#!/usr/bin/env python3

import os
from pokerapp.pokerbot import PokerBot

TOKEN = os.getEnv("POKER_TELEGRAM_BOT_TOKEN")


def main() -> None:
    bot = PokerBot(token=TOKEN)
    bot.run()


if __name__ == "__main__":
    main()
