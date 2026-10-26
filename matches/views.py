from django.http import HttpResponse

from homepage.views import page
from models.matches import check_duration, find_match_by_id
from storage import load_games, load_matches, load_players


def _load():
    games_list = load_games("data/games.json")
    players_list = load_players("data/players.json")
    return load_matches("data/matches.json", games_list, players_list)


def matches(request):
    items = ""
    for match in _load():
        status = "завершена" if match.is_completed else "идет"
        badge = "bg-success" if match.is_completed else "bg-warning"
        items += f"""
        <li class="list-group-item d-flex justify-content-between">
            <a href="/matches/{match.id}/">
                {match.match_date} – {match.game.title}
            </a>
            <span class="badge {badge}">{status}</span>
        </li>
        """
    content = f"""
    <h1>Партии</h1>
    <ul class="list-group">{items}</ul>
    """
    return HttpResponse(page("Партии – учет партий", content))


def match_detail(request, match_id):
    match = find_match_by_id(_load(), match_id)
    if match is None:
        content = """
        <h1 class="text-danger">Партия не найдена</h1>
        <a href="/matches/" class="btn btn-outline-secondary">
            ← к списку партий
        </a>
        """
        return HttpResponse(page("Партия не найдена", content), status=404)

    players = ", ".join(player.name for player in match.players)
    winner = match.winner.name if match.winner else "—"
    badge = "bg-success" if match.is_completed else "bg-warning"
    content = f"""
    <div class="card">
        <div class="card-body">
            <h5 class="card-title">Партия №{match.id}</h5>
            <p class="card-text">Игра: {match.game.title}</p>
            <p class="card-text">Дата: {match.match_date}</p>
            <p class="card-text">
                Продолжительность: {match.duration_minutes} мин.
                ({check_duration(match.duration_minutes)})
            </p>
            <p class="card-text">Участники: {players}</p>
            <p class="card-text">Победитель: {winner}</p>
            <p class="card-text">
                Статус: <span class="badge {badge}">{match.status}</span>
            </p>
            <a href="/matches/" class="btn btn-outline-secondary">
                ← к списку партий
            </a>
        </div>
    </div>
    """
    return HttpResponse(page(f"Партия №{match.id}", content), status=200)
