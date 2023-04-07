from typing import List, Tuple, Dict

from pokerapp.entity.cards import Cards
from pokerapp.entity.entities import Money, Score
from pokerapp.entity.game import Game
from pokerapp.entity.player import Player
from pokerapp.entity.playerbet import PlayerBet

SMALL_BLIND = 5


class RoundRateModel:

    def round_pre_flop_rate_before_first_turn(self, game: Game) -> None:
        self.raise_rate_bet(game, game.players[0], SMALL_BLIND)
        self.raise_rate_bet(game, game.players[1], SMALL_BLIND)

    def round_pre_flop_rate_after_first_turn(self, game: Game) -> None:
        dealer = 2 % len(game.players)
        game.trading_end_user_id = game.players[dealer].user_id

    def raise_rate_bet(self, game: Game, player: Player, amount: int) -> None:
        amount += game.max_round_rate - player.round_rate

        player.wallet.authorize(
            game_id=game.id,
            amount=amount,
        )
        player.round_rate += amount

        game.players_bets = game.players_bets + [PlayerBet(player.user_id, amount, game.state)]

        game.max_round_rate = player.round_rate
        game.trading_end_user_id = player.user_id

    def call_check(self, game, player) -> None:
        amount = game.max_round_rate - player.round_rate

        player.wallet.authorize(
            game_id=game.id,
            amount=amount,
        )

        game.players_bets = game.players_bets + [PlayerBet(player.user_id, amount, game.state)]

        player.round_rate += amount

    def all_in(self, game, player) -> Money:
        amount = player.wallet.authorize_all(
            game_id=game.id,
        )
        player.round_rate += amount
        if game.max_round_rate < player.round_rate:
            game.max_round_rate = player.round_rate
            game.trading_end_user_id = player.user_id

        game.players_bets = game.players_bets + [PlayerBet(player.user_id, amount, game.state)]

        return amount

    def _sum_authorized_money(
            self,
            game: Game,
            players: List[Tuple[Player, Cards]],
    ) -> int:
        sum_authorized_money = 0
        for player in players:
            sum_authorized_money += player[0].wallet.authorized_money(
                game_id=game.id,
            )
        return sum_authorized_money

    def finish_rate(
            self,
            game: Game,
            player_scores: Dict[Score, List[Tuple[Player, Cards]]],
    ) -> List[Tuple[Player, Cards, Money]]:
        sorted_player_scores_items = sorted(
            player_scores.items(),
            reverse=True,
            key=lambda x: x[0],
        )
        player_scores_values = list(
            map(lambda x: x[1], sorted_player_scores_items))

        res = []
        for win_players in player_scores_values:
            players_authorized = self._sum_authorized_money(
                game=game,
                players=win_players,
            )
            if players_authorized <= 0:
                continue

            game_pot = game.pot
            for win_player, best_hand in win_players:
                if game.pot <= 0:
                    break

                authorized = win_player.wallet.authorized_money(
                    game_id=game.id,
                )

                win_money_real = game_pot * (authorized / players_authorized)
                win_money_real = round(win_money_real)

                win_money_can_get = authorized * len(game.players)
                win_money = min(win_money_real, win_money_can_get)

                win_player.wallet.inc(win_money)
                game.pot -= win_money
                res.append((win_player, best_hand, win_money))

        return res

    def to_pot(self, game) -> None:
        for p in game.players:
            game.pot += p.round_rate
            p.round_rate = 0
        game.max_round_rate = 0
        game.trading_end_user_id = game.players[0].user_id
