#!/usr/bin/env python3

import datetime
import traceback
from threading import Timer
from typing import List

from telegram import Message, ReplyKeyboardMarkup, Update, Bot
from telegram.ext import Handler, CallbackContext

from pokerapp.config import Config
from pokerapp.entity.cards import Cards
from pokerapp.entity.entities import (
    ChatId,
    UserId,
    Money,
)
from pokerapp.entity.game import Game
from pokerapp.entity.gamestate import GameState
from pokerapp.entity.player import Player
from pokerapp.entity.playeraction import PlayerAction
from pokerapp.entity.playerbet import PlayerBet
from pokerapp.entity.playerstate import PlayerState
from pokerapp.entity.userexception import UserException
from pokerapp.model.privatechatmodel import UserPrivateChatModel
from pokerapp.model.roundratemodel import RoundRateModel
from pokerapp.model.walletmanagermodel import WalletManagerModel
from pokerapp.model.winnerdetermination import WinnerDetermination
from pokerapp.view.pokerbotview import PokerBotViewer

DICE_MULT = 10
DICE_DELAY_SEC = 5
BONUSES = (5, 20, 40, 80, 160, 320)
DICES = "⚀⚁⚂⚃⚄⚅"

KEY_CHAT_DATA_GAME = "game"
KEY_OLD_PLAYERS = "old_players"
KEY_LAST_TIME_ADD_MONEY = "last_time"
KEY_NOW_TIME_ADD_MONEY = "now_time"

MAX_PLAYERS = 8
MIN_PLAYERS = 2
ONE_DAY = 86400
MAX_TIME_FOR_TURN = datetime.timedelta(minutes=2)
DESCRIPTION_FILE = "assets/description_bot.md"


