-- ==========================================
-- Учет партий в настольные игры: SQL-запросы проекта
-- Значения в условиях приведены для проверки в SQLite CLI;
-- в веб-приложении они передаются параметрами ?.
-- ==========================================

-- 1. [список] Все игры по алфавиту (страница «Игры»)
SELECT id, title, min_players, max_players, genre
FROM games
ORDER BY title;

-- 2. [список] Все игроки по алфавиту
SELECT id, name, email
FROM players
ORDER BY name;

-- 3. [список, LIMIT] Пять последних партий
SELECT id, game_id, match_date, duration_minutes
FROM matches
ORDER BY match_date DESC, id DESC
LIMIT 5 OFFSET 0;

-- 4. [WHERE] Игры, в которые можно сыграть впятером
--    (страница «Подбор игры», число игроков – параметр)
SELECT id, title, min_players, max_players, genre
FROM games
WHERE min_players <= 5
  AND max_players >= 5
ORDER BY title;

-- 5. [WHERE] Незавершенные партии
SELECT id, game_id, match_date, duration_minutes
FROM matches
WHERE is_completed = 0
ORDER BY match_date;

-- 6. [WHERE] Длинные партии (более 4 часов) за сентябрь–октябрь 2026
SELECT id, game_id, match_date, duration_minutes
FROM matches
WHERE duration_minutes > 240
  AND match_date BETWEEN '2026-09-01' AND '2026-10-31';

-- 7. [WHERE, LIKE] Игры жанра «вечериночная» или с «Кол» в названии
SELECT id, title, genre
FROM games
WHERE genre = 'вечериночная'
   OR title LIKE '%Кол%';

-- 8. [JOIN] Партии с названием игры и именем победителя (страница «Партии»)
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
ORDER BY matches.match_date, matches.id;

-- 9. [JOIN] Участники партии №1 (страница партии)
SELECT players.id, players.name
FROM match_players
JOIN players ON match_players.player_id = players.id
WHERE match_players.match_id = 1
ORDER BY players.name;

-- 10. [JOIN] Партии игрока «Анна»: игра, дата, победитель
SELECT matches.id, games.title AS game_title, matches.match_date,
       winners.name AS winner_name
FROM players
JOIN match_players ON match_players.player_id = players.id
JOIN matches ON matches.id = match_players.match_id
JOIN games ON games.id = matches.game_id
LEFT JOIN players AS winners ON winners.id = matches.winner_id
WHERE players.name = 'Анна'
ORDER BY matches.match_date;

-- 11. [агрегат] Общее число партий и число завершенных
SELECT COUNT(*) AS matches_count,
       SUM(is_completed) AS completed_count
FROM matches;

-- 12. [агрегат] Продолжительность партий: средняя, минимальная,
--     максимальная и суммарная
SELECT ROUND(AVG(duration_minutes), 1) AS avg_minutes,
       MIN(duration_minutes) AS min_minutes,
       MAX(duration_minutes) AS max_minutes,
       SUM(duration_minutes) AS total_minutes
FROM matches;

-- 13. [агрегат] Сколько партий без победителя (COUNT(column) и NULL)
SELECT COUNT(*) AS all_matches,
       COUNT(winner_id) AS with_winner
FROM matches;

-- 14. [GROUP BY] Количество партий и средняя длительность по играм
--     (игры без партий тоже выводятся – LEFT JOIN)
SELECT games.title AS game_title,
       COUNT(matches.id) AS matches_count,
       ROUND(AVG(matches.duration_minutes), 1) AS avg_minutes
FROM games
LEFT JOIN matches ON matches.game_id = games.id
GROUP BY games.id, games.title
ORDER BY matches_count DESC, games.title;

-- 15. [GROUP BY] Рейтинг игроков: сыграно партий и побед
SELECT players.name,
       COUNT(match_players.match_id) AS played,
       (SELECT COUNT(*) FROM matches
        WHERE matches.winner_id = players.id) AS wins
FROM players
LEFT JOIN match_players ON match_players.player_id = players.id
GROUP BY players.id, players.name
ORDER BY wins DESC, played DESC, players.name;

-- 16. [GROUP BY] Количество игр каждого жанра
SELECT genre, COUNT(*) AS games_count
FROM games
GROUP BY genre
ORDER BY games_count DESC, genre;

-- 17. [GROUP BY, HAVING] Игры, сыгранные больше одного раза
SELECT games.title AS game_title,
       COUNT(matches.id) AS matches_count
FROM games
JOIN matches ON matches.game_id = games.id
GROUP BY games.id, games.title
HAVING COUNT(matches.id) > 1
ORDER BY matches_count DESC;

-- 18. [подзапрос, NOT IN] Игры, в которые еще ни разу не играли
SELECT id, title
FROM games
WHERE id NOT IN (SELECT game_id FROM matches)
ORDER BY title;
