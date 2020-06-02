#!/usr/bin/env python3

import telegram.ext.messagequeue as mq
from telegram import Bot
from telegram.utils.request import Request
from telegram.ext import Updater, PicklePersistence

from app.pokerbotcontrol import PokerBotCotroller
from app.pokerbotmodel import PokerBotModel
from app.pokerbotview import PokerBotViewer


class PokerBot:
    def __init__(
        self,
        token: str,
        proxy_url: str = "socks5://127.0.0.1:9050",
        state_file: str = "./state.dat"
    ):
        req = Request(proxy_url=proxy_url, con_pool_size=8)
        msg_queue = mq.MessageQueue(
            all_burst_limit=20,
            all_time_limit_ms=60000,
        )
        bot = MQBot(token=token, request=req, msg_queue=msg_queue)

        self._persistence = PicklePersistence(
            state_file,
            store_bot_data=False,
            store_chat_data=False,
            store_user_data=True,
        )
        self._updater = Updater(
            bot=bot,
            use_context=True,
            persistence=self._persistence,
        )

        self._view = PokerBotViewer(bot=bot)
        self._model = PokerBotModel(
            view=self._view,
            bot=bot,
        )
        self._controller = PokerBotCotroller(self._model, self._updater)

    def flush(self) -> None:
        self._persistence.flush()

    def run(self) -> None:
        self._updater.start_polling()


class MQBot(Bot):
    def __init__(
        self,
        *args,
        is_messages_queued_default=True,
        msg_queue=None,
        **kwargs,
    ):
        super(MQBot, self).__init__(*args, **kwargs)
        self._is_messages_queued_default = is_messages_queued_default
        self._msg_queue = msg_queue or mq.MessageQueue()

    def __del__(self):
        try:
            self._msg_queue.stop()
        except Exception:
            pass

    @mq.queuedmessage
    def send_photo(self, *args, **kwargs):
        return super(MQBot, self).send_photo(*args, **kwargs)

    @mq.queuedmessage
    def send_message(self, *args, **kwargs):
        return super(MQBot, self).send_message(*args, **kwargs)

    @mq.queuedmessage
    def edit_message_reply_markup(self, *args, **kwargs):
        return super(MQBot, self).edit_message_reply_markup(*args, **kwargs)
