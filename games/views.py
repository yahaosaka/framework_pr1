from django.http import HttpResponse

from homepage.views import page
from models.games import find_game_by_id
from models.matches import matches_for_game
from storage import load_games, load_matches, load_players


def games(request):
    items = ""
    for game in load_games("data/games.json"):
        items += (
            f'<li class="list-group-item">'
            f'<a href="/games/{game.id}/">{game.title}</a> – '
            f"{game.min_players}–{game.max_players} игроков, {game.genre}"
            f"</li>"
        )
    content = f"""
    <h1>Настольные игры</h1>
    <ul class="list-group">{items}</ul>
    """
    return HttpResponse(page("Игры – учет партий", content))


def game_detail(request, game_id):
    games_list = load_games("data/games.json")
    game = find_game_by_id(games_list, game_id)
    if game is None:
        content = """
        <h1 class="text-danger">Игра не найдена</h1>
        <a href="/games/" class="btn btn-outline-secondary">
            ← к списку игр
        </a>
        """
        return HttpResponse(page("Игра не найдена", content), status=404)

    players_list = load_players("data/players.json")
    matches_list = load_matches("data/matches.json", games_list, players_list)
    played = len(matches_for_game(matches_list, game))
    badge = "bg-success" if played else "bg-secondary"
    content = f"""
    <div class="card">
        <div class="card-body">
            <h5 class="card-title">{game.title}</h5>
            <p class="card-text"><strong>ID:</strong> {game.id}</p>
            <p class="card-text"><strong>Жанр:</strong> {game.genre}</p>
            <p class="card-text">
                <strong>Игроков:</strong>
                от {game.min_players} до {game.max_players}
            </p>
            <p class="card-text">
                Сыграно партий: <span class="badge {badge}">{played}</span>
            </p>
            <a href="/games/" class="btn btn-outline-secondary">
                ← к списку игр
            </a>
        </div>
    </div>
    """
    return HttpResponse(page(game.title, content), status=200)
