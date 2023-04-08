import unittest
from typing import Tuple
from unittest.mock import MagicMock

import redis

from pokerapp.config import Config
from pokerapp.entity.cards import Card, Cards
from pokerapp.entity.entities import Money
from pokerapp.entity.game import Game
from pokerapp.entity.player import Player
from pokerapp.entity.playeraction import PlayerAction
from pokerapp.entity.wallet import Wallet
from pokerapp.model.roundratemodel import RoundRateModel
from pokerapp.model.walletmanagermodel import WalletManagerModel


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

    @staticmethod
    def _approve_all(game: Game) -> None:
        for player in game.players:
            player.wallet.approve(game.id)

    @staticmethod
    def _create_player(user_id: str) -> Player:
        player: Player = MagicMock(spec=Player)
        player.user_id = user_id
        player.wallet = MagicMock(spec=Wallet)
        player.bet_amount = 0
        player.wallet.authorize = lambda game_id, amount: setattr(player, 'bet_amount', player.bet_amount + amount)
        player.round_rate = 0
        return player

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

    def test_round_pre_flop_rate_before_first_turn(self):
        g = Game()
        player_one = self._create_player('1')
        player_two = self._create_player('2')
        player_three = self._create_player('3')
        g.players = [
            player_one,
            player_two,
            player_three,
        ]

        self.assertEqual(0, player_one.bet_amount)
        self.assertEqual(0, player_two.bet_amount)
        self.assertEqual(0, player_three.bet_amount)

        self._round_rate.round_pre_flop_rate_before_first_turn(g)

        self.assertEqual(PlayerAction.BIG_BLIND.value / 2, player_one.bet_amount)
        self.assertEqual(PlayerAction.BIG_BLIND.value, player_two.bet_amount)
        self.assertEqual(0, player_three.bet_amount)

    def test_raise_rate_bet__preflop_raise_from_small_bling(self):
        g = Game()
        player_one = self._create_player('1')
        player_two = self._create_player('2')
        player_three = self._create_player('3')
        g.players = [
            player_one,
            player_two,
            player_three,
        ]

        self.assertEqual(0, player_one.bet_amount)
        self.assertEqual(0, player_two.bet_amount)
        self.assertEqual(0, player_three.bet_amount)

        self._round_rate.round_pre_flop_rate_before_first_turn(g)

        self.assertEqual(PlayerAction.BIG_BLIND.value / 2, player_one.bet_amount)
        self.assertEqual(PlayerAction.BIG_BLIND.value, player_two.bet_amount)
        self.assertEqual(0, player_three.bet_amount)

        raise_amount = 10
        self._round_rate.raise_rate_bet(g, player_one, raise_amount)
        self.assertEqual(PlayerAction.BIG_BLIND.value + raise_amount, player_one.bet_amount)


if __name__ == '__main__':
    unittest.main()