class PokerBotModel:
    def __init__(
        self,
        view: PokerBotViewer,
        bot: Bot,
        cfg: Config,
        kv,
    ):
        self._view: PokerBotViewer = view
        self._bot: Bot = bot
        self._winner_determine: WinnerDetermination = WinnerDetermination()
        self._kv = kv
        self._cfg: Config = cfg
        self._round_rate: RoundRateModel = RoundRateModel()

        self._readyMessages = {}

    @property
    def _min_players(self):
        if self._cfg.DEBUG:
            return 1

        return MIN_PLAYERS

    @staticmethod
    def _game_from_context(context: CallbackContext) -> Game:
        if KEY_CHAT_DATA_GAME not in context.chat_data:
            context.chat_data[KEY_CHAT_DATA_GAME] = Game()
        return context.chat_data[KEY_CHAT_DATA_GAME]

    @staticmethod
    def _current_turn_player(game: Game) -> Player:
        assert len(game.players) > 0

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
                text=f"You are already ready {update.effective_user.username}. "
                     f"{len(game.players)} player{'s are' if len(game.players) != 1 else ' is'} ready. "
                     f"{'Tap /start to start.' if len(game.players) > 1 else ''}"
            )
            return

        player = Player(
            user_id=user.id,
            mention_markdown=user.mention_markdown(),
            wallet=WalletManagerModel(user.id, self._kv),
            ready_message_id=update.effective_message.message_id,
        )

        if player.wallet.value() < PlayerAction.BIG_BLIND.value:
            return self._view.send_message_reply(
                chat_id=chat_id,
                message_id=update.effective_message.message_id,
                text="You don't have enough money",
            )

        game.ready_users.add(user.id)

        game.players.append(player)

        members_count = self._bot.get_chat_member_count(chat_id)
        players_active = len(game.players)
        # One is the bot.
        if players_active == members_count - 1 and \
                players_active >= self._min_players:
            self._start_game(context=context, game=game, chat_id=chat_id)

        self._view.send_message_reply(
            chat_id=chat_id,
            message_id=update.effective_message.message_id,
            text=f"You are ready now {update.effective_user.username}. "
                 f"{players_active} player{'s are' if players_active != 1 else ' is'} ready. "
                 f"{'Tap /start to start.' if players_active > 1 else ''}"
        )
        return

    def stop(self, user_id: UserId) -> None:
        UserPrivateChatModel(user_id=user_id, kv=self._kv).delete()

    def start(self, update: Update, context: CallbackContext) -> None:
        game = self._game_from_context(context)
        chat_id = update.effective_message.chat_id
        user_id = update.effective_message.from_user.id

        if game.state not in (GameState.INITIAL, GameState.FINISHED):
            self._view.send_message(
                chat_id=chat_id,
                text="The game is already in progress"
            )
            return

        # One is the bot.
        members_count = self._bot.get_chat_member_count(chat_id) - 1
        if members_count == 1:
            with open(DESCRIPTION_FILE, 'r') as f:
                text = f.read()

            chat_id = update.effective_message.chat_id
            self._view.send_message(
                chat_id=chat_id,
                text=text,
            )
            self._view.send_photo(chat_id=chat_id, photo=open("./assets/poker_hand.jpg", 'rb'))

            if update.effective_chat.type == 'private':
                UserPrivateChatModel(user_id=user_id, kv=self._kv) \
                    .set_chat_id(chat_id=chat_id)

            return

        players_active = len(game.players)
        if players_active >= self._min_players:
            self._start_game(context=context, game=game, chat_id=chat_id)
        else:
            self._view.send_message(
                chat_id=chat_id,
                text="Not enough player. Need players /ready to start."
            )
        return

    def _start_game(
        self,
        context: CallbackContext,
        game: Game,
        chat_id: ChatId
    ) -> None:
        print(f"new game: {game.id}, players count: {len(game.players)}")

        self._view.send_message(
            chat_id=chat_id,
            text='The game is started! 🃏',
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[["poker"]],
                resize_keyboard=True,
            ),
        )

        old_players_ids = context.chat_data.get(KEY_OLD_PLAYERS, [])
        old_players_ids = old_players_ids[-1:] + old_players_ids[:-1]

        def index(ln: List, obj) -> int:
            try:
                return ln.index(obj)
            except ValueError:
                return -1

        game.players.sort(key=lambda p: index(old_players_ids, p.user_id))

        game.state = GameState.ROUND_PRE_FLOP
        self._divide_cards(game=game, chat_id=chat_id)

        game.current_player_index = 1
        self._round_rate.round_pre_flop_rate_before_first_turn(game)
        self._process_playing(chat_id=chat_id, game=game)
        self._round_rate.round_pre_flop_rate_after_first_turn(game)

        context.chat_data[KEY_OLD_PLAYERS] = list(
            map(lambda p: p.user_id, game.players),
        )

    def bonus(self, update: Update, context: CallbackContext) -> None:
        wallet = WalletManagerModel(
            update.effective_message.from_user.id, self._kv)
        money = wallet.value()

        chat_id = update.effective_message.chat_id
        message_id = update.effective_message.message_id

        if wallet.has_daily_bonus():
            return self._view.send_message_reply(
                chat_id=chat_id,
                message_id=update.effective_message.message_id,
                text=f"Your money: *{money}$*\n",
            )

        icon: str
        dice_msg: Message
        bonus: Money

        SATURDAY = 5
        if datetime.datetime.today().weekday() == SATURDAY:
            dice_msg = self._view.send_dice_reply(
                chat_id=chat_id,
                message_id=message_id,
                emoji='🎰'
            )
            icon = '🎰'
            bonus = dice_msg.dice.value * 20
        else:
            dice_msg = self._view.send_dice_reply(
                chat_id=chat_id,
                message_id=message_id,
            )
            icon = DICES[dice_msg.dice.value-1]
            bonus = BONUSES[dice_msg.dice.value - 1]

        message_id = dice_msg.message_id
        money = wallet.add_daily(amount=bonus)

        def print_bonus() -> None:
            self._view.send_message_reply(
                chat_id=chat_id,
                message_id=message_id,
                text=f"Bonus: *{bonus}$* {icon}\n" +
                     f"Your money: *{money}$*\n",
            )

        Timer(DICE_DELAY_SEC, print_bonus).start()

    def reset_game(self, update: Update, context: CallbackContext) -> None:
        game = self._game_from_context(context)

        bets: List[PlayerBet] = game.players_bets
        [player.wallet.inc(bet.amount)
         for bet in bets
         for player in game.players
         if player.user_id == bet.user_id]

        game.reset()
        self._view.send_message(
            chat_id=update.effective_message.chat_id,
            text="The game is reset. Press /ready to start again.",
        )

    def send_cards_to_user(
            self,
            update: Update,
            context: CallbackContext,
    ) -> None:
        game = self._game_from_context(context)

        current_player = None
        for player in game.players:
            if player.user_id == update.effective_user.id:
                current_player = player
                break

        if current_player is None or not current_player.cards:
            self._view.send_message(
                chat_id=update.effective_message.chat_id,
                text=f"{update.effective_message.from_user.mention_markdown()}" +
                     (f", you are not in the game."
                      if not game.state == GameState.INITIAL else f", the game is not started.")
            )
            return

        self._view.send_cards(
            chat_id=update.effective_message.chat_id,
            cards=current_player.cards,
            mention_markdown=current_player.mention_markdown,
            ready_message_id=update.effective_message.message_id,
        )

    def _check_access(self, chat_id: ChatId, user_id: UserId) -> bool:
        chat_admins = self._bot.get_chat_administrators(chat_id)
        for m in chat_admins:
            if m.user.id == user_id:
                return True
        return False

    def _send_cards_private(self, player: Player, cards: Cards) -> None:
        user_chat_model = UserPrivateChatModel(
            user_id=player.user_id,
            kv=self._kv,
        )
        private_chat_id = user_chat_model.get_chat_id()

        if private_chat_id is None:
            raise ValueError("private chat not found")

        private_chat_id = private_chat_id.decode('utf-8')

        message_id = self._view.send_desk_cards_img(
            chat_id=private_chat_id,
            cards=cards,
            caption="Your cards",
            disable_notification=False,
        ).message_id

        try:
            rm_msg_id = user_chat_model.pop_message()
            while rm_msg_id is not None:
                try:
                    rm_msg_id = rm_msg_id.decode('utf-8')
                    self._view.remove_message(
                        chat_id=private_chat_id,
                        message_id=rm_msg_id,
                    )
                except Exception as ex:
                    print("remove_message", ex)
                    traceback.print_exc()
                rm_msg_id = user_chat_model.pop_message()

            user_chat_model.push_message(message_id=message_id)
        except Exception as ex:
            print("bulk_remove_message", ex)
            traceback.print_exc()

    def _divide_cards(self, game: Game, chat_id: ChatId) -> None:
        for player in game.players:
            cards = player.cards = [
                game.remain_cards.pop(),
                game.remain_cards.pop(),
            ]

            try:
                self._send_cards_private(player=player, cards=cards)

                continue
            except Exception as ex:
                print(ex)
                pass

            self._view.send_cards(
                chat_id=chat_id,
                cards=cards,
                mention_markdown=player.mention_markdown,
                ready_message_id=player.ready_message_id,
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

        current_player_money = current_player.wallet.value()

        # Player do not have money so make it ALL_IN.
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

        game.last_turn_time = datetime.datetime.now()
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
            caption=f"Current pot: {game.pot}$",
        )

    def _finish(
        self,
        game: Game,
        chat_id: ChatId,
    ) -> None:
        self._round_rate.to_pot(game)

        print(
            f"game finished: {game.id}, " +
            f"players count: {len(game.players)}, " +
            f"pot: {game.pot}"
        )

        active_players: list[Player] = game.players_by(
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
        self._view.send_message(chat_id=chat_id, text=(
            self._create_final_result_text(active_players, game, only_one_player, winners_hand_money)))

        for player in game.players:
            player.wallet.approve(game.id)

        game.reset()

    @staticmethod
    def _create_final_result_text(active_players, game, only_one_player, winners_hand_money):
        text = "Game is finished with result:\n\n"
        for (player, best_hand, money) in winners_hand_money:
            win_hand = " ".join(best_hand)
            text += (
                    f"{player.mention_markdown}:\n" +
                    f"GOT: *{money} $*\n"
            )
            if not only_one_player:
                active_hands = '\n'.join(map(lambda p: f"{p.mention_markdown}: {' '.join(p.cards)}", active_players))

                text += (
                    f"Final table:\n"
                    f"{' '.join(game.cards_table)}\n"
                    f"Winning hand:\n"
                    f"{win_hand}\n\n"
                    f"All revealed hands:\n"
                    f"{active_hands}\n"
                )
        text += "\n/ready to continue"
        return text

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

    def ban_player(self, update: Update, context: CallbackContext) -> None:
        game = self._game_from_context(context)
        chat_id = update.effective_message.chat_id

        if game.state in (GameState.INITIAL, GameState.FINISHED):
            return

        diff = datetime.datetime.now() - game.last_turn_time
        if diff < MAX_TIME_FOR_TURN:
            self._view.send_message(
                chat_id=chat_id,
                text="You can't ban. Max turn time is 2 minutes",
            )
            return

        self._view.send_message(
            chat_id=chat_id,
            text="Time is over!",
        )
        self.fold(update, context)

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

        try:
            amount = game.max_round_rate - player.round_rate
            if player.wallet.value() <= amount:
                return self.all_in(update=update, context=context)

            mention_markdown = self._current_turn_player(game).mention_markdown
            self._view.send_message(
                chat_id=chat_id,
                text=f"{mention_markdown} {action}" if not action == PlayerAction.CALL.value else
                f"{mention_markdown} calls for {amount}$"
            )

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

        try:
            action = PlayerAction.RAISE_RATE
            if player.round_rate == game.max_round_rate:
                action = PlayerAction.BET

            if player.wallet.value() < raise_bet_rate.value:
                return self.all_in(update=update, context=context)

            self._view.send_message(
                chat_id=chat_id,
                text=player.mention_markdown +
                f" {action.value} {raise_bet_rate.value}$"
            )

            self._round_rate.raise_rate_bet(game, player, raise_bet_rate.value)
        except UserException as e:
            self._view.send_message(chat_id=chat_id, text=str(e))
            return

        self._process_playing(chat_id=chat_id, game=game)

    def all_in(self, update: Update, context: CallbackContext) -> None:
        game = self._game_from_context(context)
        chat_id = update.effective_message.chat_id
        player = self._current_turn_player(game)
        mention = player.mention_markdown
        amount = self._round_rate.all_in(game, player)
        self._view.send_message(
            chat_id=chat_id,
            text=f"{mention} {PlayerAction.ALL_IN.value} {amount}$"
        )
        player.state = PlayerState.ALL_IN
        self._process_playing(chat_id=chat_id, game=game)

    def top_up(self, update, context):
        chat_id = update.effective_message.chat_id

        wallet = WalletManagerModel(update.effective_message.from_user.id, self._kv)
        if wallet.value() > 0:
            self._view.send_message_reply(
                chat_id=chat_id,
                message_id=update.effective_message.message_id,
                text="Your wallet is not empty. You can not top up it."
            )
            return

        game = self._game_from_context(context)
        if not game.state == GameState.INITIAL:
            self._view.send_message_reply(
                chat_id=chat_id,
                message_id=update.effective_message.message_id,
                text="Game is in progress. You can not top up your wallet."
            )
            return

        top_up_amount = 1000
        wallet.inc(top_up_amount)
        self._view.send_message_reply(
            chat_id=chat_id,
            message_id=update.effective_message.message_id,
            text=f"Your wallet is topped up with {top_up_amount} $"
        )

    def show_table(self, update, context):
        from pokerapp.utils.draw_poker_table import draw_poker_table

        game = self._game_from_context(context)
        chat_id = update.effective_message.chat_id
        players = game.players
        current_player = self._current_turn_player(game)

        table_image = draw_poker_table(players=players, current_player=current_player)
        self._view.send_photo(chat_id=chat_id, photo=table_image)
