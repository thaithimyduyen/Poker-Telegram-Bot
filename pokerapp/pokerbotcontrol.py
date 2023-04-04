#!/usr/bin/env python3

from telegram import Update, BotCommand
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

        commands = [
            ('ready', 'Ready to play.', self._handle_ready),
            ('start', 'Start new game.', self._handle_start),
            ('stop', 'Stop current game.', self._handle_stop),
            ('money', 'Show your money.', self._handle_money),
            ('ban', 'Ban user.', self._handle_ban),
            ('cards', 'Show your cards.', self._handle_cards),
        ]

        model._bot.set_my_commands(list(map(lambda e: BotCommand('/' + e[0], e[1]), commands)))

        list(map(lambda e: updater.dispatcher.add_handler(CommandHandler(e[0], e[2])), commands))

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
