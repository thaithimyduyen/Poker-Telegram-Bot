#!/usr/bin/env python3

from signal import signal, SIGINT
from telegram import Bot
from telegram.utils.request import Request
from telegram.ext import Updater, PicklePersistence

from app.pokerbotcontrol import PokerBotCotroller
from app.pokerbotmodel import PokerBotModel
from app.pokerbotview import PokerBotViewer


class PokerBot:
    def __init__(
        self,
        token: str,
        proxy_url: str = "socks5://192.168.31.110:9100",
        state_file: str = "./state.dat"
    ):
        req = Request(proxy_url=proxy_url, con_pool_size=8)
        bot = Bot(token=token, request=req)
        self._persistence = PicklePersistence(state_file)
        self._updater = Updater(
            bot=bot,
            use_context=True,
            persistence=self._persistence,
        )

        self._view = PokerBotViewer(bot=bot)
        self._model = PokerBotModel(
            view=self._view,
            bot=bot,
        )
        self._controller = PokerBotCotroller(self._model, self._updater)

    def run(self) -> None:
        signal(SIGINT, self._persistence.flush)
        self._updater.start_polling()
