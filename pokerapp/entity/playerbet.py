from pokerapp.entity.entities import UserId, Money
from pokerapp.entity.gamestate import GameState


class PlayerBet:
    def __init__(self, user_id: UserId, amount: Money, game_state: GameState):
        self.user_id = user_id
        self.amount = amount
        self.game_state = game_state
