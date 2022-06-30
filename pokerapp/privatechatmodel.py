from types import NoneType
from typing import Union

import redis

from pokerapp.entities import (
    ChatId,
    MessageId,
    UserId,
)


class UserPrivateChatModel:
    def __init__(self, user_id: UserId, kv: redis.Redis):
        self.user_id = user_id
        self._kv = kv

    @property
    def _key(self) -> str:
        return "pokerbot:chats:" + str(self.user_id)

    def get_chat_id(self) -> Union[ChatId, NoneType]:
        return self._kv.get(self._key)

    def set_chat_id(self, chat_id: ChatId) -> None:
        return self._kv.set(self._key, chat_id)

    def delete(self) -> None:
        self._kv.delete(self._key + ":messages")

        return self._kv.delete(self._key)

    def pop_message(self) -> Union[MessageId, NoneType]:
        return self._kv.rpop(self._key+":messages")

    def push_message(self, message_id: MessageId) -> None:
        return self._kv.rpush(self._key+":messages", message_id)
