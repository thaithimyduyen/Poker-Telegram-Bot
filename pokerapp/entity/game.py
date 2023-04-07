import datetime
from typing import List, Tuple
from uuid import uuid4

from pokerapp.entity.cards import get_cards
from pokerapp.entity.gamestate import GameState
from pokerapp.entity.player import Player
from pokerapp.entity.playerbet import PlayerBet
from pokerapp.entity.playerstate import PlayerState


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
        self.players_bets: List[PlayerBet] = []

    def players_by(self, states: Tuple[PlayerState]) -> List[Player]:
        return list(filter(lambda p: p.state in states, self.players))

    def __repr__(self):
        return "{}({!r})".format(self.__class__.__name__, self.__dict__)
