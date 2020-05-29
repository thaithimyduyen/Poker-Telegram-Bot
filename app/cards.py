#!/usr/bin/env python3


# TODO: Add function get_cards(). It should create shuffled copy of cards.
class Card(str):
    @property
    def suit(self):
        return self[1]

    @property
    def value(self):
        if self[0] == "J":
            return 11
        elif self[0] == "Q":
            return 12
        elif self[0] == "K":
            return 13
        elif self[0] == "A":
            return 14
        return int(self[0])


CARDS = [
    Card("2♥️"), Card("3♥️"), Card("4♥️"), Card("5♥️"),
    Card("6♥️"), Card("7♥️"), Card("8♥️"), Card("9♥️"),
    Card("10♥️"), Card("J♥️"), Card("Q♥️"), Card("K♥️"),
    Card("A♥️"), Card("2♦️"), Card("3♦️"), Card("4♦️"),
    Card("5♦️"), Card("6♦️"), Card("7♦️"), Card("8♦️"),
    Card("9♦️"), Card("10♦️"), Card("J♦️"), Card("Q♦️"),
    Card("K♦️"), Card("A♦️"), Card("2♣️"), Card("3♣️"),
    Card("4♣️"), Card("5♣️"), Card("6♣️"), Card("7♣️"),
    Card("8♣️"), Card("9♣️"), Card("10♣️"), Card("J♣️"),
    Card("Q♣️"), Card("K♣️"), Card("A♣️"), Card("2♠️"),
    Card("3♠️"), Card("4♠️"), Card("5♠️"), Card("6♠️"),
    Card("7♠️"), Card("8♠️"), Card("9♠️"), Card("10♠️"),
    Card("J♠️"), Card("Q♠️"), Card("K♠️"), Card("A♠️"),
]
