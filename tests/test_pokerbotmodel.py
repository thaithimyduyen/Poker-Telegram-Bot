#!/usr/bin/env python3

import unittest
from typing import Tuple
from unittest.mock import MagicMock

import redis
from telegram import Bot, Update
from telegram.ext import CallbackContext

from pokerapp.cards import Cards, Card, get_cards
from pokerapp.config import Config
from pokerapp.entities import Money, Player, Game, PlayerBet, GameState, Wallet
from pokerapp.pokerbotmodel import RoundRateModel, WalletManagerModel, PokerBotModel
from pokerapp.pokerbotview import PokerBotViewer

HANDS_FILE = "./tests/hands.txt"


def with_cards(p: Player) -> Tuple[Player, Cards]:
    return (p, [Card("6♥"), Card("A♥"), Card("A♣"), Card("A♠")])


class TestRoundRateModel(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestRoundRateModel, self).__init__(*args, **kwargs)
        self._user_id = 0
        self._round_rate = RoundRateModel()
        cfg: Config = Config()
        self._kv = redis.Redis(
            host=cfg.REDIS_HOST,
            port=cfg.REDIS_PORT,
            db=cfg.REDIS_DB,
            password=cfg.REDIS_PASS if cfg.REDIS_PASS != "" else None
        )

    def _next_player(self, game: Game, autorized: Money) -> Player:
        self._user_id += 1
        wallet_manager = WalletManagerModel(self._user_id, kv=self._kv)
        wallet_manager.authorize_all("clean_wallet_game")
        wallet_manager.inc(autorized)
        wallet_manager.authorize(game.id, autorized)
        game.pot += autorized
        p = Player(
            user_id=self._user_id,
            mention_markdown="@test",
            wallet=wallet_manager,
            ready_message_id="",
        )
        game.players.append(p)

        return p

    def _approve_all(self, game: Game) -> None:
        for player in game.players:
            player.wallet.approve(game.id)

    def assert_authorized_money_zero(self, game_id: str, *players: Player):
        for (i, p) in enumerate(players):
            authorized = p.wallet.authorized_money(game_id=game_id)
            self.assertEqual(0, authorized, "player[" + str(i) + "]")

    def test_finish_rate_single_winner(self):
        g = Game()
        winner = self._next_player(g, 50)
        loser = self._next_player(g, 50)

        self._round_rate.finish_rate(g, player_scores={
            1: [with_cards(winner)],
            0: [with_cards(loser)],
        })
        self._approve_all(g)

        self.assertAlmostEqual(100, winner.wallet.value(), places=1)
        self.assertAlmostEqual(0, loser.wallet.value(), places=1)
        self.assert_authorized_money_zero(g.id, winner, loser)

    def test_finish_rate_two_winners(self):
        g = Game()
        first_winner = self._next_player(g, 50)
        second_winner = self._next_player(g, 50)
        loser = self._next_player(g, 100)

        self._round_rate.finish_rate(g, player_scores={
            1: [with_cards(first_winner), with_cards(second_winner)],
            0: [with_cards(loser)],
        })
        self._approve_all(g)

        self.assertAlmostEqual(100, first_winner.wallet.value(), places=1)
        self.assertAlmostEqual(100, second_winner.wallet.value(), places=1)
        self.assertAlmostEqual(0, loser.wallet.value(), places=1)
        self.assert_authorized_money_zero(
            g.id,
            first_winner,
            second_winner,
            loser,
        )

    def test_finish_rate_all_in_one_extra_winner(self):
        g = Game()
        first_winner = self._next_player(g, 15)  # All in.
        second_winner = self._next_player(g, 5)  # All in.
        extra_winner = self._next_player(g, 90)  # All in.
        loser = self._next_player(g, 90)  # Call.

        self._round_rate.finish_rate(g, player_scores={
            2: [with_cards(first_winner), with_cards(second_winner)],
            1: [with_cards(extra_winner)],
            0: [with_cards(loser)],
        })
        self._approve_all(g)

        # authorized * len(players)
        self.assertAlmostEqual(60, first_winner.wallet.value(), places=1)
        # authorized * len(players)
        self.assertAlmostEqual(20, second_winner.wallet.value(), places=1)
        # pot - winners
        self.assertAlmostEqual(120, extra_winner.wallet.value(), places=1)

        self.assertAlmostEqual(0, loser.wallet.value(), places=1)

        self.assert_authorized_money_zero(
            g.id, first_winner, second_winner, extra_winner, loser,
        )

    def test_finish_rate_all_winners(self):
        g = Game()
        first_winner = self._next_player(g, 50)
        second_winner = self._next_player(g, 100)
        third_winner = self._next_player(g, 150)

        self._round_rate.finish_rate(g, player_scores={
            1: [
                with_cards(first_winner),
                with_cards(second_winner),
                with_cards(third_winner),
            ],
        })
        self._approve_all(g)

        self.assertAlmostEqual(50, first_winner.wallet.value(), places=1)
        self.assertAlmostEqual(
            100, second_winner.wallet.value(), places=1)
        self.assertAlmostEqual(150, third_winner.wallet.value(), places=1)
        self.assert_authorized_money_zero(
            g.id, first_winner, second_winner, third_winner,
        )

    def test_finish_rate_all_in_all(self):
        g = Game()

        first_winner = self._next_player(g, 3)  # All in.
        second_winner = self._next_player(g, 60)  # All in.
        third_loser = self._next_player(g, 10)  # All in.
        fourth_loser = self._next_player(g, 10)  # All in.

        self._round_rate.finish_rate(g, player_scores={
            3: [with_cards(first_winner), with_cards(second_winner)],
            2: [with_cards(third_loser)],
            1: [with_cards(fourth_loser)],
        })
        self._approve_all(g)

        # pot * (autorized / winners_authorized)
        self.assertAlmostEqual(4, first_winner.wallet.value(), places=1)
        self.assertAlmostEqual(79, second_winner.wallet.value(), places=1)

        self.assertAlmostEqual(0, third_loser.wallet.value(), places=1)
        self.assertAlmostEqual(0, fourth_loser.wallet.value(), places=1)

        self.assert_authorized_money_zero(
            g.id, first_winner, second_winner, third_loser, fourth_loser
        )


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
