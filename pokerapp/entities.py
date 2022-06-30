#!/usr/bin/env python3

from abc import abstractmethod
import enum
import datetime
from typing import Tuple, List
from uuid import uuid4
from pokerapp.cards import get_cards


MessageId = str
ChatId = str
UserId = str
Mention = str
Score = int
Money = int


@abstractmethod
class Wallet:
    @staticmethod
    def _prefix(id: int, suffix: str = ""):
        pass

    def add_daily(self) -> Money:
        pass

    def inc(self, amount: Money = 0) -> None:
        pass

    def inc_authorized_money(self, game_id: str, amount: Money) -> None:
        pass

    def authorized_money(self, game_id: str) -> Money:
        pass

    def authorize(self, game_id: str, amount: Money) -> None:
        pass

    def authorize_all(self, game_id: str) -> Money:
        pass

    def value(self) -> Money:
        pass

    def approve(self, game_id: str) -> None:
        pass


class Player:
    def __init__(
        self,
        user_id: UserId,
        mention_markdown: Mention,
        wallet: Wallet,
        ready_message_id: str,
    ):
        self.user_id = user_id
        self.mention_markdown = mention_markdown
        self.state = PlayerState.ACTIVE
        self.wallet = wallet
        self.cards = []
        self.round_rate = 0
        self.ready_message_id = ready_message_id

    def __repr__(self):
        return "{}({!r})".format(self.__class__.__name__, self.__dict__)


class PlayerState(enum.Enum):
    ACTIVE = 1
    FOLD = 0
    ALL_IN = 10


class Game:
    def __init__(self):
        self.reset()

    def reset(self):
        self.id = str(uuid4())
        self.pot = 0
        self.max_round_rate = 0
        self.state = GameState.INITIAL
        self.players: List[Player] = []
        self.cards_table = []
        self.current_player_index = -1
        self.remain_cards = get_cards()
        self.trading_end_user_id = 0
        self.ready_users = set()
        self.last_turn_time = datetime.datetime.now()

    def players_by(self, states: Tuple[PlayerState]) -> List[Player]:
        return list(filter(lambda p: p.state in states, self.players))

    def __repr__(self):
        return "{}({!r})".format(self.__class__.__name__, self.__dict__)


class GameState(enum.Enum):
    INITIAL = 0
    ROUND_PRE_FLOP = 1  # No cards on the table.
    ROUND_FLOP = 2  # Three cards.
    ROUND_TURN = 3  # Four cards.
    ROUND_RIVER = 4  # Five cards.
    FINISHED = 5  # The end.


class PlayerAction(enum.Enum):
    CHECK = "check"
    CALL = "call"
    FOLD = "fold"
    RAISE_RATE = "raise rate"
    BET = "bet"
    ALL_IN = "all in"
    SMALL = 10
    NORMAL = 25
    BIG = 50


class UserException(Exception):
    pass
