#!/usr/bin/env python3

import os
from app.entities import (
    GameState,
    Game,
    Player,
)


KEY_CHAT_DATA_GAME = "game"
MAX_PLAYERS = 8
MIN_PLAYERS = 1 if "POKERBOT_DEBUG" in os.environ else 2


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
        self._divide_cards(
            game=game,
            chat_id=update.effective_message.chat_id,
        )

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

    def _divide_cards(self, game, chat_id):
        for player in game.players.values():
            cards = player.cards = [
                game.remain_cards.pop(),
                game.remain_cards.pop(),
            ]
            self._view.send_cards(
                chat_id=chat_id,
                cards=cards,
                mention_markdown=player.mention_markdown,
            )

    def _current_player(self, game):
        return list(game.players.values())[game.current_player_index]

    def _process_playing(self, chat_id, game):
        players_count = len(game.players)
        game.current_player_index += 1
        if game.current_player_index > (players_count - 1):
            self._goto_next_round(game, chat_id)
            return
        current_player = self._current_player(game)
        mention_markdown = current_player.mention_markdown
        if len(game.cards_table) == 0:
            cards_table = "no cards"
        else:
            cards_table = " ".join(game.cards_table)
        player_money = current_player.money
        bank = game.bank
        self._view.extend_with_turn_actions(
            chat_id=chat_id,
            text=f"{mention_markdown} It is your turn\n" +
            f"Cards on the table: {cards_table}\n" +
            f"Your money: *{player_money}$*\n " +
            f"Bank: *{bank}$*",
        )

    def add_cards_to_table(self, cards_count, game, chat_id):
        for _ in range(cards_count):
            game.cards_table.append(game.remain_cards.pop())

        cards_table = " ".join(game.cards_table)
        self._view.send_message(
            chat_id=chat_id,
            text=f"Cards are added to table: {cards_table}"
        )

    def _finish(self, game, chat_id):
        pass

    def _goto_next_round(self, game, chat_id):
        game.current_player_index = -1
        if len(game.players) == 0:
            self._finish(game, chat_id)

        elif game.state == GameState.round_pre_flop:
            game.state = GameState.round_flop
            self.add_cards_to_table(
                cards_count=3,
                game=game,
                chat_id=chat_id,
            )

        elif game.state == GameState.round_flop:
            game.state = GameState.round_turn
            self.add_cards_to_table(
                cards_count=1,
                game=game,
                chat_id=chat_id,
            )

        elif game.state == GameState.round_turn:
            game.state = GameState.round_river
            self.add_cards_to_table(
                cards_count=1,
                game=game,
                chat_id=chat_id,
            )

        elif game.state == GameState.round_river:
            self._finish(game, chat_id)
            return

        self._process_playing(chat_id, game)

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

    def raise_rate(self, update, context):
        pass

    def all_in(self, update, context):
        pass
