#!/usr/bin/env python3
from app.cards import CARDS
import enum
import random


class Player:
    def __init__(self, user_id, mention_markdown):
        self.user_id = user_id
        self.mention_markdown = mention_markdown
        self.state = PlayerState.active
        self.cards = []
        self.money = 100
        self.round_rait = 0


class Game:
    def __init__(self):
        self.bank = 0
        self.max_round_rait = 0
        self.state = GameState.initial
        self.players = {}
        self.current_player_index = -1
        self.cards_table = []
        self.remain_cards = CARDS.copy()
        random.shuffle(self.remain_cards)


class GameState(enum.Enum):
    initial = 0
    round_pre_flop = 1  # No cards on the table.
    round_flop = 2  # Three cards.
    round_turn = 3  # Four cards.
    round_river = 4  # Five cards.
    finished = 5  # The end.


class PlayerState(enum.Enum):
    active = True
    lose = False


class PlayerAction(enum.Enum):
    check = "check"
    fold = "fold"
    raise_rate = "raise_rate"
    all_in = "all_in"
