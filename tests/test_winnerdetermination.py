import unittest

from typing import Tuple

from app.entities import Cards, Card
from app.winnerdetermination import WinnerDetermination


HANDS_FILE = "./tests/hands.txt"


class TestWinnerDetermination(unittest.TestCase):
    def parse_hands(line: str) -> Tuple[Cards]:
        """ The first hand is the best """

        line_toks = line.split()

        first_hand = TestWinnerDetermination.parse_hand(line_toks[0])
        second_hand = TestWinnerDetermination.parse_hand(line_toks[1])

        if line_toks[2] == "2":
            return (second_hand, first_hand)

        return (first_hand, second_hand)

    def parse_hand(hand: str) -> Cards:
        return [Card(c) for c in hand.split("'")]

    def test_determine_best_hand(self):
        """
        Test calculation of the best hand
        """

        with open(HANDS_FILE, "r") as f:
            game_lines = f.readlines()

        determinator = WinnerDetermination()
        for l in game_lines:
            hands = TestWinnerDetermination.parse_hands(l)
            got_best_hand = determinator._determine_best_hand(hands)
            self.assertListEqual(list1=got_best_hand, list2=hands[0])


if __name__ == '__main__':
    unittest.main()
