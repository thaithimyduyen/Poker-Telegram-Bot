#!/usr/bin/env python3

import unittest
from unittest.mock import MagicMock

from telegram import Bot, Update
from telegram.ext import CallbackContext

from pokerapp.cards import Cards, get_cards
from pokerapp.config import Config
from pokerapp.entities import Player, Game, PlayerBet, GameState, Wallet
from pokerapp.pokerbotmodel import PokerBotModel
from pokerapp.pokerbotview import PokerBotViewer

HANDS_FILE = "./tests/hands.txt"


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

    def test_top_up(self):
        model = self._model

        kv = MagicMock(spec=dict)
        kv.get = lambda key: 0
        kv.topped_up_amount = 0
        kv.incrby = lambda name, amount: setattr(kv, 'topped_up_amount', amount)
        model._kv = kv

        model._game_from_context = lambda a: Game()

        view = MagicMock(spec=PokerBotViewer)
        model._view = view

        view.text = ''
        model._view.send_message_reply = lambda chat_id, message_id, text: setattr(view, 'text', text)

        update = MagicMock(spec=Update)
        context = MagicMock(spec=CallbackContext)

        self.assertEqual('', view.text)

        model.top_up(update, context)

        self.assertEqual(1000, kv.topped_up_amount)
        self.assertEqual('Your wallet is topped up with 1000 $', view.text)

    def test_top_up__should_not_top_up_when_wallet_not_empty(self):
        model = self._model

        kv = MagicMock(spec=dict)
        kv.get = lambda key: 1
        kv.topped_up_amount = 0
        kv.incrby = lambda name, amount: setattr(kv, 'topped_up_amount', amount)
        model._kv = kv

        model._game_from_context = lambda a: Game()

        view = MagicMock(spec=PokerBotViewer)
        model._view = view

        view.text = ''
        model._view.send_message_reply = lambda chat_id, message_id, text: setattr(view, 'text', text)

        update = MagicMock(spec=Update)
        context = MagicMock(spec=CallbackContext)

        self.assertEqual('', view.text)

        model.top_up(update, context)

        self.assertEqual(0, kv.topped_up_amount)
        self.assertEqual('Your wallet is not empty. You can not top up it.', view.text)

    def test_top_up__should_not_top_up_when_game_in_progress(self):
        model = self._model

        kv = MagicMock(spec=dict)
        kv.get = lambda key: 0
        kv.topped_up_amount = 0
        kv.incrby = lambda name, amount: setattr(kv, 'topped_up_amount', amount)
        model._kv = kv

        game = Game()
        game.state = GameState.ROUND_PRE_FLOP

        model._game_from_context = lambda a: game

        view = MagicMock(spec=PokerBotViewer)
        model._view = view

        view.text = ''
        model._view.send_message_reply = lambda chat_id, message_id, text: setattr(view, 'text', text)

        update = MagicMock(spec=Update)
        context = MagicMock(spec=CallbackContext)

        self.assertEqual('', view.text)

        model.top_up(update, context)

        self.assertEqual(0, kv.topped_up_amount)
        self.assertEqual('Game is in progress. You can not top up your wallet.', view.text)

if __name__ == '__main__':
    unittest.main()
