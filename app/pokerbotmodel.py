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

        user = update.effective_message.from_user

        game.players[user.id] = Player(
            user_id=user.id,
            mention_markdown=user.mention_markdown(),
        )

        self._view.send_message(
            chat_id=update.effective_message.chat_id,
            text=f"{user.mention_markdown()} is ready"
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

        game.state = GameState.round_pre_flop
        self._divide_card(game)

        self._view.send_message(
            chat_id=update.effective_message.chat_id,
            text="*Game is created!!*"
        )
        self._process_playing(
            chat_id=update.effective_message.chat_id,
            game=game,
        )

    def _check_access(self, chat_id, user_id):
        chat_admins = self._bot.get_chat_administrators(chat_id)
        for m in chat_admins:
            if m.user.id == user_id:
                return True
        return False

    def _divide_card(self, game):
        for player in game.players.values():
            player.cards = [game.cards.pop(), game.cards.pop()]

    def _current_player(self, game):
        return list(game.players.values())[game.current_player_index]

    def _process_playing(self, chat_id, game):
        game.current_player_index += 1
        current_player = self._current_player(game)
        mention_markdown = current_player.mention_markdown
        cards = current_player.cards
        self._view.send_message_with_cards(
            chat_id=chat_id,
            text=f"{mention_markdown} your turn",
            cards=cards,
        )

    def _goto_next_round(self):
        pass

    def _finish(self):
        pass

    def fold(self, update, context):
        pass

    def middleware_user_turn(self, fn):
        def m(update, context):
            game = self._game_from_context(context)
            current_player = self._current_player(game)
            user_id_current = update.effective_message.from_user.id
            if user_id_current != current_player.user_id:
                self._view.send_message_reply(
                    chat_id=update.effective_message.chat_id,
                    text="It's not your turn"
                )
                return

            fn(update, context)

        return m

    def check(self, update, context):
        game = self._game_from_context(context)
        self._view.send_message(
            chat_id=update.effective_message.chat_id,
            text=f"{self._current_player(game).mention_markdown} was checked"
        )

        self._process_playing(
            chat_id=update.effective_message.chat_id,
            game=game,
        )

    def raise_rait(self, update, context):
        pass

    def all_in(self, update, context):
        pass
