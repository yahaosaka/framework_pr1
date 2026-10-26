from django.shortcuts import render

from models.games import find_game_by_id
from models.matches import matches_for_game
from storage import load_games, load_matches, load_players


def games(request):
    games_list = load_games("data/games.json")
    context = {
        "games": games_list,
    }
    return render(request, "games/game_list.html", context)


def game_detail(request, game_id):
    games_list = load_games("data/games.json")
    game = find_game_by_id(games_list, game_id)
    game_matches = []
    if game is not None:
        players_list = load_players("data/players.json")
        matches_list = load_matches(
            "data/matches.json",
            games_list,
            players_list,
        )
        game_matches = matches_for_game(matches_list, game)
    context = {
        "game": game,
        "matches": game_matches,
    }
    return render(
        request,
        "games/game_detail.html",
        context,
        status=404 if game is None else 200,
    )
