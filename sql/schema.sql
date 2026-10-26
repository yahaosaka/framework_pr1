-- ==========================================
-- Учет партий в настольные игры: структура базы данных
-- ==========================================

CREATE TABLE IF NOT EXISTS games (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL UNIQUE,
    min_players INTEGER NOT NULL CHECK (min_players >= 2),
    max_players INTEGER NOT NULL CHECK (max_players <= 6),
    genre TEXT,
    CHECK (min_players <= max_players)
);

CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT
);

CREATE TABLE IF NOT EXISTS matches (
    id INTEGER PRIMARY KEY,
    game_id INTEGER NOT NULL,
    match_date TEXT NOT NULL,
    duration_minutes INTEGER NOT NULL CHECK (duration_minutes > 0),
    winner_id INTEGER,
    is_completed INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (game_id) REFERENCES games(id),
    FOREIGN KEY (winner_id) REFERENCES players(id)
);

-- Участники партий: связь «многие ко многим» между matches и players
CREATE TABLE IF NOT EXISTS match_players (
    match_id INTEGER NOT NULL,
    player_id INTEGER NOT NULL,
    PRIMARY KEY (match_id, player_id),
    FOREIGN KEY (match_id) REFERENCES matches(id),
    FOREIGN KEY (player_id) REFERENCES players(id)
);
