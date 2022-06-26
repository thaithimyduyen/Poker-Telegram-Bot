#!/usr/bin/env python3

import os

from dotenv import load_dotenv

from pokerapp.config import Config
from pokerapp.pokerbot import PokerBot


def main() -> None:
    load_dotenv()
    cfg: Config = Config()

    if cfg.TOKEN == "":
        print("Environment varaible POKERBOT_TOKEN is not set")
        os.exit(1)

    bot = PokerBot(token=cfg.TOKEN, cfg=cfg)
    bot.run()


if __name__ == "__main__":
    main()
