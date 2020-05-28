#!/usr/bin/env python3
from itertools import combinations
dict_cards_order = {
    '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7,
    '8': 8, '9': 9, '10': 10, "J": 11, 'Q': 12, 'K': 13, 'A': 14

}
dict_suits = {
    "♥️": "Н",
    "♦️": "D",
    "♣️": "C",
    "♠️": "S",
}


class WinnerDetermination:
    def __init__(self, all_cards_all_player):
        self.all_cards_all_player = all_cards_all_player

    def make_combination(self, cards):
        hands = list(combinations(cards, 5))
        return hands

    def check_hand(self, hand):
        pass

    def determine_best_hand(self, hands):
        best_hand_point = 0
        for hand in hands:
            hand_point = self.check_hand(hand)
            best_hand_point = max(best_hand_point, hand_point)
            hand_point_dict = {
                hand: hand_point
            }
        return best_hand_point

    def determine_winner(self):
        for player, all_card in self.all_cards_all_player.items():
            hands = self.make_combination(all_card)
            best_hand = self.determine_best_hand(hands)
            best_hand_player_dict = {
                player: best_hand
            }

        most_best_hand = self.determine_best_hand(
            best_hand_player_dict.values())
        winner = best_hand_player_dict[most_best_hand]
        return winner

    # A, K, Q, J, 10, all the same suit

    def check_royal_flush(self, hand):
        pass

    # Five cards in a sequence, all in the same suit
    def check_straight_flush(self, hand):
        pass

    # All four cards of the same rank
    def check_four_of_a_kind(self, hand):
        pass

    # Three of a kind with a pair
    def check_full_house(self, hand):
        pass

    # Any five cards of the same suit, but not in a sequence
    def check_flush(self, hand):
        pass

    # Five cards in a sequence, but not of the same suit.
    def check_straight(self, hand):
        pass

    # Three cards of the same rank
    def check_three_of_kind(self, hand):
        pass

    # Two different pairs.
    def check_two_different_pairs(self, hand):
        pass

    # Two cards of the same rank
    def check_pair(self, hand):
        pass

    # High Card
    def check_high_card(self, hand):
        pass
