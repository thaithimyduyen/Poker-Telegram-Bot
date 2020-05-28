#!/usr/bin/env python3

from telegram import (
    ParseMode,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    Bot,
)


from app.entities import (
    Game,
    Player,
    PlayerAction,
    MessageId,
    ChatId,
    Cards,
    Mention,
)


class PokerBotViewer:
    def __init__(self, bot: Bot):
        self._bot = bot

    def send_message(self, chat_id: ChatId, text: str) -> MessageId:
        return self._bot.send_message(
            chat_id=chat_id,
            parse_mode=ParseMode.MARKDOWN,
            text=text,
        ).message_id

    def send_message_reply(
        self,
        chat_id: ChatId,
        message_id: MessageId,
        text: str,
    ) -> MessageId:
        return self._bot.send_message(
            reply_to_message_id=message_id,
            chat_id=chat_id,
            parse_mode=ParseMode.MARKDOWN,
            text=text,
        ).message_id

    @staticmethod
    def _get_cards_markup(cards: Cards) -> ReplyKeyboardMarkup:
        return ReplyKeyboardMarkup(
            keyboard=[cards],
            selective=True,
            resize_keyboard=True,
        )

    @staticmethod
    def _get_turns_markup(change_action: list) -> InlineKeyboardMarkup:
        keyboard = [[
            InlineKeyboardButton(
                text=PlayerAction.fold.value,
                callback_data=PlayerAction.fold.value
            ),
            InlineKeyboardButton(
                text=PlayerAction.all_in.value,
                callback_data=PlayerAction.all_in.value
            )
        ]]
        for action in change_action:
            keyboard.append([InlineKeyboardButton(
                text=action,
                callback_data=action
            )])

        return InlineKeyboardMarkup(
            inline_keyboard=keyboard
        )

    def send_cards(
            self,
            chat_id: ChatId,
            cards: Cards,
            mention_markdown: Mention,
    ) -> MessageId:
        markup = PokerBotViewer._get_cards_markup(cards)
        return self._bot.send_message(
            chat_id=chat_id,
            text="Showing cards to " + mention_markdown,
            reply_markup=markup,
            parse_mode=ParseMode.MARKDOWN
        ).message_id

    @staticmethod
    def define_change_action(game: Game, player: Player):
        if player.round_rate == game.max_round_rate:
            return [PlayerAction.check.value, PlayerAction.bet.value]
        else:
            return [PlayerAction.call.value, PlayerAction.raise_rate.value]

    def send_turn_actions(
            self,
            chat_id: ChatId,
            game: Game,
            player: Player,
    ) -> MessageId:
        if len(game.cards_table) == 0:
            cards_table = "no cards"
        else:
            cards_table = " ".join(game.cards_table)

        text = (
            "{}, it is your turn\n" +
            "Cards on the table: \n" +
            "{}\n" +
            "Your money: *{}$*\n " +
            "Max round rate: *{}$*"
        ).format(
            player.mention_markdown,
            cards_table,
            player.money,
            game.max_round_rate,
        )
        change_action = PokerBotViewer.define_change_action(game, player)
        markup = PokerBotViewer._get_turns_markup(change_action)
        return self._bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=markup,
            parse_mode=ParseMode.MARKDOWN
        ).message_id
