#!/usr/bin/env python3

from telegram import Update
from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    CallbackContext,
    Updater,
)

from pokerapp.entities import PlayerAction
from pokerapp.pokerbotmodel import PokerBotModel


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
            CommandHandler('stop', self._handle_stop)
        )
        updater.dispatcher.add_handler(
            CommandHandler('money', self._handle_money)
        )
        updater.dispatcher.add_handler(
            CommandHandler('ban', self._handle_ban)
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

    def _handle_stop(self, update: Update, context: CallbackContext) -> None:
        self._model.stop(user_id=update.effective_message.from_user.id)

    def _handle_cards(self, update: Update, context: CallbackContext) -> None:
        self._model.send_cards_to_user(update, context)

    def _handle_ban(self, update: Update, context: CallbackContext) -> None:
        self._model.ban_player(update, context)

    def _handle_check(self, update: Update, context: CallbackContext) -> None:
        self._model.check(update, context)

    def _handle_money(self, update: Update, context: CallbackContext) -> None:
        self._model.bonus(update, context)

    def _handle_button_clicked(
        self,
        update: Update,
        context: CallbackContext,
    ) -> None:
        query_data = update.callback_query.data
        if query_data == PlayerAction.CHECK.value:
            self._model.call_check(update, context)
        elif query_data == PlayerAction.CALL.value:
            self._model.call_check(update, context)
        elif query_data == PlayerAction.FOLD.value:
            self._model.fold(update, context)
        elif query_data == str(PlayerAction.SMALL.value):
            self._model.raise_rate_bet(
                update, context, PlayerAction.SMALL
            )
        elif query_data == str(PlayerAction.NORMAL.value):
            self._model.raise_rate_bet(
                update, context, PlayerAction.NORMAL
            )
        elif query_data == str(PlayerAction.BIG.value):
            self._model.raise_rate_bet(update, context, PlayerAction.BIG)
        elif query_data == PlayerAction.ALL_IN.value:
            self._model.all_in(update, context)
