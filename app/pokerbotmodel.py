#!/usr/bin/env python3

import os

from typing import List, Tuple, Dict
from threading import Lock
from telegram import Update, Bot
from telegram.ext import Handler, CallbackContext

from app.winnerdetermination import WinnerDetermination
from app.cards import Cards
from app.entities import (
    Game,
    GameState,
    Player,
    ChatId,
    UserId,
    UserException,
    Money,
    Wallet,
    PlayerAction,
    PlayerState,
    Score,
)
from app.pokerbotview import PokerBotViewer


KEY_CHAT_DATA_GAME = "game"
KEY_USER_WALLET = "wallet"
KEY_OLD_PLAYERS = ""

MAX_PLAYERS = 8
MIN_PLAYERS = 1 if "POKERBOT_DEBUG" in os.environ else 2
SMALL_BLIND = 5
MONEY_DAILY = 100


class PokerBotModel:
    def __init__(self, view: PokerBotViewer, bot: Bot):
        self._view = view
        self._bot = bot
        self._wallet_manager = WalletManagerModel()
        self._round_rate = RoundRateModel(self._wallet_manager)
        self._winner_determine = WinnerDetermination()

    @staticmethod
    def _game_from_context(context: CallbackContext) -> Game:
        if KEY_CHAT_DATA_GAME not in context.chat_data:
            context.chat_data[KEY_CHAT_DATA_GAME] = Game()
        return context.chat_data[KEY_CHAT_DATA_GAME]

    @staticmethod
    def _current_turn_player(game: Game) -> Player:
        i = game.current_player_index % len(game.players)
        return game.players[i]

    def ready(self, update: Update, context: CallbackContext) -> None:
        game = self._game_from_context(context)
        chat_id = update.effective_message.chat_id

        if game.state != GameState.INITIAL:
            self._view.send_message_reply(
                chat_id=chat_id,
                message_id=update.effective_message.message_id,
                text="The game is already started. Wait!"
            )
            return

        if len(game.players) > MAX_PLAYERS:
            self._view.send_message_reply(
                chat_id=chat_id,
                text="The room is full",
                message_id=update.effective_message.message_id,
            )
            return

        user = update.effective_message.from_user

        if user.id in game.ready_users:
            self._view.send_message_reply(
                chat_id=chat_id,
                message_id=update.effective_message.message_id,
                text="You has already been ready",
            )
            return

        if KEY_USER_WALLET not in context.user_data:
            context.user_data[KEY_USER_WALLET] = Wallet()

        player = Player(
            user_id=user.id,
            mention_markdown=user.mention_markdown(),
            wallet=context.user_data[KEY_USER_WALLET],
        )

        if self._wallet_manager.value(player.wallet) < 2*SMALL_BLIND:
            return self._view.send_message_reply(
                chat_id=chat_id,
                message_id=update.effective_message.message_id,
                text="You have enough money",
            )

        game.ready_users.add(user.id)

        game.players.append(player)

        members_count = self._bot.get_chat_members_count(chat_id)
        players_active = len(game.players)
        # One is the bot.
        if players_active == members_count - 1 and \
                players_active >= MIN_PLAYERS:
            self._start_game(context=context, game=game, chat_id=chat_id)

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

        if len(game.players) < MIN_PLAYERS:
            self._view.send_message_reply(
                chat_id=chat_id,
                text="Not enough players",
                message_id=message_id,
            )
            return

        self._start_game(context=context, game=game, chat_id=chat_id)

    def _start_game(
        self,
        context: CallbackContext,
        game: Game,
        chat_id: ChatId
    ) -> None:

        old_players_ids = context.chat_data.get(KEY_OLD_PLAYERS, [])
        old_players_ids = old_players_ids[-1:] + old_players_ids[:-1]

        def index(l: List, obj) -> int:
            try:
                return l.index(obj)
            except ValueError:
                return -1

        game.players.sort(key=lambda p: index(old_players_ids, p.user_id))

        game.state = GameState.ROUND_PRE_FLOP
        self._divide_cards(game=game, chat_id=chat_id,)

        game.current_player_index = 1
        self._round_rate.round_pre_flop_rate_before_first_turn(game)
        self._process_playing(chat_id=chat_id, game=game)
        self._round_rate.round_pre_flop_rate_after_first_turn(game)

        context.chat_data[KEY_OLD_PLAYERS] = list(
            map(lambda p: p.user_id, game.players),
        )

    def add_money(self, update: Update, context: CallbackContext) -> None:
        if KEY_USER_WALLET not in context.user_data:
            context.user_data[KEY_USER_WALLET] = Wallet()

        wallet = context.user_data[KEY_USER_WALLET]
        self._wallet_manager.add_daily(wallet)

        money = self._wallet_manager.value(wallet)
        self._view.send_message_reply(
            chat_id=update.effective_message.chat_id,
            message_id=update.effective_message.message_id,
            text=f" Add to your wallet {MONEY_DAILY}$\n" +
            f"Your money: {money}$"
        )

    def send_cards_to_user(
        self,
        update: Update,
        context: CallbackContext,
    ) -> None:
        game = self._game_from_context(context)

        for player in game.players:
            if player.user_id == update.effective_user.id:
                current_player = player
                break

        if current_player is None or not current_player.cards:
            return

        self._view.send_cards(
            chat_id=update.effective_message.chat_id,
            cards=current_player.cards,
            mention_markdown=current_player.mention_markdown,
        )

    def _check_access(self, chat_id: ChatId, user_id: UserId) -> bool:
        chat_admins = self._bot.get_chat_administrators(chat_id)
        for m in chat_admins:
            if m.user.id == user_id:
                return True
        return False

    def _divide_cards(self, game: Game, chat_id: ChatId) -> None:
        for player in game.players:
            cards = player.cards = [
                game.remain_cards.pop(),
                game.remain_cards.pop(),
            ]
            self._view.send_cards(
                chat_id=chat_id,
                cards=cards,
                mention_markdown=player.mention_markdown,
            )

    def _process_playing(self, chat_id: ChatId, game: Game) -> None:
        game.current_player_index += 1
        game.current_player_index %= len(game.players)

        current_player = self._current_turn_player(game)

        # Process next round.
        if current_player.user_id == game.trading_end_user_id:
            self._round_rate.to_pot(game)
            self._goto_next_round(game, chat_id)

            game.current_player_index = 0

        # Game finished.
        if game.state == GameState.INITIAL:
            return

        # Player could be changed.
        current_player = self._current_turn_player(game)

        current_player_money = self._wallet_manager.value(
            current_player.wallet,
        )

        # Player do not have monery so make it ALL_IN.
        if current_player_money <= 0:
            current_player.state = PlayerState.ALL_IN

        # Skip inactive players.
        if current_player.state != PlayerState.ACTIVE:
            self._process_playing(chat_id, game)
            return

        # All fold except one.
        all_in_active_players = game.players_by(
            states=(PlayerState.ACTIVE, PlayerState.ALL_IN)
        )
        if len(all_in_active_players) == 1:
            self._finish(game, chat_id)
            return

        self._view.send_turn_actions(
            chat_id=chat_id,
            game=game,
            player=current_player,
            money=current_player_money,
        )

    def add_cards_to_table(
        self,
        count: int,
        game: Game,
        chat_id: ChatId,
    ) -> None:
        for _ in range(count):
            game.cards_table.append(game.remain_cards.pop())

        self._view.send_desk_cards_img(
            chat_id=chat_id,
            cards=game.cards_table,
            caption=f"*Current pot:* {game.pot}$",
        )

    def _finish(
        self,
        game: Game,
        chat_id: ChatId,
    ) -> None:
        self._round_rate.to_pot(game)

        active_players = game.players_by(
            states=(PlayerState.ACTIVE, PlayerState.ALL_IN)
        )

        player_scores = self._winner_determine.determinate_scores(
            players=active_players,
            cards_table=game.cards_table,
        )

        winners_hand_money = self._round_rate.finish_rate(
            game=game,
            player_scores=player_scores,
        )

        only_one_player = len(active_players) == 1
        text = "Game is finished with result:\n\n"
        for (player, best_hand, money) in winners_hand_money:
            win_hand = " ".join(best_hand)
            text += (
                f"{player.mention_markdown}:\n" +
                f"GOT: *{money} $*\n"
            )
            if not only_one_player:
                text += (
                    f"With combination of cards:\n" +
                    f"{win_hand}\n\n"
                )
        text += "/ready to continue"
        self._view.send_message(chat_id=chat_id, text=text)

        game.reset()

    def _goto_next_round(self, game: Game, chat_id: ChatId) -> bool:
        # The state of the last player becomes ALL_IN at end of the round .
        active_players = game.players_by(
            states=(PlayerState.ACTIVE,)
        )
        if len(active_players) == 1:
            active_players[0].state = PlayerState.ALL_IN
            if len(game.cards_table) == 5:
                self._finish(game, chat_id)
                return

        def add_cards(cards_count):
            return self.add_cards_to_table(
                count=cards_count,
                game=game,
                chat_id=chat_id
            )

        state_transitions = {
            GameState.ROUND_PRE_FLOP: {
                "next_state": GameState.ROUND_FLOP,
                "processor": lambda: add_cards(3),
            },
            GameState.ROUND_FLOP: {
                "next_state": GameState.ROUND_TURN,
                "processor": lambda: add_cards(1),
            },
            GameState.ROUND_TURN: {
                "next_state": GameState.ROUND_RIVER,
                "processor": lambda: add_cards(1),
            },
            GameState.ROUND_RIVER: {
                "next_state": GameState.FINISHED,
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
            if game.state == GameState.INITIAL:
                return

            current_player = self._current_turn_player(game)
            current_user_id = update.callback_query.from_user.id
            if current_user_id != current_player.user_id:
                return

            fn(update, context)
            self._view.remove_markup(
                chat_id=update.effective_message.chat_id,
                message_id=update.effective_message.message_id,
            )

        return m

    def fold(self, update: Update, context: CallbackContext) -> None:
        game = self._game_from_context(context)
        player = self._current_turn_player(game)

        player.state = PlayerState.FOLD

        self._view.send_message(
            chat_id=update.effective_message.chat_id,
            text=f"{player.mention_markdown} {PlayerAction.FOLD.value}"
        )

        self._process_playing(
            chat_id=update.effective_message.chat_id,
            game=game,
        )

    def call_check(
        self,
        update: Update,
        context: CallbackContext,
    ) -> None:
        game = self._game_from_context(context)
        chat_id = update.effective_message.chat_id
        player = self._current_turn_player(game)

        action = PlayerAction.CALL.value
        if player.round_rate == game.max_round_rate:
            action = PlayerAction.CHECK.value

        self._view.send_message(
            chat_id=chat_id,
            text=f"{self._current_turn_player(game).mention_markdown} {action}"
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
        raise_bet_rate: PlayerAction
    ) -> None:
        game = self._game_from_context(context)
        chat_id = update.effective_message.chat_id
        player = self._current_turn_player(game)

        action = PlayerAction.RAISE_RATE
        if player.round_rate == game.max_round_rate:
            action = PlayerAction.BET

        self._view.send_message(
            chat_id=chat_id,
            text=player.mention_markdown +
            f" {action.value} {raise_bet_rate.value}$"
        )

        try:
            self._round_rate.raise_rate_bet(game, player, raise_bet_rate.value)
        except UserException as e:
            self._view.send_message(chat_id=chat_id, text=str(e))
            return

        self._process_playing(chat_id=chat_id, game=game)

    def all_in(self, update: Update, context: CallbackContext) -> None:
        game = self._game_from_context(context)
        chat_id = update.effective_message.chat_id
        player = self._current_turn_player(game)
        amount = self._round_rate.all_in(game, player)
        self._view.send_message(
            chat_id=chat_id,
            text=player.mention_markdown +
            f"{PlayerAction.ALL_IN.value} {amount}$"
        )
        player.state = PlayerState.ALL_IN
        self._process_playing(chat_id=chat_id, game=game)


class WalletManagerModel:
    def __init__(self):
        self._lock = Lock()

    def add_daily(self, wallet: Wallet) -> None:
        self._lock.acquire()
        try:
            wallet.money += MONEY_DAILY
        finally:
            self._lock.release()

    def inc(self, game: Game, wallet: Wallet, amount: Money = 0) -> None:
        """ Increase count of money in the wallet.
            Decrease authorized money.
        """

        self._lock.acquire()
        try:
            if wallet.money + amount < 0:
                raise UserException("not enough money")

            wallet.money += amount

            authorized = wallet.authorized_money[game.id] - amount
            wallet.authorized_money[game.id] = max(0, authorized)
        finally:
            self._lock.release()

    def approve(self, game: Game, wallet: Wallet) -> None:
        """ Approve authorized money. """

        self._lock.acquire()
        try:
            wallet.authorized_money[game.id] = 0
        finally:
            self._lock.release()

    def authorize(self, game: Game, wallet: Wallet, amount: Money) -> None:
        """ Decrease count of money. """

        return self.inc(game, wallet, -amount)

    def authorize_all(self, game: Game, wallet: Wallet) -> Money:
        """ Decrease all money of player. """
        self._lock.acquire()
        try:
            money = wallet.money
            wallet.authorized_money[game.id] += money
            wallet.money = 0
            return money
        finally:
            self._lock.release()

    def value(self, wallet: Wallet) -> Money:
        """ Get count of money in the wallet. """

        self._lock.acquire()
        try:
            return wallet.money
        finally:
            self._lock.release()


class RoundRateModel:
    def __init__(self, wallet_manager: WalletManagerModel):
        self._wallet_manager = wallet_manager

    def round_pre_flop_rate_before_first_turn(self, game: Game) -> None:
        self.raise_rate_bet(game, game.players[0], SMALL_BLIND)
        self.raise_rate_bet(game, game.players[1], SMALL_BLIND)

    def round_pre_flop_rate_after_first_turn(self, game: Game) -> None:
        dealer = 2 % len(game.players)
        game.trading_end_user_id = game.players[dealer].user_id

    def raise_rate_bet(self, game: Game, player: Player, amount: int) -> None:
        amount += game.max_round_rate - player.round_rate

        self._wallet_manager.authorize(
            game=game,
            wallet=player.wallet,
            amount=amount,
        )
        player.round_rate += amount

        game.max_round_rate = player.round_rate
        game.trading_end_user_id = player.user_id

    def call_check(self, game, player) -> None:
        amount = game.max_round_rate - player.round_rate

        self._wallet_manager.authorize(
            game=game,
            wallet=player.wallet,
            amount=amount,
        )
        player.round_rate += amount

    def all_in(self, game, player) -> Money:
        amount = self._wallet_manager.authorize_all(
            game=game,
            wallet=player.wallet,
        )
        player.round_rate += amount
        if game.max_round_rate < player.round_rate:
            game.max_round_rate = player.round_rate
            game.trading_end_user_id = player.user_id
        return amount

    @staticmethod
    def _sum_authorized_money(
        game: Game,
        players: List[Tuple[Player, Cards]],
    ) -> int:
        sum_authorized_money = 0
        for player in players:
            sum_authorized_money += player[0].wallet.authorized_money[game.id]
        return sum_authorized_money

    def finish_rate(
        self,
        game: Game,
        player_scores: Dict[Score, List[Tuple[Player, Cards]]],
    ) -> List[Tuple[Player, Cards, Money]]:
        sorted_player_scores_items = sorted(
            player_scores.items(),
            reverse=True,
            key=lambda x: x[0],
        )
        player_scores_values = list(
            map(lambda x: x[1], sorted_player_scores_items))

        res = []
        for win_players in player_scores_values:
            players_authorized = self._sum_authorized_money(
                game=game,
                players=win_players,
            )
            if players_authorized <= 0:
                continue

            game_pot = game.pot
            for win_player, best_hand in win_players:
                if game.pot <= 0:
                    break

                authorized = win_player.wallet.authorized_money[game.id]

                win_money_real = game_pot * (authorized / players_authorized)
                win_money_real = round(win_money_real)

                win_money_can_get = authorized * len(game.players)
                win_money = min(win_money_real, win_money_can_get)

                self._wallet_manager.inc(
                    game=game,
                    wallet=win_player.wallet,
                    amount=win_money,
                )
                game.pot -= win_money
                res.append((win_player, best_hand, win_money))

        for p in game.players:
            self._wallet_manager.approve(game, p.wallet)

        return res

    def to_pot(self, game) -> None:
        for p in game.players:
            game.pot += p.round_rate
            p.round_rate = 0
        game.max_round_rate = 0
        game.trading_end_user_id = game.players[0].user_id
