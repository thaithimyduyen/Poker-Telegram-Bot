#!/usr/bin/env python3


class PokerBotModel:
    def __init__(self, view, bot):
        self._view = view
        self._bot = bot

    def start(self, update, context):
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
        # game_state = NewGame()
        self._view.send_message(
            chat_id=update.effective_message.chat_id,
            text="*Game is created!!*"
        )

    def _check_access(self, chat_id, user_id):
        chat_members = self._bot.get_chat_administrators(chat_id)
        for m in chat_members:
            if m.user.id == user_id:
                return True
        return False


# class NewGame:
#     def __init__(self, state, players):
#         self._state = state,
#         self._players = players
