#!/usr/bin/env python3
from app.entities import Card, Cards
from itertools import combinations
import enum

dict_cards_order = {
    2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7,
    8: 8, 9: 9, 10: 10, 11: 11, 12: 12, 13: 13, 14: 14
}
CONST_POKER = 15**5


class HandsOfPoker(enum.Enum):
    Royal_flush = 10
    Straight_flush = 9
    Four_of_a_kind = 8
    Full_house = 7
    Flush = 6
    Straights = 5
    Three_of_a_kind = 4
    Two_pair = 3
    Pair = 2
    High_Card = 1


class WinnerDetermination:
    def _make_combinations(self, cards: Card) -> Card:
        hands = list(combinations(cards, 5))
        return hands

    def _calculate_hand_point(self, hand: Cards) -> int:
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

    def _determine_best_hand(self, hands) -> list:
        best_point = 0
        best_hand = []
        for hand in hands:
            hand_point = self._calculate_hand_point(hand)
            if hand_point > best_point:
                best_hand = hand
                best_point = hand_point
        return [best_hand, best_point]

    def determine_winner(self, all_cards_all_players):
        for player, all_card in all_cards_all_players.items():
            hands = self._make_combinations(all_card)
            best_hand, best_point = self._determine_best_hand(hands)
            hand_point_player_dict = {
                player: [best_hand, best_point]
            }

        winner_point = 0
        winner = []
        winner_hand = []
        for player, hand_and_point in hand_point_player_dict.items():
            best_hand, best_point = hand_and_point
            if best_point > winner_point:
                winner_point = best_point

        for player, hand_and_point in hand_point_player_dict.items():
            best_hand, best_point = hand_and_point
            if best_point == winner_point:
                winner_hand.append(best_hand)
                winner.append(player)

        return [winner, winner_hand]

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
            point = CONST_POKER*HandsOfPoker.Royal_flush.value
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
            point = (CONST_POKER *
                     HandsOfPoker.Straight_flush.value) + hand_value[4]
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
            point = CONST_POKER*HandsOfPoker.Four_of_a_kind.value
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
            point = CONST_POKER*HandsOfPoker.Full_house.value
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
            point = max(hand_value) + CONST_POKER*HandsOfPoker.Flush.value
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
            point = CONST_POKER*HandsOfPoker.Straights.value + hand_value[4]
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
            point = CONST_POKER*HandsOfPoker.Three_of_a_kind.value
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
            point = CONST_POKER*HandsOfPoker.Two_pair.value
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
            point = CONST_POKER*HandsOfPoker.Pair.value
            for k in sort_dict_hand_key:
                point += k*(15**i)
                i -= 1
        return point

    # High Card
    def check_high_card(self, hand):
        point = 0
        hand_value = sorted(self.make_value(hand))
        hand_value.append(HandsOfPoker.High_Card.value)
        for i in range(6):
            point += hand_value[i]*(15**i)
        return point
