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
    initial = 0
    round_pre_flop = 1  # No cards on the table.
    round_flop = 2  # Three cards.
    round_turn = 3  # Four cards.
    round_river = 4  # Five cards.
    finished = 5  # The end.


class PlayerAction(enum.Enum):
    check = "check"
    call = "call"
    fold = "fold"
    raise_rate = "raise rate"
    bet = "bet"
    all_in = "all in"


class UserException(Exception):
    pass
