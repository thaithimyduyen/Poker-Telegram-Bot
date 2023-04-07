#!/usr/bin/env python3
from functools import partial

from telegram import Update, BotCommand
from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    CallbackContext,
    Updater,
)

from pokerapp.entity.playeraction import PlayerAction
from pokerapp.model.pokerbotmodel import PokerBotModel


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
            ('top_up', 'Top up your balance.', self._top_up),
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

    def _top_up(self, update: Update, context: CallbackContext) -> None:
        self._model.top_up(update, context)

    def _handle_button_clicked(self, update: Update, context: CallbackContext) -> None:
        actions = {
            PlayerAction.CHECK.value: lambda: self._model.call_check(update, context),
            PlayerAction.CALL.value: lambda: self._model.call_check(update, context),
            PlayerAction.FOLD.value: lambda: self._model.fold(update, context),
            PlayerAction.ALL_IN.value: lambda: self._model.all_in(update, context),
            **{
                str(action.value): partial(
                    self._model.raise_rate_bet, update, context, action
                ) for action in [
                    PlayerAction.BET_TEN,
                    PlayerAction.BET_TWENTY_FIVE,
                    PlayerAction.BET_FIFTY,
                    PlayerAction.BET_ONE_HUNDRED,
                    PlayerAction.BET_TWO_HUNDRED_FIFTY,
                    PlayerAction.BET_FIVE_HUNDRED,
                    PlayerAction.BET_ONE_THOUSAND,
                ]
            }
        }

        query_data = update.callback_query.data
        if query_data in actions:
            actions[query_data]()
