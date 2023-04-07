#!/usr/bin/env python3

import unittest
from typing import Tuple
from unittest.mock import MagicMock

from telegram import Bot, Update
from telegram.ext import CallbackContext

from pokerapp.cards import Cards, Card, get_cards
from pokerapp.config import Config
from pokerapp.entities import Player, Game, PlayerBet, GameState, Wallet
from pokerapp.pokerbotmodel import PokerBotModel
from pokerapp.pokerbotview import PokerBotViewer

HANDS_FILE = "./tests/hands.txt"


def with_cards(p: Player) -> Tuple[Player, Cards]:
    return (p, [Card("6♥"), Card("A♥"), Card("A♣"), Card("A♠")])


class TestPokerBotModel(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestPokerBotModel, self).__init__(*args, **kwargs)

        self._model = PokerBotModel(MagicMock(spec=PokerBotViewer), MagicMock(spec=Bot), MagicMock(spec=Config), None)

    def test_reset_game(self):
        game: Game = Game()

        def create_player(user_id: str) -> Player:
            player: Player = MagicMock(spec=Player)
            player.user_id = user_id
            player.wallet = MagicMock(spec=Wallet)
            player.test_amount = 0
            player.wallet.inc = lambda amount: setattr(player, 'test_amount', player.test_amount + amount)
            return player

        player_one: Player = create_player('1')
        player_two: Player = create_player('2')
        player_three: Player = create_player('3')
        game.players = [player_one, player_two, player_three]

        game.players_bets = [
            PlayerBet(player_one.user_id, 2, GameState.ROUND_FLOP),
            PlayerBet(player_one.user_id, 4, GameState.ROUND_RIVER),
            PlayerBet(player_three.user_id, 10, GameState.ROUND_RIVER),
        ]
        self._model._game_from_context = lambda a: game

        update = MagicMock(spec=Update)
        context = MagicMock(spec=CallbackContext)

        self.assertEqual(0, player_one.test_amount)
        self.assertEqual(0, player_two.test_amount)
        self.assertEqual(0, player_three.test_amount)
        self._model.reset_game(update, context)
        self.assertEqual(6, player_one.test_amount)
        self.assertEqual(0, player_two.test_amount)
        self.assertEqual(10, player_three.test_amount)

    def test_create_final_result_text(self):
        def create_player(mention_markdown, player_cards) -> Player:
            player = MagicMock(spec=Player)
            player.cards = [player_cards.pop(), player_cards.pop()]
            player.mention_markdown = mention_markdown
            return player

        cards: Cards = get_cards()
        cards.sort(key=lambda card: (card.rank, card.suit), reverse=True)

        player_one: Player = create_player("Player 1", cards)

        player_two: Player = create_player("Player 2", cards)

        game: Game = MagicMock(spec=Game)
        game.cards_table = [cards.pop(), cards.pop(), cards.pop(), cards.pop(), cards.pop()]

        winners_hand_money = [[player_one, player_one.cards, 100]]

        text = self._model._create_final_result_text([player_one, player_two], game, False, winners_hand_money)
        self.assertEqual((
            "Game is finished with result:\n\n"
            f"Player 1:\nGOT: *100 $*\n"
            "Final table:\n"
            "2♠ 2♣ 2♥ 2♦ 3♠\n"
            "Winning hand:\n"
            "10♠ 10♣\n\n"
            "All revealed hands:\n"
            "Player 1: 10♠ 10♣\n"
            "Player 2: 10♥ 10♦\n\n"
            "/ready to continue"
        ), text)


if __name__ == '__main__':
    unittest.main()
