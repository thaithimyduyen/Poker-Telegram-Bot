import logging

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
    bot.run()


if __name__ == "__main__":
    main()
