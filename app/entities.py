#!/usr/bin/env python3

import enum
from uuid import uuid4
from collections import defaultdict
from app.cards import get_cards

DEFAULT_MONEY = 1000

MessageId = str
ChatId = str
UserId = str
Mention = str
Score = int
Money = int


class Wallet:
    def __init__(self):
        self.money = Money(DEFAULT_MONEY)
        self.authorized_money = defaultdict(int)


class Player:
    def __init__(
        self,
        user_id: UserId,
        mention_markdown: Mention,
        wallet: Wallet,
    ):
        self.user_id = user_id
        self.mention_markdown = mention_markdown
        self.wallet = wallet
        self.cards = []
        self.round_rate = 0


class Game:
    def __init__(self):
        self.reset()

    def reset(self):
        self.id = str(uuid4())
        self.pot = 0
        self.max_round_rate = 0
        self.state = GameState.initial
        self.active_players = []
        self.cards_table = []
        self.current_player_index = -1
        self.remain_cards = get_cards()
        self.trading_end_user_id = 0
        self.ready_users = set()

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


class PlayerState(enum.Enum):
    ACTIVE = 1
    FOLD = 0
    ALL_IN = 10


class UserException(Exception):
    pass
