from pokerapp.entity.entities import UserId, Mention
from pokerapp.entity.playerstate import PlayerState
from pokerapp.entity.wallet import Wallet


class Player:
    def __init__(
            self,
            user_id: UserId,
            mention_markdown: Mention,
            wallet: Wallet,
            ready_message_id: str,
    ):
        self.user_id = user_id
        self.mention_markdown = mention_markdown
        self.state = PlayerState.ACTIVE
        self.wallet = wallet
        self.cards = []
        self.round_rate = 0
        self.ready_message_id = ready_message_id

    def __repr__(self):
        return "{}({!r})".format(self.__class__.__name__, self.__dict__)

    def __eq__(self, other):
        return self.user_id == other.user_id
