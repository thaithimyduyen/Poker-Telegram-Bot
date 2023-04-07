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


class PokerBotController:
    def __init__(self, model: PokerBotModel, updater: Updater):
        self._model = model

        commands = [
            ('ready', 'Ready to play.', self._handle_ready),
            ('start', 'Start new game.', self._handle_start),
            ('stop', 'Stop current game.', self._handle_stop),
            ('money', 'Show your money.', self._handle_money),
            ('ban', 'Ban user.', self._handle_ban),
            ('cards', 'Show your cards.', self._handle_cards),
            ('reset_game', 'Reset game and refund players', self._reset_game),
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

    def _reset_game(self, update: Update, context: CallbackContext) -> None:
        self._model.reset_game(update, context)

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
        elif query_data == str(PlayerAction.BET_TEN.value):
            self._model.raise_rate_bet(
                update, context, PlayerAction.BET_TEN
            )
        elif query_data == str(PlayerAction.BET_TWENTY_FIVE.value):
            self._model.raise_rate_bet(
                update, context, PlayerAction.BET_TWENTY_FIVE
            )
        elif query_data == str(PlayerAction.BET_FIFTY.value):
            self._model.raise_rate_bet(update, context, PlayerAction.BET_FIFTY)
        elif query_data == str(PlayerAction.BET_ONE_HUNDRED.value):
            self._model.raise_rate_bet(update, context, PlayerAction.BET_ONE_HUNDRED)
        elif query_data == str(PlayerAction.BET_TWO_HUNDRED_FIFTY.value):
            self._model.raise_rate_bet(update, context, PlayerAction.BET_TWO_HUNDRED_FIFTY)
        elif query_data == str(PlayerAction.BET_FIVE_HUNDRED.value):
            self._model.raise_rate_bet(update, context, PlayerAction.BET_FIVE_HUNDRED)
        elif query_data == str(PlayerAction.BET_ONE_THOUSAND.value):
            self._model.raise_rate_bet(update, context, PlayerAction.BET_ONE_THOUSAND)
        elif query_data == PlayerAction.ALL_IN.value:
            self._model.all_in(update, context)
