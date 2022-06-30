## TEXAS POKER PLAYING TELEGRAM BOT

Welcome to the telegram Bot **"Texas Poker Online"**!!!

**Try it: [@online_poker_bot](https://t.me/online_poker_bot)**

Texas Poker is one of the most popular game nowsday. And of course there are many applications and webs where you can play. We accidently thought about that why don't we playing poker when we are chatting with friends on the telegram. And how the poker game bot was created. 

The bot plays role "our admin": he divides cards, adds cards, controlls whose turn is next, determines the winner and saves our money or can give us bonus money every day.

All things that we need to do is adding bot to your group chat on telegram and every member need to  command /ready at the beginning of round. Then the game will be started. Rules of the texas poker you can read briefly below:

**Here is the brief instruction of Texas Poker**\
Every player has two private cards and on the table has five community cards which are dealt face up in the three stages.
On the beginning of game, two people which are selected for big and small blinds. This means the blinds are forced to bet, the small blind bet 5\$ and the big blind bet 10\$.
when cards are divied to every member, the stages will be started.

There are 4 stages in every game:
- The pre-flop: There is no card on the table
- The flop: Add three cards on the table
- The turn: Add to table one card 
- The river: Add to table the last card

In every stage, every member will be betting with actions:
- bet: putting into the pot the chips
- call: putting into the pot the same number of chips
- check: skipping your turn and putting no chips into pot
- raise: putting into the pot more than enough chips to call 
- all-in: putting into the pot all chips that you have
- fold: putting no chips into the pot and is out of the game.
A betting interval ends when the bets have been equalized and the new stage will be started.

The game can end any time if there is only one players in the game and of course when the winner is defined.
After four stages, every member will be show their best hand (five cards from seven cards) to determinate the winner.
The winner is determinated by various combinations of Poker hands rank from five of a kind (the highest) to no pair or nothing (the lowest) 

**Poker hand ranking**\
![chat example](https://raw.githubusercontent.com/thaithimyduyen/Poker-Telegram-Bot/master/assets/poker_hand.jpg "Chat example")

**Telegram chat example**\
![chat example](https://raw.githubusercontent.com/thaithimyduyen/Poker-Telegram-Bot/master/assets/chatexample.png "Chat example")

### How to use ?

1. Ensure you have `docker`, `docker-compose`, and `make` installed.
2. Create a token file `make .env POKERBOT_TOKEN="POKERBOT_TOKEN"`.

    > Get token from [@BotFather](https://telegram.me/BotFather).
3. Start the bot `make up`.

### FAQ

1. It shows `not enough players` after `/start`.
   All players need to send `/ready`.
   The command `/start` starts a game only for ready players.
2. I don't see my cards.
   All cards are sent in the inline keyboard, if you don't see them, try
   to send `/cards` to the chat.
   There is a bug on iOS about hiding inline keyboard.
3. My cards are overlaped with someone else on MacOS Telegram.
   It is a bug of [MacOS desktop client](https://github.com/overtake/TelegramSwift/issues/575).
4. How bonus is calculated?
   It is random and depends on the number on the side of a die.

   | side | virtual bonus money |
   | ---- | ------------------- |
   | ⚀    | 5                   |
   | ⚁    | 20                  |
   | ⚂    | 40                  |
   | ⚃    | 80                  |
   | ⚄    | 160                 |
   | ⚅    | 320                 |
5. A player doesn't want to make a turn or cannot.
   After two minutes send `/ban`.

### License

Copyright 2020 Thái Thị Mỹ Duyên

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
