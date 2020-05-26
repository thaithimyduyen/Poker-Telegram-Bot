#!/usr/bin/env python3

from telegram.ext import (
    CommandHandler, CallbackQueryHandler
)
from app.entities import PlayerAction


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
        updater.dispatcher.add_handler(
            CallbackQueryHandler(self._handle_button_clicked)
        )

    def _handle_ready(self, update, context):
        self._model.ready(update, context)

    def _handle_start(self, update, context):
        self._model.start(update, context)

    def _handle_check(self, update, context):
        self._model.check(update, context)

    def _handle_button_clicked(self, update, context):
        query_data = update.callback_query.data
        if query_data == PlayerAction.check.value:
            self._model.check(update, context)
        elif query_data == PlayerAction.fold.value:
            self._model.fold(update, context)
        elif query_data == PlayerAction.raise_rate.value:
            self._model.raise_rate(update, context)
        elif query_data == PlayerAction.all_in.value:
            self._model.all_in(update, context)
