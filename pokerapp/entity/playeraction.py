import enum


class PlayerAction(enum.Enum):
    CHECK = "check"
    CALL = "call"
    FOLD = "fold"
    RAISE_RATE = "raise rate"
    BET = "bet"
    ALL_IN = "all in"
    BET_TEN = 10
    BET_TWENTY_FIVE = 25
    BET_FIFTY = 50
    BET_ONE_HUNDRED = 100
    BET_TWO_HUNDRED_FIFTY = 250
    BET_FIVE_HUNDRED = 500
    BET_ONE_THOUSAND = 1000
