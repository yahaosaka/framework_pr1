from datetime import date

from django.shortcuts import render

from db.database import fetch_all, fetch_one
from models.matches import check_duration


def with_dates(rows):
    """Строки sqlite3.Row → словари с датой played_on для фильтра date."""
    result = []
    for row in rows:
        item = dict(row)
        item["played_on"] = date.fromisoformat(row["match_date"])
        result.append(item)
    return result


def matches(request):
    matches_list = fetch_all(
        """
        SELECT matches.id,
               matches.match_date,
               matches.duration_minutes,
               matches.is_completed,
               games.id AS game_id,
               games.title AS game_title,
               winners.name AS winner_name,
               (SELECT COUNT(*) FROM match_players
                WHERE match_players.match_id = matches.id) AS player_count
        FROM matches
        JOIN games ON matches.game_id = games.id
        LEFT JOIN players AS winners ON matches.winner_id = winners.id
        ORDER BY matches.match_date, matches.id;
        """
    )
    return render(
        request,
        "matches/match_list.html",
        {"matches": with_dates(matches_list)},
    )


def match_detail(request, match_id):
    row = fetch_one(
        """
        SELECT matches.id,
               matches.match_date,
               matches.duration_minutes,
               matches.is_completed,
               games.id AS game_id,
               games.title AS game_title,
               winners.name AS winner_name
        FROM matches
        JOIN games ON matches.game_id = games.id
        LEFT JOIN players AS winners ON matches.winner_id = winners.id
        WHERE matches.id = ?;
        """,
        [match_id],
    )
    match = None
    players = []
    duration_check = ""
    if row is not None:
        match = with_dates([row])[0]
        match["duration_hours"] = round(row["duration_minutes"] / 60, 1)
        duration_check = check_duration(row["duration_minutes"])
        players = fetch_all(
            """
            SELECT players.id, players.name
            FROM match_players
            JOIN players ON match_players.player_id = players.id
            WHERE match_players.match_id = ?
            ORDER BY players.name;
            """,
            [match_id],
        )
    context = {
        "match": match,
        "players": players,
        "duration_check": duration_check,
    }
    return render(
        request,
        "matches/match_detail.html",
        context,
        status=404 if match is None else 200,
    )


def statistics(request):
    totals = fetch_one(
        """
        SELECT COUNT(*) AS matches_count,
               SUM(is_completed) AS completed_count,
               ROUND(AVG(duration_minutes), 1) AS avg_minutes,
               MIN(duration_minutes) AS min_minutes,
               MAX(duration_minutes) AS max_minutes,
               SUM(duration_minutes) AS total_minutes
        FROM matches;
        """
    )
    by_game = fetch_all(
        """
        SELECT games.id AS game_id,
               games.title AS game_title,
               COUNT(matches.id) AS matches_count,
               ROUND(AVG(matches.duration_minutes), 1) AS avg_minutes
        FROM games
        LEFT JOIN matches ON matches.game_id = games.id
        GROUP BY games.id, games.title
        ORDER BY matches_count DESC, games.title;
        """
    )
    rating = fetch_all(
        """
        SELECT players.name,
               COUNT(match_players.match_id) AS played,
               (SELECT COUNT(*) FROM matches
                WHERE matches.winner_id = players.id) AS wins
        FROM players
        LEFT JOIN match_players ON match_players.player_id = players.id
        GROUP BY players.id, players.name
        ORDER BY wins DESC, played DESC, players.name;
        """
    )
    min_matches = request.GET.get("min", "1")
    min_matches = int(min_matches) if min_matches.isdigit() else 1
    popular = fetch_all(
        """
        SELECT games.title AS game_title,
               COUNT(matches.id) AS matches_count
        FROM games
        JOIN matches ON matches.game_id = games.id
        GROUP BY games.id, games.title
        HAVING COUNT(matches.id) > ?
        ORDER BY matches_count DESC;
        """,
        [min_matches],
    )
    by_genre = fetch_all(
        """
        SELECT genre, COUNT(*) AS games_count
        FROM games
        GROUP BY genre
        ORDER BY games_count DESC, genre;
        """
    )
    unplayed = fetch_all(
        """
        SELECT id, title
        FROM games
        WHERE id NOT IN (SELECT game_id FROM matches)
        ORDER BY title;
        """
    )
    context = {
        "totals": totals,
        "by_game": by_game,
        "rating": rating,
        "popular": popular,
        "min_matches": min_matches,
        "by_genre": by_genre,
        "unplayed": unplayed,
    }
    return render(request, "matches/statistics.html", context)
