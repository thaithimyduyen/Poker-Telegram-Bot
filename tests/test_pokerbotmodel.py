#!/usr/bin/env python3

import unittest
from typing import Tuple

from app.cards import Cards, Card
from app.entities import Money, Player, Game, Wallet
from app.pokerbotmodel import RoundRateModel, WalletManagerModel


HANDS_FILE = "./tests/hands.txt"


def with_cards(p: Player) -> Tuple[Player, Cards]:
    return (p, [Card("6♥"), Card("A♥"), Card("A♣"), Card("A♠")])


class TestRoundRateModel(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestRoundRateModel, self).__init__(*args, **kwargs)
        self._user_id = 0
        self._wallet_manager = WalletManagerModel()
        self._round_rate = RoundRateModel(self._wallet_manager)

    def _next_player(self, game: Game, autorized: Money) -> Player:
        w = Wallet()
        w.money = autorized
        self._wallet_manager.authorize(game, w, autorized)
        self._user_id += 1
        game.pot += autorized
        return Player(self._user_id, "@test", w)

    def assert_authorized_money_zero(self, *players):
        for (i, p) in enumerate(players):
            authorized = next(iter(p.wallet.authorized_money.values()))
            self.assertEqual(0, authorized, "player[" + str(i) + "]")

    def test_finish_rate_single_winner(self):
        g = Game()
        winner = self._next_player(g, 50)
        loser = self._next_player(g, 50)

        self._round_rate.finish_rate(g, player_scores={
            1: [with_cards(winner)],
            0: [with_cards(loser)],
        })

        self.assertEqual(g.pot, winner.wallet.money)
        self.assertEqual(0, loser.wallet.money)
        self.assert_authorized_money_zero(winner, loser)

    def test_finish_rate_two_winners(self):
        g = Game()
        first_winner = self._next_player(g, 50)
        second_winner = self._next_player(g, 50)
        loser = self._next_player(g, 100)

        self._round_rate.finish_rate(g, player_scores={
            1: [with_cards(first_winner), with_cards(second_winner)],
            0: [with_cards(loser)],
        })

        self.assertEqual(100, first_winner.wallet.money)
        self.assertEqual(100, second_winner.wallet.money)
        self.assertEqual(0, loser.wallet.money)
        self.assert_authorized_money_zero(first_winner, second_winner, loser)

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

        # authorized * len(players)
        self.assertEqual(60, first_winner.wallet.money)
        # authorized * len(players)
        self.assertEqual(20, second_winner.wallet.money)
        # pot - winners
        self.assertEqual(120, extra_winner.wallet.money)

        self.assertEqual(0, loser.wallet.money)

        self.assert_authorized_money_zero(
            first_winner, second_winner, extra_winner, loser,
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

        self.assertEqual(50, first_winner.wallet.money)
        self.assertEqual(100, second_winner.wallet.money)
        self.assertEqual(150, third_winner.wallet.money)
        self.assert_authorized_money_zero(
            first_winner, second_winner, third_winner,
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

        # autorized + losers_money * (autorized / winners_authorized)
        self.assertEqual(4, first_winner.wallet.money)
        self.assertEqual(79, second_winner.wallet.money)

        self.assertEqual(0, third_loser.wallet.money)
        self.assertEqual(0, fourth_loser.wallet.money)

        self.assert_authorized_money_zero(
            first_winner, second_winner, third_loser, fourth_loser
        )


if __name__ == '__main__':
    unittest.main()
