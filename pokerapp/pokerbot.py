#!/usr/bin/env python3

import logging

import redis
from telegram.ext import Updater
from telegram.utils.request import Request

from pokerapp.config import Config
from pokerapp.messagedelaybot import MessageDelayBot
from pokerapp.model.pokerbotmodel import PokerBotModel
from pokerapp.controller.pokerbotcontroller import PokerBotController
from pokerapp.view.pokerbotview import PokerBotViewer

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


class PokerBot:
    def __init__(
        self,
        token: str,
        cfg: Config,
    ):
        req = Request(con_pool_size=8)
        bot = MessageDelayBot(token=token, request=req)
        bot.run_tasks_manager()

        self._updater = Updater(
            bot=bot,
            use_context=True,
        )

        kv = redis.Redis(
            host=cfg.REDIS_HOST,
            port=cfg.REDIS_PORT,
            db=cfg.REDIS_DB,
            password=cfg.REDIS_PASS if cfg.REDIS_PASS != "" else None
        )

        self._view = PokerBotViewer(bot=bot)
        self._model = PokerBotModel(
            view=self._view,
            bot=bot,
            kv=kv,
            cfg=cfg,
        )
        self._controller = PokerBotController(self._model, self._updater)

    def run(self) -> None:
        self._updater.start_polling()


