#!/usr/bin/env python3

import random
from typing import List


class Card(str):
    @property
    def suit(self) -> str:
        return self[-1:]

    @property
    def rank(self) -> str:
        return self[:-1]

    @property
    def value(self) -> str:
        if self[0] == "J":
            return 11
        elif self[0] == "Q":
            return 12
        elif self[0] == "K":
            return 13
        elif self[0] == "A":
            return 14
        return int(self[:-1])


Cards = List[Card]


def get_cards() -> Cards:
    cards = [
        Card("2♥"), Card("3♥"), Card("4♥"), Card("5♥"),
        Card("6♥"), Card("7♥"), Card("8♥"), Card("9♥"),
        Card("10♥"), Card("J♥"), Card("Q♥"), Card("K♥"),
        Card("A♥"), Card("2♦"), Card("3♦"), Card("4♦"),
        Card("5♦"), Card("6♦"), Card("7♦"), Card("8♦"),
        Card("9♦"), Card("10♦"), Card("J♦"), Card("Q♦"),
        Card("K♦"), Card("A♦"), Card("2♣"), Card("3♣"),
        Card("4♣"), Card("5♣"), Card("6♣"), Card("7♣"),
        Card("8♣"), Card("9♣"), Card("10♣"), Card("J♣"),
        Card("Q♣"), Card("K♣"), Card("A♣"), Card("2♠"),
        Card("3♠"), Card("4♠"), Card("5♠"), Card("6♠"),
        Card("7♠"), Card("8♠"), Card("9♠"), Card("10♠"),
        Card("J♠"), Card("Q♠"), Card("K♠"), Card("A♠"),
    ]
    random.SystemRandom().shuffle(cards)
    return cards
