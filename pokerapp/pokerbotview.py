#!/usr/bin/env python3

from telegram import (
    Dice,
    Message,
    ParseMode,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    Bot,
)
from io import BytesIO

from pokerapp.desk import DeskImageGenerator
from pokerapp.cards import Cards
from pokerapp.entities import (
    Game,
    Player,
    PlayerAction,
    MessageId,
    ChatId,
    Mention,
    Money,
)


class PokerBotViewer:
    def __init__(self, bot: Bot):
        self._bot = bot
        self._desk_generator = DeskImageGenerator()

    def send_message(self, chat_id: ChatId, text: str) -> None:
        self._bot.send_message(
            chat_id=chat_id,
            parse_mode=ParseMode.MARKDOWN,
            text=text,
        )

    def send_photo(self, chat_id: ChatId) -> None:
        # TODO: photo to args.
        self._bot.send_photo(
            chat_id=chat_id,
            photo=open("./assets/poker_hand.jpg", 'rb'),
            parse_mode=ParseMode.MARKDOWN,
        )
    
    def send_dice_reply(
        self,
        chat_id: ChatId,
        message_id: MessageId,
    ) -> Message:
        return self._bot.send_dice(
            reply_to_message_id=message_id,
            chat_id=chat_id,
        )

    def send_message_reply(
        self,
        chat_id: ChatId,
        message_id: MessageId,
        text: str,
    ) -> None:
        
        self._bot.send_message(
            reply_to_message_id=message_id,
            chat_id=chat_id,
            parse_mode=ParseMode.MARKDOWN,
            text=text,
        )

    def send_desk_cards_img(
        self,
        chat_id: ChatId,
        cards: Cards,
        caption="",
    ):
        im_cards = self._desk_generator.generate_desk(cards)
        bio = BytesIO()
        bio.name = 'desk.png'
        im_cards.save(bio, 'PNG')
        bio.seek(0)
        return self._bot.send_photo(
            chat_id=chat_id,
            photo=bio,
            caption=caption,
            parse_mode=ParseMode.MARKDOWN,
        )

    @staticmethod
    def _get_cards_markup(cards: Cards) -> ReplyKeyboardMarkup:
        return ReplyKeyboardMarkup(
            keyboard=[cards],
            selective=True,
            resize_keyboard=True,
        )

    @staticmethod
    def _get_turns_markup(
        check_call_action: PlayerAction
    ) -> InlineKeyboardMarkup:
        keyboard = [[
            InlineKeyboardButton(
                text=PlayerAction.FOLD.value,
                callback_data=PlayerAction.FOLD.value,
            ),
            InlineKeyboardButton(
                text=PlayerAction.ALL_IN.value,
                callback_data=PlayerAction.ALL_IN.value,
            ),
            InlineKeyboardButton(
                text=check_call_action.value,
                callback_data=check_call_action.value,
            ),
        ], [
            InlineKeyboardButton(
                text=str(PlayerAction.SMALL.value) + "$",
                callback_data=str(PlayerAction.SMALL.value)
            ),
            InlineKeyboardButton(
                text=str(PlayerAction.NORMAL.value) + "$",
                callback_data=str(PlayerAction.NORMAL.value)
            ),
            InlineKeyboardButton(
                text=str(PlayerAction.BIG.value) + "$",
                callback_data=str(PlayerAction.BIG.value)
            ),
        ]]

        return InlineKeyboardMarkup(
            inline_keyboard=keyboard
        )

    def send_cards(
            self,
            chat_id: ChatId,
            cards: Cards,
            mention_markdown: Mention,
    ) -> None:
        markup = PokerBotViewer._get_cards_markup(cards)
        self._bot.send_message(
            chat_id=chat_id,
            text="Showing cards to " + mention_markdown,
            reply_markup=markup,
            parse_mode=ParseMode.MARKDOWN
        )

    @staticmethod
    def define_check_call_action(
        game: Game,
        player: Player,
    ) -> PlayerAction:
        if player.round_rate == game.max_round_rate:
            return PlayerAction.CHECK
        return PlayerAction.CALL

    def send_turn_actions(
            self,
            chat_id: ChatId,
            game: Game,
            player: Player,
            money: Money,
    ) -> None:
        if len(game.cards_table) == 0:
            cards_table = "no cards"
        else:
            cards_table = " ".join(game.cards_table)
        text = (
            "Turn of {}\n" +
            "{}\n" +
            "Money: *{}$*\n" +
            "Max round rate: *{}$*"
        ).format(
            player.mention_markdown,
            cards_table,
            money,
            game.max_round_rate,
        )
        check_call_action = PokerBotViewer.define_check_call_action(
            game, player
        )
        markup = PokerBotViewer._get_turns_markup(check_call_action)
        self._bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=markup,
            parse_mode=ParseMode.MARKDOWN
        )

    def remove_markup(
        self,
        chat_id: ChatId,
        message_id: MessageId,
    ) -> None:
        self._bot.edit_message_reply_markup(
            chat_id=chat_id,
            message_id=message_id,
        )
