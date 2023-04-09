#!/usr/bin/env python3

import unittest
from typing import Tuple
from unittest.mock import MagicMock

from pokerapp.entity.cards import Cards, Card
from pokerapp.entity.player import Player
from pokerapp.entity.wallet import Wallet
from pokerapp.model.winnerdetermination import WinnerDetermination

HANDS_FILE = "./hands.txt"


class TestWinnerDetermination(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestWinnerDetermination, self).__init__(*args, **kwargs)
        self.determinator = WinnerDetermination()

    @staticmethod
    def _create_player(user_id: str, cards: []) -> Player:
        player: Player = Player(user_id, user_id, MagicMock(spec=Wallet), '0')
        player.user_id = user_id
        player.test_amount = 0
        player.wallet.inc = lambda amount: setattr(player, 'test_amount', player.test_amount + amount)
        player.cards = cards
        return player

    @classmethod
    def _parse_hands(cls, line: str) -> Tuple[Cards]:
        """ The first hand is the best """

        line_toks = line.split()

        first_hand = cls._parse_hand(line_toks[0])
        second_hand = cls._parse_hand(line_toks[1])

        if line_toks[2] == "2":
            return (second_hand, first_hand)

        return (first_hand, second_hand)

    @staticmethod
    def _parse_hand(hand: str) -> Cards:
        return [Card(c) for c in hand.split("'")]

    def test_determine_best_hand(self):
        with open(HANDS_FILE, "r") as f:
            game_lines = f.readlines()

        determinator = self.determinator
        for ln in game_lines:
            hands = TestWinnerDetermination._parse_hands(ln)
            got_best_hand = determinator._best_hand_score(hands)[0]
            self.assertListEqual(list1=got_best_hand, list2=hands[0])

    def test_check_hand_get_score_1(self):
        determinator = self.determinator
        hand = [Card('A♠'), Card('2♦'), Card('4♥'), Card('5♦'), Card('3♦')]
        self.assertEqual(3796880, determinator._check_hand_get_score(hand))

    def test_check_hand_get_score_2(self):
        hand_one = [Card('6♥'), Card('8♥'), Card('J♥'), Card('K♥'), Card('5♥')]
        hand_two = [Card('6♥'), Card('8♥'), Card('J♥'), Card('K♥'), Card('Q♥')]
        self.assertTrue(
            self.determinator._check_hand_get_score(hand_two) > self.determinator._check_hand_get_score(hand_one))

    def test_determinate_scores_1(self):
        determinator = self.determinator

        player_one: Player = self._create_player('1', [Card("K♣"), (Card("A♣"))])
        player_two: Player = self._create_player('2', [(Card("6♦")), (Card("7♦"))])

        cards_table = [(Card("10♦")), (Card("10♥")), (Card("8♣")), (Card("5♠")), (Card("Q♣"))]

        scores = determinator.determinate_scores([player_one, player_two], cards_table)
        self.assertListEqual([(Card("K♣")), (Card("A♣")), (Card("10♦")), (Card("10♥")), (Card("Q♣"))],
                             list(scores[1555857][0][1]))

        self.assertListEqual([(Card("7♦")), (Card("10♦")), (Card("10♥")), (Card("8♣")), (Card("Q♣"))],
                             list(scores[1555327][0][1]))

    def test_determinate_scores_2(self):
        determinator = self.determinator

        player_one: Player = self._create_player('1', [Card("3♠"), (Card("A♠"))])
        player_two: Player = self._create_player('2', [(Card("9♣")), (Card("9♠"))])

        cards_table = [(Card("9♥")), (Card("2♦")), (Card("4♥")), (Card("5♦")), (Card("3♦"))]

        scores = determinator.determinate_scores([player_one, player_two], cards_table)
        self.assertListEqual([(Card("A♠")), (Card("2♦")), (Card("3♠")), (Card("4♥")), (Card("5♦"))],
                             list(scores[3796880][0][1]))

        self.assertListEqual([(Card("9♣")), (Card("9♠")), (Card("9♥")), (Card("4♥")), (Card("5♦"))],
                             list(scores[3039604][0][1]))

if __name__ == '__main__':
    unittest.main()
