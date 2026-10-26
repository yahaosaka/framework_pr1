from django.shortcuts import render

from models.matches import check_duration, find_match_by_id
from storage import load_games, load_matches, load_players


def _load_matches():
    games_list = load_games("data/games.json")
    players_list = load_players("data/players.json")
    return load_matches("data/matches.json", games_list, players_list)


def matches(request):
    context = {
        "matches": _load_matches(),
    }
    return render(request, "matches/match_list.html", context)


def match_detail(request, match_id):
    match = find_match_by_id(_load_matches(), match_id)
    context = {
        "match": match,
        "duration_check": (
            check_duration(match.duration_minutes) if match else ""
        ),
    }
    return render(
        request,
        "matches/match_detail.html",
        context,
        status=404 if match is None else 200,
    )
