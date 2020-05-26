#!/usr/bin/env python3

from telegram import (
    ParseMode,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup
)
from app.entities import PlayerAction


class PokerBotViewer:
    def __init__(self, bot):
        self._bot = bot

    def send_message(self, chat_id, text):
        self._bot.send_message(
            chat_id=chat_id,
            parse_mode=ParseMode.MARKDOWN,
            text=text,
        )

    def send_message_reply(self, chat_id, message_id, text):
        self._bot.send_message(
            reply_to_message_id=message_id,
            chat_id=chat_id,
            parse_mode=ParseMode.MARKDOWN,
            text=text,
        )

    @staticmethod
    def _get_cards_markup(cards):
        return ReplyKeyboardMarkup(
            keyboard=[cards],
            selective=True,
            resize_keyboard=True,
        )

    @staticmethod
    def _get_turns_markup():
        keyboard = [[
            InlineKeyboardButton(
                text=PlayerAction.check.value,
                callback_data=PlayerAction.check.value
            ),
            InlineKeyboardButton(
                text=PlayerAction.fold.value,
                callback_data=PlayerAction.fold.value
            ),
            InlineKeyboardButton(
                text=PlayerAction.raise_rate.value,
                callback_data=PlayerAction.raise_rate.value
            ),
            InlineKeyboardButton(
                text=PlayerAction.all_in.value,
                callback_data=PlayerAction.all_in.value
            )
        ]]
        return InlineKeyboardMarkup(
            inline_keyboard=keyboard
        )

    def send_cards(self, chat_id, cards, mention_markdown) -> str:
        markup = PokerBotViewer._get_cards_markup(cards)
        self._bot.send_message(
            chat_id=chat_id,
            text="Showing cards to " + mention_markdown,
            reply_markup=markup,
            parse_mode=ParseMode.MARKDOWN
        )

    def extend_with_turn_actions(self, chat_id, text):
        markup = PokerBotViewer._get_turns_markup()
        return self._bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=markup,
            parse_mode=ParseMode.MARKDOWN
        ).message_id
