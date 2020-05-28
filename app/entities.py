#!/usr/bin/env python3
import enum
import random

from typing import List

from app.cards import CARDS

Cards = List[str]
MessageId = str
ChatId = str
UserId = str
Mention = str


class Player:
    def __init__(self, user_id: UserId, mention_markdown: Mention):
        self.user_id = user_id
        self.mention_markdown = mention_markdown
        self.cards = []
        self.money = 100
        self.round_rate = 0


class Game:
    def __init__(self):
        self.pot = 0
        self.max_round_rate = 0
        self.state = GameState.initial
        self.active_players = []
        self.cards_table = []
        self.current_player_index = -1
        self.remain_cards = CARDS.copy()
        self.trading_end_user_id = 0
        self.ready_players = set()
        random.shuffle(self.remain_cards)


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
    raise_rate = "raise_rate"
    bet = "bet"
    all_in = "all_in"


class UserException(Exception):
    pass
