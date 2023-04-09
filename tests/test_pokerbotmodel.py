#!/usr/bin/env python3

import unittest
from unittest.mock import MagicMock

from telegram import Bot, Update
from telegram.ext import CallbackContext

from pokerapp.config import Config
from pokerapp.entity.cards import Cards, get_cards
from pokerapp.entity.game import Game
from pokerapp.entity.gamestate import GameState
from pokerapp.entity.player import Player
from pokerapp.entity.playerbet import PlayerBet
from pokerapp.entity.wallet import Wallet
from pokerapp.model.pokerbotmodel import PokerBotModel
from pokerapp.view.pokerbotview import PokerBotViewer


class TestPokerBotModel(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestPokerBotModel, self).__init__(*args, **kwargs)

        self._model: PokerBotModel = PokerBotModel(MagicMock(spec=PokerBotViewer), MagicMock(spec=Bot),
                                                   MagicMock(spec=Config), None)
        self._view = MagicMock(spec=PokerBotViewer)
        self._view.text = ''
        self._view.send_message_reply = lambda chat_id, message_id, text: setattr(self._view, 'text', text)
        self._view.send_message = lambda chat_id, text, reply_markup=None: setattr(self._view, 'text', text)
        self._model._view = self._view

        self._kv = MagicMock(spec=dict)
        self._kv.get = lambda key: 0
        self._kv.inc_amount = 0
        self._kv.incrby = lambda name, amount: setattr(self._kv, 'inc_amount', amount)
        self._model._kv = self._kv

        self._cfg = MagicMock(spec=Config)
        self._cfg.DEBUG = False
        self._model._cfg = self._cfg

    @staticmethod
    def _create_player(user_id: str, cards: []) -> Player:
        player: Player = Player(user_id, user_id, MagicMock(spec=Wallet), '0')
        player.user_id = user_id
        player.test_amount = 0
        player.wallet.inc = lambda amount: setattr(player, 'test_amount', player.test_amount + amount)
        player.cards = cards
        player.mention_markdown = user_id
        return player

    def test_reset_game(self):
        game: Game = Game()

        player_one: Player = self._create_player('1', [])
        player_two: Player = self._create_player('2', [])
        player_three: Player = self._create_player('3', [])
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
        cards: Cards = get_cards()
        cards.sort(key=lambda card: (card.rank, card.suit), reverse=True)

        player_one: Player = self._create_player("Player 1", [cards.pop(), cards.pop()])

        player_two: Player = self._create_player("Player 2", [cards.pop(), cards.pop()])

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

        model._game_from_context = lambda a: Game()

        update = MagicMock(spec=Update)
        context = MagicMock(spec=CallbackContext)

        self.assertEqual('', model._view.text)

        model.top_up(update, context)

        self.assertEqual(1000, model._kv.inc_amount)
        self.assertEqual('Your wallet is topped up with 1000 $', model._view.text)

    def test_top_up__should_not_top_up_when_wallet_not_empty(self):
        model = self._model

        model._kv.get = lambda key: 1

        model._game_from_context = lambda a: Game()

        view = MagicMock(spec=PokerBotViewer)
        model._view = view

        view.text = ''
        model._view.send_message_reply = lambda chat_id, message_id, text: setattr(view, 'text', text)

        update = MagicMock(spec=Update)
        context = MagicMock(spec=CallbackContext)

        self.assertEqual('', view.text)

        model.top_up(update, context)

        self.assertEqual(0, model._kv.inc_amount)
        self.assertEqual('Your wallet is not empty. You can not top up it.', view.text)

    def test_top_up__should_not_top_up_when_game_in_progress(self):
        model = self._model

        game = Game()
        game.state = GameState.ROUND_PRE_FLOP

        model._game_from_context = lambda a: game

        update = MagicMock(spec=Update)
        context = MagicMock(spec=CallbackContext)

        view = model._view
        self.assertEqual('', view.text)

        model.top_up(update, context)

        self.assertEqual(0, model._kv.inc_amount)
        self.assertEqual('Game is in progress. You can not top up your wallet.', view.text)

    def test_ready(self):
        model = self._model

        model._kv.get = lambda key: 1000

        game = Game()
        game.state = GameState.INITIAL

        model._game_from_context = lambda context: game

        update = MagicMock(spec=Update)
        update.effective_message.from_user.id = '1'

        self.assertEqual(model._view.text, '')
        self.assertEqual(len(game.ready_users), 0)
        self.assertEqual(len(game.players), 0)

        model.ready(update, MagicMock(spec=CallbackContext))

        self.assertTrue(model._view.text.startswith('You are ready now'),
                        f"Actual text: {model._view.text}")

        self.assertEqual(len(game.ready_users), 1)
        self.assertEqual(game.ready_users.copy().pop(), '1')
        self.assertEqual(len(game.players), 1)

    def test_start(self):
        model = self._model

        game = Game()
        model._game_from_context = lambda context: game

        game.state = GameState.INITIAL

        player_one = self._create_player('1', [])
        player_one.wallet.value = lambda: 1000

        player_two = self._create_player('2', [])
        player_two.wallet.value = lambda: 1000

        game.players = [player_one, player_two]

        model._bot.get_chat_member_count = lambda chat_id: 3

        context = MagicMock(spec=CallbackContext)
        context.chat_data.get = lambda key, arr: []

        self.assertEqual(model._view.text, '')

        model._round_rate.finish_rate = lambda game, player_scores: 15

        model.start(MagicMock(spec=Update), context)

        self.assertEqual(model._view.text, 'The game is started! 🃏')

if __name__ == '__main__':
    unittest.main()
