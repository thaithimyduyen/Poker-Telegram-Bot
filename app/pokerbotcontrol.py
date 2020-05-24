#!/usr/bin/env python3

from telegram.ext import (
    CommandHandler,
)


class PokerBotCotroller:
    def __init__(self, model, updater):
        self._model = model

        m = self._model.middleware_user_turn

        updater.dispatcher.add_handler(
            CommandHandler('ready', self._handle_ready)
        )
        updater.dispatcher.add_handler(
            CommandHandler('start', self._handle_start)
        )
        updater.dispatcher.add_handler(
            CommandHandler('check', m(self._handle_check))
        )

    def _handle_ready(self, update, context):
        self._model.ready(update, context)

    def _handle_start(self, update, context):
        self._model.start(update, context)

    def _handle_check(self, update, context):
        self._model.check(update, context)
