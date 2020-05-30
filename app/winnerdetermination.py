#!/usr/bin/env python3

import enum
from itertools import combinations
from typing import Dict, List, Tuple

from app.cards import Card, Cards
from app.entities import Player, Score

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
    def _make_combinations(self, cards: Card) -> Card:
        hands = list(combinations(cards, 5))
        return hands

    def _calculate_hand_point(self, hand: Cards) -> Score:
        if self.check_royal_flush(hand) != 0:
            return self.check_royal_flush(hand)
        elif self.check_straight_flush(hand) != 0:
            return self.check_straight_flush(hand)
        elif self.check_four_of_a_kind(hand) != 0:
            return self.check_four_of_a_kind(hand)
        elif self.check_full_house(hand) != 0:
            return self.check_full_house(hand)
        elif self.check_flush(hand) != 0:
            return self.check_flush(hand)
        elif self.check_straight(hand) != 0:
            return self.check_straight(hand)
        elif self.check_three_of_kind(hand) != 0:
            return self.check_three_of_kind(hand)
        elif self.check_two_different_pairs(hand) != 0:
            return self.check_two_different_pairs(hand)
        elif self.check_pair(hand) != 0:
            return self.check_pair(hand)
        elif self.check_high_card(hand) != 0:
            return self.check_high_card(hand)

    def _best_hand_score(self, hands) -> Tuple[Cards, Score]:
        best_point = 0
        best_hand = []
        for hand in hands:
            hand_point = self._calculate_hand_point(hand)
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

    def make_value(self, hand):
        return [i.value for i in hand]

    def make_suit(self, hand):
        return [i.suit for i in hand]

    # A, K, Q, J, 10, all the same suit
    def check_royal_flush(self, hand):
        point = 0
        hand_value = sorted(set(self.make_value(hand)))
        hand_suit = set(self.make_suit(hand))
        min_hand = hand_value[0]
        if len(hand_value) == 5 and min_hand == 10 and len(hand_suit) == 1:
            point = HAND_RANK*HandsOfPoker.ROYAL_FLUSH.value
        return point

    # Five cards in a sequence, all in the same suit
    def check_straight_flush(self, hand):
        point = 0
        hand_value = sorted(set(self.make_value(hand)))
        hand_suit = set(self.make_suit(hand))
        if len(hand_value) < 5:
            return point
        min_pos = hand_value[0]
        max_pos = hand_value[4]
        delta_pos = max_pos - min_pos
        if len(hand_suit) == 1 and delta_pos == 4:
            point = (HAND_RANK *
                     HandsOfPoker.STRAIGHT_FLUSH.value) + hand_value[4]
        return point

    # All four cards of the same rank
    def check_four_of_a_kind(self, hand):
        point = 0
        dict_hand = {}
        hand_value = self.make_value(hand)
        for i in hand_value:
            if i not in dict_hand:
                dict_hand[i] = 0
            dict_hand[i] += 1
        sort_dict_hand = sorted(
            dict_hand.items(), key=lambda x: x[1], reverse=True)

        sort_dict_hand_value = list(map(lambda x: x[1], sort_dict_hand))
        sort_dict_hand_key = list(map(lambda x: x[0], sort_dict_hand))

        if sort_dict_hand_value == [4, 1]:
            i = 2
            point = HAND_RANK*HandsOfPoker.FOUR_OF_A_KIND.value
            for k in sort_dict_hand_key:
                point += k*(15**i)
                i -= 1
        return point

    # Three of a kind with a pair
    def check_full_house(self, hand):
        point = 0
        dict_hand = {}
        hand_value = self.make_value(hand)
        for i in hand_value:
            if i not in dict_hand:
                dict_hand[i] = 0
            dict_hand[i] += 1
        sort_dict_hand = sorted(
            dict_hand.items(), key=lambda x: x[1], reverse=True)

        sort_dict_hand_value = list(map(lambda x: x[1], sort_dict_hand))
        sort_dict_hand_key = list(map(lambda x: x[0], sort_dict_hand))
        if sort_dict_hand_value == [3, 2]:
            i = 1
            point = HAND_RANK*HandsOfPoker.FULL_HOUSE.value
            for k in sort_dict_hand_key:
                point += k*(15**i)
                i -= 1
        return point

    # Any five cards of the same suit, but not in a sequence

    def check_flush(self, hand):
        point = 0
        suit = self.make_suit(hand)
        hand_value = self.make_value(hand)
        if len(set(suit)) == 1:
            point = max(hand_value) + HAND_RANK*HandsOfPoker.FLUSH.value
        return point

    # Five cards in a sequence, but not of the same suit.
    def check_straight(self, hand):
        point = 0
        hand_value = sorted(set(self.make_value(hand)))
        if len(hand_value) < 5:
            return point
        min_pos = hand_value[0]
        max_pos = hand_value[4]
        delta_pos = max_pos - min_pos
        if delta_pos == 4:
            point = HAND_RANK*HandsOfPoker.STRAIGHTS.value + hand_value[4]
        return point

    # Three cards of the same rank
    def check_three_of_kind(self, hand):
        point = 0
        hand_value = self.make_value(hand)
        dict_hand = {}
        for i in hand_value:
            if i not in dict_hand:
                dict_hand[i] = 0
            dict_hand[i] += 1
        sort_dict_hand = sorted(
            dict_hand.items(), key=lambda x: x[1], reverse=True)

        sort_dict_hand_value = list(map(lambda x: x[1], sort_dict_hand))
        sort_dict_hand_key = list(map(lambda x: x[0], sort_dict_hand))
        if sort_dict_hand_value == [3, 1, 1]:
            i = 2
            point = HAND_RANK*HandsOfPoker.THREE_OF_A_KIND.value
            for k in sort_dict_hand_key:
                point += k*(15**i)
                i -= 1
        return point

    # Two different pairs.
    def check_two_different_pairs(self, hand):
        point = 0
        hand_value = self.make_value(hand)
        dict_hand = {}
        for i in hand_value:
            if i not in dict_hand:
                dict_hand[i] = 0
            dict_hand[i] += 1
        sort_dict_hand = sorted(
            dict_hand.items(), key=lambda x: x[1], reverse=True)
        sort_dict_hand_value = list(map(lambda x: x[1], sort_dict_hand))
        sort_dict_hand_key = list(map(lambda x: x[0], sort_dict_hand))
        if sort_dict_hand_value == [2, 2, 1]:
            i = 3
            point = HAND_RANK*HandsOfPoker.TWO_PAIR.value
            for k in sort_dict_hand_key:
                point += k*(15**i)
                i -= 1
        return point

    # Two cards of the same rank
    def check_pair(self, hand):
        point = 0
        hand_value = self.make_value(hand)
        dict_hand = {}
        for i in hand_value:
            if i not in dict_hand:
                dict_hand[i] = 0
            dict_hand[i] += 1
        sort_dict_hand = sorted(
            dict_hand.items(), key=lambda x: x[1], reverse=True)

        sort_dict_hand_value = list(map(lambda x: x[1], sort_dict_hand))
        sort_dict_hand_key = list(map(lambda x: x[0], sort_dict_hand))

        if sort_dict_hand_value == [2, 1, 1, 1]:
            i = 3
            point = HAND_RANK*HandsOfPoker.PAIR.value
            for k in sort_dict_hand_key:
                point += k*(15**i)
                i -= 1
        return point

    # High Card
    def check_high_card(self, hand):
        point = 0
        hand_value = sorted(self.make_value(hand))
        hand_value.append(HandsOfPoker.HIGH_CARD.value)
        for i in range(6):
            point += hand_value[i]*(15**i)
        return point
