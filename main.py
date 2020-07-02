#!/usr/bin/env python3

from app.pokerbot import PokerBot

TOKEN_FILE = "./token.txt"


def main() -> None:
    with open(TOKEN_FILE, 'r') as f:
        token = f.read()
    bot = PokerBot(token=token)
    bot.run()


if __name__ == "__main__":
    main()
