#!/usr/bin/env python3
from app.cards import CARDS
import enum
import random


class Player:
    def __init__(self, user_id, username):
        self._user_id = user_id
        self._username = username
        self._state = PlayerState.active
        self._cards = []
        self._money = 0


class Game:
    def __init__(self):
        self.state = GameState.initial
        self.cards = random.shuffle(CARDS)
        self.players = {}
        self.current_player_index = 0


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
