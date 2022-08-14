Welcome to Bot - "Texas Poker"
It is open-source: https://github.com/thaithimyduyen/Poker-Telegram-Bot

*How*:
1. Add this bot to your telegram group.
2. Each member of the group should send the command /ready in order to start the game.
3. Everyone can see only his cards in the inline menu.
4. Enjoy the time with the Bot!

*Commands*:
- /start - start the game without waiting for all users to be ready.
- /ready - mark yourself ready, when all players are ready, the game will be started.
- /money - get daily money bonus.
- /ban   - ban a current player if he didn't make a move in 2 minutes.
- /cards - show your cards to you.

*Here is the brief instruction of Texas Poker*:
Every player has two private cards and on the table has five community cards which are dealt face up in the three stages.
On the beginning of game, two people which are selected for big and small blinds. This means the blinds are forced to bet, the small blind bet 5$ and the big blind bet 10$.
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

*You will receive game cards to this chat.*
To stop it, run /stop.

Have the problem? Create an issue: https://github.com/thaithimyduyen/Poker-Telegram-Bot/issues/new
