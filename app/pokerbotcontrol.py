#!/usr/bin/env python3

from telegram import Update
from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    CallbackContext,
    Updater,
)

from app.entities import PlayerAction
from app.pokerbotmodel import PokerBotModel


class PokerBotCotroller:
    def __init__(self, model: PokerBotModel, updater: Updater):
        self._model = model

        updater.dispatcher.add_handler(
            CommandHandler('ready', self._handle_ready)
        )
        updater.dispatcher.add_handler(
            CommandHandler('start', self._handle_start)
        )
        updater.dispatcher.add_handler(
            CommandHandler('cards', self._handle_cards)
        )
        updater.dispatcher.add_handler(
            CallbackQueryHandler(
                self._model.middleware_user_turn(
                    self._handle_button_clicked,
                ),
            )
        )

    def _handle_ready(self, update: Update, context: CallbackContext) -> None:
        self._model.ready(update, context)

    def _handle_start(self, update: Update, context: CallbackContext) -> None:
        self._model.start(update, context)

    def _handle_cards(self, update: Update, context: CallbackContext) -> None:
        self._model.send_cards_to_user(update, context)

    def _handle_check(self, update: Update, context: CallbackContext) -> None:
        self._model.check(update, context)

    def _handle_button_clicked(
        self,
        update: Update,
        context: CallbackContext,
    ) -> None:
        query_data = update.callback_query.data
        if query_data == PlayerAction.check.value:
            self._model.call_check(update, context, PlayerAction.check.value)
        elif query_data == PlayerAction.call.value:
            self._model.call_check(update, context, PlayerAction.call.value)
        elif query_data == PlayerAction.fold.value:
            self._model.fold(update, context)
        elif query_data == PlayerAction.raise_rate.value:
            self._model.raise_rate_bet(
                update, context, PlayerAction.raise_rate.value)
        elif query_data == PlayerAction.bet.value:
            self._model.raise_rate_bet(update, context, PlayerAction.bet.value)
        elif query_data == PlayerAction.all_in.value:
            self._model.all_in(update, context)
