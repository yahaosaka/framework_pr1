from django.shortcuts import render

from db.database import fetch_all, fetch_one
from matches.views import with_dates


def games(request):
    games_list = fetch_all(
        """
        SELECT id, title, min_players, max_players, genre
        FROM games
        ORDER BY title;
        """
    )
    return render(request, "games/game_list.html", {"games": games_list})


def game_detail(request, game_id):
    game = fetch_one(
        """
        SELECT id, title, min_players, max_players, genre
        FROM games
        WHERE id = ?;
        """,
        [game_id],
    )
    game_matches = []
    if game is not None:
        game_matches = with_dates(
            fetch_all(
                """
                SELECT matches.id,
                       matches.match_date,
                       matches.is_completed,
                       winners.name AS winner_name
                FROM matches
                LEFT JOIN players AS winners
                    ON matches.winner_id = winners.id
                WHERE matches.game_id = ?
                ORDER BY matches.match_date;
                """,
                [game_id],
            )
        )
    return render(
        request,
        "games/game_detail.html",
        {"game": game, "matches": game_matches},
        status=404 if game is None else 200,
    )


def game_search(request):
    """Подбор игр для заданного количества игроков."""
    players_value = request.GET.get("players", "").strip()
    player_count = None
    error = ""
    games_list = []
    if players_value:
        if players_value.isdigit():
            player_count = int(players_value)
            games_list = fetch_all(
                """
                SELECT id, title, min_players, max_players, genre
                FROM games
                WHERE min_players <= ?
                  AND max_players >= ?
                ORDER BY title;
                """,
                [player_count, player_count],
            )
        else:
            error = "Введите целое число игроков."
    context = {
        "games": games_list,
        "player_count": player_count,
        "players_value": players_value,
        "error": error,
    }
    return render(request, "games/game_search.html", context)
