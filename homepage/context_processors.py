from games.models import Game


def project_info(request):
    return {
        "site_title": "Учет партий в настольные игры",
        "games_count": Game.objects.count(),
    }
