#!/usr/bin/env python3

from telegram import ParseMode


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
