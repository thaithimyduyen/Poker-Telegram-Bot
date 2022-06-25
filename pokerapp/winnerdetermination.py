#!/usr/bin/env python3

import enum
from itertools import combinations
from typing import Dict, List, Tuple

from pokerapp.cards import Card, Cards
from pokerapp.entities import Player, Score

HAND_RANK = 15**5


class HandsOfPoker(enum.Enum):
    ROYAL_FLUSH = 10
    STRAIGHT_FLUSH = 9
    FOUR_OF_A_KIND = 8
    FULL_HOUSE = 7
    FLUSH = 6
    STRAIGHTS = 5
    THREE_OF_A_KIND = 4
    TWO_PAIR = 3
    PAIR = 2
    HIGH_CARD = 1


class WinnerDetermination:
    @staticmethod
    def _make_combinations(cards: Card) -> Card:
        hands = list(combinations(cards, 5))
        return hands

    @staticmethod
    def _make_values(hand) -> List[int]:
        return [i.value for i in hand]

    @staticmethod
    def _make_suits(hand) -> List[str]:
        return [i.suit for i in hand]

    @staticmethod
    def _calculate_hand_point(
        hand_value: List[int],
        kinds_poker: HandsOfPoker,
    ) -> Score:
        score = HAND_RANK*kinds_poker.value
        i = 1
        for val in hand_value:
            score += val * i
            i *= 15
        return score

    @staticmethod
    def _group_hand(hand_values: List[int]) -> Tuple[List[int], List[int]]:
        dict_hand = {}
        for i in hand_values:
            if i not in dict_hand:
                dict_hand[i] = 0
            dict_hand[i] += 1

        sorted_dict_items = sorted(
            dict_hand.items(),
            key=lambda x: x[1],
        )

        hand_values = list(map(lambda x: x[1], sorted_dict_items))
        hand_keys = list(map(lambda x: x[0], sorted_dict_items))
        return (hand_values, hand_keys)

    def _check_hand_get_score(self, hand: Cards) -> Score:
        hand_values = sorted(self._make_values(hand))
        is_single_suit = len(set(self._make_suits(hand))) == 1

        grouped_values, grouped_keys = self._group_hand(hand_values)

        delta_pos = hand_values[-1] - hand_values[0]
        is_sequence = (delta_pos == 4) and len(grouped_values) == 5

        # ROYAL_FLUSH.
        if len(grouped_keys) == 5 and hand_values[0] == 10 and is_single_suit:
            return self._calculate_hand_point(
                [], HandsOfPoker.ROYAL_FLUSH
            )

        # STRAIGHT_FLUSH.
        elif is_single_suit and is_sequence:
            return self._calculate_hand_point(
                [hand_values[-1]], HandsOfPoker.STRAIGHT_FLUSH
            )

        # FOUR_OF_A_KIND.
        elif grouped_values == [1, 4]:
            return self._calculate_hand_point(
                grouped_keys, HandsOfPoker.FOUR_OF_A_KIND
            )

        # FULL_HOUSE.
        elif grouped_values == [2, 3]:
            return self._calculate_hand_point(
                grouped_keys, HandsOfPoker.FULL_HOUSE
            )

        # FLUSH.
        elif is_single_suit:
            return self._calculate_hand_point(
                [hand_values[-1]], HandsOfPoker.FLUSH
            )

        # STRAIGHTS.
        elif is_sequence:
            return self._calculate_hand_point(
                [hand_values[-1]], HandsOfPoker.STRAIGHTS
            )

        # THREE_OF_A_KIND.
        elif grouped_values == [1, 1, 3]:
            return self._calculate_hand_point(
                grouped_keys, HandsOfPoker.THREE_OF_A_KIND
            )

        # TWO_PAIR.
        elif grouped_values == [1, 2, 2]:
            return self._calculate_hand_point(
                grouped_keys, HandsOfPoker.TWO_PAIR
            )

        # PAIR.
        elif grouped_values == [1, 1, 1, 2]:
            return self._calculate_hand_point(
                grouped_keys, HandsOfPoker.PAIR
            )

        # HIGH_CARD.
        else:
            return self._calculate_hand_point(
                hand_values, HandsOfPoker.HIGH_CARD
            )

    def _best_hand_score(self, hands: List[Cards]) -> Tuple[Cards, Score]:
        best_point = 0
        best_hand = []
        for hand in hands:
            hand_point = self._check_hand_get_score(hand)
            if hand_point > best_point:
                best_hand = hand
                best_point = hand_point
        return (best_hand, best_point)

    def determinate_scores(
        self,
        players: List[Player],
        cards_table: Cards,
    ) -> Dict[Score, List[Tuple[Player, Cards]]]:
        res = {}

        for player in players:
            player_hands = self._make_combinations(player.cards + cards_table)
            best_hand, score = self._best_hand_score(player_hands)

            if score not in res:
                res[score] = []
            res[score].append((player, best_hand))

        return res
