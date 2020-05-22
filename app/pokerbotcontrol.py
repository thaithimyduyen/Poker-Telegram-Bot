#!/usr/bin/env python3

from telegram.ext import (
    CommandHandler,
)


class PokerBotCotroller:
    def __init__(self, model, updater):
        self._model = model

        updater.dispatcher.add_handler(
            CommandHandler('ready', self._handle_ready)
        )
        updater.dispatcher.add_handler(
            CommandHandler('start', self._handle_start)
        )

    def _handle_ready(self, update, context):
        self._model.ready(update, context)

    def _handle_start(self, update, context):
        self._model.start(update, context)
