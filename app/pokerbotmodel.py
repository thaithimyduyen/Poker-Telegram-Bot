#!/usr/bin/env python3

from app.entities import (
    GameState,
    Game,
    Player,
)


KEY_CHAT_DATA_GAME = "game"
MAX_PLAYERS = 8
MIN_PLAYERS = 2


class PokerBotModel:
    def __init__(self, view, bot):
        self._view = view
        self._bot = bot

    def _game_from_context(self, context) -> Game:
        if KEY_CHAT_DATA_GAME not in context.chat_data:
            context.chat_data[KEY_CHAT_DATA_GAME] = Game()
        return context.chat_data[KEY_CHAT_DATA_GAME]

    def ready(self, update, context):
        game = self._game_from_context(context)

        if game.state != GameState.initial:
            self._view.send_message_reply(
                chat_id=update.effective_message.chat_id,
                message_id=update.effective_message.message_id,
                text="The game is already started. Wait!"
            )
            return

        if len(game.players) > MAX_PLAYERS:
            self._view.send_message_reply(
                chat_id=update.effective_message.chat_id,
                text="The room is full",
                message_id=update.effective_message.message_id,
            )
            return
        username = update.effective_message.from_user.username
        user_id = update.effective_message.from_user.id

        game.players[user_id] = Player(
            user_id=user_id,
            username=username
        )

        self._view.send_message(
            chat_id=update.effective_message.chat_id,
            text=f"`@{username}` is ready"
        )

    def start(self, update, context):
        game = self._game_from_context(context)

        has_access = self._check_access(
            chat_id=update.effective_message.chat_id,
            user_id=update.effective_message.from_user.id,
        )
        if not has_access:
            self._view.send_message_reply(
                chat_id=update.effective_message.chat_id,
                text="👾 *Denied!* 👾",
                message_id=update.effective_message.message_id,
            )
            return

        if len(game.players) < MIN_PLAYERS:
            self._view.send_message_reply(
                chat_id=update.effective_message.chat_id,
                text="Not enough player",
                message_id=update.effective_message.message_id,
            )
            return

        self._view.send_message(
            chat_id=update.effective_message.chat_id,
            text="*Game is created!!*"
        )

    def _check_access(self, chat_id, user_id):
        chat_admins = self._bot.get_chat_administrators(chat_id)
        for m in chat_admins:
            if m.user.id == user_id:
                return True
        return False
