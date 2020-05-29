#!/usr/bin/env python3

import os

from telegram import Update, Bot
from telegram.ext import Handler, CallbackContext
from app.winnerdetermination import WinnerDetermination
from app.entities import (
    Game,
    GameState,
    Player,
    ChatId,
    UserId,
    UserException,
)
from app.pokerbotview import PokerBotViewer


KEY_CHAT_DATA_GAME = "game"
MAX_PLAYERS = 8
MIN_PLAYERS = 1 if "POKERBOT_DEBUG" in os.environ else 2
SMALL_BLIND = 5
RAISE_RATE = 10


class PokerBotModel:
    def __init__(self, view: PokerBotViewer, bot: Bot):
        self._view = view
        self._bot = bot
        self._round_rate = RoundRateModel()
        self._winner_determine = WinnerDetermination()

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

        if user.id in game.ready_players:
            self._view.send_message_reply(
                chat_id=update.effective_message.chat_id,
                message_id=update.effective_message.message_id,
                text="You has already been ready"
            )
            return

        game.ready_players.add(user.id)

        game.active_players.append(Player(
            user_id=user.id,
            mention_markdown=user.mention_markdown(),
        ))

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

        game.current_player_index = 1
        self._round_rate.round_pre_flop_rate_before_first_turn(game)
        self._process_playing(chat_id=chat_id, game=game)
        self._round_rate.round_pre_flop_rate_after_first_turn(game)

    def _check_access(self, chat_id: ChatId, user_id: UserId) -> bool:
        chat_admins = self._bot.get_chat_administrators(chat_id)
        for m in chat_admins:
            if m.user.id == user_id:
                return True
        return False

    def _divide_cards(self, game: Game, chat_id: ChatId) -> None:
        for player in game.active_players:
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
        return game.active_players[i]

    def _process_playing(self, chat_id: ChatId, game: Game) -> None:
        if len(game.active_players) == 1:
            self._finish(game, chat_id)
            return

        game.current_player_index += 1
        game.current_player_index %= len(game.active_players)

        if self._current_player(game).user_id == game.trading_end_user_id:
            self._round_rate.to_pot(game)
            self._goto_next_round(game, chat_id)
            game.current_player_index = 0

        if game.state == GameState.finished:
            return

        player = self._current_player(game)
        self._view.send_turn_actions(
            chat_id=chat_id,
            game=game,
            player=player,
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
            text="*Cards are added to table:*\n" +
            f"{cards_table}\n" +
            f"*Current_pot:* {game.pot}$"
        )

    def _finish(self, game: Game, chat_id: ChatId) -> None:
        text = "Game is finished with result:\n\n"
        for player in game.active_players:
            player_all_cards = player.cards + game.cards_table
            all_cards_all_players = {
                player: player_all_cards
            }
        print(all_cards_all_players)
        winners = self._winner_determine.determine_winner(
            all_cards_all_players)
        win_hands, win_players = winners
        for win_hand in win_hands:
            player.win_hand = win_hand

        self._round_rate.finish_rate(game, win_players)
        for player in win_players:
            text += (f"{player.mention_markdown}:\n" +
                     f"GET: *{player.win_rate} $*\n" +
                     f"With combination of cards:\n" +
                     f"{player.win_hand}\n\n")
        self._view.send_message(
            chat_id=chat_id,
            text=text
        )
        # TODO: Clear game.

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
            text=f"{self._current_player(game).mention_markdown} folded"
        )

        game.pot += self._current_player(game).round_rate

        del game.active_players[game.current_player_index]
        game.current_player_index -= 1

        self._process_playing(
            chat_id=update.effective_message.chat_id,
            game=game,
        )

    def call_check(
        self,
        update: Update,
        context: CallbackContext,
        action: str
    ) -> None:
        game = self._game_from_context(context)
        chat_id = update.effective_message.chat_id
        player = self._current_player(game)
        self._view.send_message(
            chat_id=chat_id,
            text=f"{self._current_player(game).mention_markdown} {action}"
        )
        try:
            self._round_rate.call_check(game, player)
        except UserException as e:
            self._view.send_message(chat_id=chat_id, text=str(e))
            return

        self._process_playing(
            chat_id=chat_id,
            game=game,
        )

    def raise_rate_bet(
        self,
        update: Update,
        context: CallbackContext,
        action: str
    ) -> None:
        game = self._game_from_context(context)

        chat_id = update.effective_message.chat_id
        self._view.send_message(
            chat_id=chat_id,
            text=f"{self._current_player(game).mention_markdown}" +
            f" {action} {RAISE_RATE} $"
        )

        player = self._current_player(game)

        try:
            self._round_rate.raise_rate_bet(game, player, RAISE_RATE)
        except UserException as e:
            self._view.send_message(chat_id=chat_id, text=str(e))
            return

        self._process_playing(chat_id=chat_id, game=game)

    def all_in(self, update: Update, context: CallbackContext) -> None:
        pass


class RoundRateModel:
    def round_pre_flop_rate_before_first_turn(self, game):
        self.raise_rate_bet(game, game.active_players[0], SMALL_BLIND)
        self.raise_rate_bet(game, game.active_players[1], SMALL_BLIND)

    def round_pre_flop_rate_after_first_turn(self, game):
        dealer = 2 % len(game.active_players)
        game.trading_end_user_id = game.active_players[dealer].user_id

    def raise_rate_bet(self, game: Game, player: Player, amount: int) -> None:
        amount += game.max_round_rate - player.round_rate

        if amount > player.money:
            raise UserException("not enough money")

        player.money -= amount
        player.round_rate += amount

        game.max_round_rate = player.round_rate
        game.trading_end_user_id = player.user_id

    def call_check(self, game, player) -> None:
        amount = game.max_round_rate - player.round_rate

        if amount > player.money:
            raise UserException("not enough money")

        player.money -= amount
        player.round_rate += amount

    def finish_rate(self, game: Game, win_players) -> None:
        for win_player in win_players:
            win_get_rate = game.pot // len(win_players)
            win_player.money += win_get_rate
            win_player.win_rate = win_get_rate

    def to_pot(self, game) -> None:
        for p in game.active_players:
            game.pot += p.round_rate
            p.round_rate = 0
        game.max_round_rate = 0
        game.trading_end_user_id = game.active_players[0].user_id
