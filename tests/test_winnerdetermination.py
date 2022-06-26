#!/usr/bin/env python3

import unittest

from typing import Tuple

from pokerapp.cards import Cards, Card
from pokerapp.winnerdetermination import WinnerDetermination


HANDS_FILE = "./tests/hands.txt"


class TestWinnerDetermination(unittest.TestCase):
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
        """
        Test calculation of the best hand
        """

        with open(HANDS_FILE, "r") as f:
            game_lines = f.readlines()

        determinator = WinnerDetermination()
        for ln in game_lines:
            hands = TestWinnerDetermination._parse_hands(ln)
            got_best_hand = determinator._best_hand_score(hands)[0]
            self.assertListEqual(list1=got_best_hand, list2=hands[0])


if __name__ == '__main__':
    unittest.main()
