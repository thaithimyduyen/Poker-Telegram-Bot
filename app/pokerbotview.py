#!/usr/bin/env python3

from telegram import (
    ParseMode,
    InlineKeyboardButton,
    ReplyKeyboardMarkup
)


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
        keyboard = [[
            InlineKeyboardButton(
                text=cards[0],
                callback_data="first card"
            ),
            InlineKeyboardButton(
                text=cards[1],
                callback_data="second card"
            )
        ]]
        return ReplyKeyboardMarkup(
            keyboard=keyboard,
            selective=True,
            resize_keyboard=True,
        )

    def send_message_with_cards(self, chat_id, text, cards):
        markup = PokerBotViewer._get_cards_markup(cards)
        return self._bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=markup,
            parse_mode=ParseMode.MARKDOWN
        ).message_id
