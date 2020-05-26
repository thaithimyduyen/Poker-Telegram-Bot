#!/usr/bin/env python3

import os

from telegram import Update, Bot
from telegram.ext import Handler, CallbackContext

from app.entities import Game, GameState, Player, ChatId, UserId
from app.pokerbotview import PokerBotViewer


KEY_CHAT_DATA_GAME = "game"
MAX_PLAYERS = 8
MIN_PLAYERS = 1 if "POKERBOT_DEBUG" in os.environ else 2


class PokerBotModel:
    def __init__(self, view: PokerBotViewer, bot: Bot):
        self._view = view
        self._bot = bot

    def _game_from_context(self, context: CallbackContext) -> Game:
        if KEY_CHAT_DATA_GAME not in context.chat_data:
            context.chat_data[KEY_CHAT_DATA_GAME] = Game()
        return context.chat_data[KEY_CHAT_DATA_GAME]

    def ready(self, update: Update, context: CallbackContext) -> None:
        game = self._game_from_context(context)

        if game.state != GameState.initial:
            self._view.send_message_reply(
                chat_id=update.effective_message.chat_id,
                message_id=update.effective_message.message_id,
                text="The game is already started. Wait!"
            )
            return

        if len(game.active_players) > MAX_PLAYERS:
            self._view.send_message_reply(
                chat_id=update.effective_message.chat_id,
                text="The room is full",
                message_id=update.effective_message.message_id,
            )
            return

        user = update.effective_message.from_user

        game.active_players[user.id] = Player(
            user_id=user.id,
            mention_markdown=user.mention_markdown(),
        )

        self._view.send_message(
            chat_id=update.effective_message.chat_id,
            text=f"{user.mention_markdown()} is ready"
        )

    def start(self, update: Update, context: CallbackContext) -> None:
        game = self._game_from_context(context)

        chat_id = update.effective_message.chat_id
        message_id = update.effective_message.message_id
        has_access = self._check_access(
            chat_id=chat_id,
            user_id=update.effective_message.from_user.id,
        )
        if not has_access:
            self._view.send_message_reply(
                chat_id=chat_id,
                text="👾 *Denied!* 👾",
                message_id=message_id,
            )
            return

        if len(game.active_players) < MIN_PLAYERS:
            self._view.send_message_reply(
                chat_id=chat_id,
                text="Not enough players",
                message_id=message_id,
            )
            return

        game.state = GameState.round_pre_flop
        self._divide_cards(game=game, chat_id=chat_id,)

        self._view.send_message(chat_id=chat_id, text="*Game is created!!*")
        self._process_playing(chat_id=chat_id, game=game)

    def _check_access(self, chat_id: ChatId, user_id: UserId) -> bool:
        chat_admins = self._bot.get_chat_administrators(chat_id)
        for m in chat_admins:
            if m.user.id == user_id:
                return True
        return False

    def _divide_cards(self, game: Game, chat_id: ChatId) -> None:
        for player in game.active_players.values():
            cards = player.cards = [
                game.remain_cards.pop(),
                game.remain_cards.pop(),
            ]
            self._view.send_cards(
                chat_id=chat_id,
                cards=cards,
                mention_markdown=player.mention_markdown,
            )

    def _current_player(self, game: Game) -> Player:
        i = game.current_player_index % len(game.active_players)
        return list(game.active_players.values())[i]

    def _process_playing(self, chat_id: ChatId, game: Game) -> None:
        if len(game.active_players) == 1:
            self._finish(game, chat_id)
            return

        if game.current_player_index == len(game.active_players) - 1:
            self._goto_next_round(game, chat_id)

        if game.state == GameState.finished:
            return

        game.current_player_index += 1
        game.current_player_index %= len(game.active_players)

        current_player = self._current_player(game)
        self._view.send_turn_actions(
            chat_id=chat_id,
            game=game,
            player=current_player,
        )

    def add_cards_to_table(
        self,
        count: int,
        game: Game,
        chat_id: ChatId,
    ) -> None:
        for _ in range(count):
            game.cards_table.append(game.remain_cards.pop())

        cards_table = " ".join(game.cards_table)
        self._view.send_message(
            chat_id=chat_id,
            text=f"Cards are added to table: {cards_table}"
        )

    def _finish(self, game: Game, chat_id: ChatId) -> None:
        self._view.send_message(
            chat_id=chat_id,
            text=f"Finished"
        )

    def _goto_next_round(self, game: Game, chat_id: ChatId) -> bool:
        def add_cards(cards_count):
            return self.add_cards_to_table(
                count=cards_count,
                game=game,
                chat_id=chat_id
            )

        state_transitions = {
            GameState.round_pre_flop: {
                "next_state": GameState.round_flop,
                "processor": lambda: add_cards(3),
            },
            GameState.round_flop: {
                "next_state": GameState.round_turn,
                "processor": lambda: add_cards(1),
            },
            GameState.round_turn: {
                "next_state": GameState.round_river,
                "processor": lambda: add_cards(1),
            },
            GameState.round_river: {
                "next_state": GameState.finished,
                "processor": lambda: self._finish(game, chat_id),
            }
        }

        if game.state not in state_transitions:
            raise Exception("unexpected state: " + game.state.value)

        transation = state_transitions[game.state]
        game.state = transation["next_state"]
        transation["processor"]()

    def middleware_user_turn(self, fn: Handler) -> Handler:
        def m(update, context):
            game = self._game_from_context(context)
            current_player = self._current_player(game)
            current_user_id = update.callback_query.from_user.id
            if current_user_id != current_player.user_id:
                return

            fn(update, context)

        return m

    def fold(self, update: Update, context: CallbackContext) -> None:
        game = self._game_from_context(context)
        self._view.send_message(
            chat_id=update.effective_message.chat_id,
            text=f"{self._current_player(game).mention_markdown} was folded"
        )
        player_id = update.callback_query.from_user.id
        game.bank += game.active_players[player_id].round_rate

        del game.active_players[player_id]
        game.current_player_index -= 1

        self._process_playing(
            chat_id=update.effective_message.chat_id,
            game=game,
        )

    def check(self, update: Update, context: CallbackContext) -> None:
        game = self._game_from_context(context)
        self._view.send_message(
            chat_id=update.effective_message.chat_id,
            text=f"{self._current_player(game).mention_markdown} was checked"
        )

        self._process_playing(
            chat_id=update.effective_message.chat_id,
            game=game,
        )

    def raise_rate(self, update: Update, context: CallbackContext) -> None:
        pass

    def all_in(self, update: Update, context: CallbackContext) -> None:
        pass
