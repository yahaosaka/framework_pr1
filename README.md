# Система учета партий в настольные игры

## Назначение

Консольная версия (ПР3) дополнена веб-интерфейсом на Django (ПР5),
страницы которого формируются шаблонами Django (ПР6), а данные
хранятся в базе SQLite и получаются SQL-запросами (ПР7).

Приложение для учета партий в настольные игры: хранит справочник игр,
список игроков и сыгранные партии, проверяет введенные данные и считает
победы игроков.

## Целевая аудитория

* любители настольных игр;
* организаторы настольных игр;
* участники игровых клубов.

## Предметная область

Предметной областью проекта являются настольные игры и игровые партии.

Основным объектом учета является партия в настольную игру. Для партии необходимо хранить информацию об игре, дате проведения, количестве игроков, продолжительности, победителе и статусе партии.

## Основные сущности

* Настольная игра;
* Игрок;
* Игровая партия;
* Результат партии.

## Основные функции

* ввод информации о проведенной партии;
* проверка количества участников;
* проверка продолжительности партии;
* определение статуса партии;
* фиксация победителя;
* отображение информации о партии.

## План развития

* ~~добавление хранения нескольких партий~~ (ПР2);
* ~~добавление сохранения данных в файлы~~ (ПР2);
* ~~обработка исключений~~ (ПР2);
* ~~реализация классов предметной области~~ (ПР3);
* ~~разработка веб-приложения на Django~~ (ПР5);
* ~~подключение базы данных~~ (ПР7);
* реализация пользователей;
* разработка REST API;
* контейнеризация приложения;
* настройка CI/CD.

## Возможности

Консольное приложение с меню:

* просмотр, добавление, поиск игр и подбор игр по числу игроков;
* проверка, подходит ли игра для заданного числа игроков;
* просмотр, добавление и поиск игроков;
* создание партии с проверкой числа игроков и продолжительности;
* завершение партии с выбором победителя среди участников;
* рейтинг игроков по числу побед;
* сохранение данных между запусками в JSON-файлах;
* проверка данных одной партии (исходный сценарий ПР1).

## Классы

### Game – настольная игра
Атрибуты: `id`, `title`, `min_players`, `max_players`, `genre`.
Методы: `is_suitable_for()`, `__str__()`, статический `validate_players()`,
классовый `from_data()`, `to_data()`; свойство `info`.

### Player – игрок
Атрибуты: `id`, `name`, `email`.
Методы: `__str__()`, `from_data()`, `to_data()`.

### Match – партия
Атрибуты: `id`, `game` (объект `Game`), `match_date`, `duration_minutes`,
`players` (список `Player`), `winner` (`Player` или `None`), `is_completed`.
Методы: `finish()`, `__str__()`, `to_data()`; свойства `player_count`,
`status`, `duration_hours`.

### Взаимодействие объектов
`Match` хранит ссылки на объекты `Game` и `Player`, а не их номера:
`match.game.title`, `match.players[0].name`, `match.winner.email`.
Победителем может быть только участник партии. Функции модулей работают с
коллекциями `List[Game]`, `List[Player]`, `List[Match]`; операции над
одним объектом вынесены в методы классов.

## База данных SQLite (ПР7)

Данные перенесены из JSON в базу `data/boardgames.sqlite`. Django ORM на
этом этапе не используется: представления выполняют SQL-запросы через
модуль `sqlite3`.

| Таблица | Поля (тип) | Ключи |
|---------|------------|-------|
| `games` | `id` INTEGER, `title` TEXT, `min_players` INTEGER, `max_players` INTEGER, `genre` TEXT | PK `id` |
| `players` | `id` INTEGER, `name` TEXT, `email` TEXT | PK `id` |
| `matches` | `id` INTEGER, `game_id` INTEGER, `match_date` TEXT (ГГГГ-ММ-ДД), `duration_minutes` INTEGER, `winner_id` INTEGER (может быть NULL), `is_completed` INTEGER (0/1) | PK `id`; FK `game_id` → `games.id`, `winner_id` → `players.id` |
| `match_players` | `match_id` INTEGER, `player_id` INTEGER | PK (`match_id`, `player_id`); FK → `matches.id`, `players.id` |

* `sql/schema.sql` – создание таблиц (`CREATE TABLE IF NOT EXISTS`,
  ограничения `NOT NULL`, `CHECK`, `UNIQUE`, `DEFAULT`);
* `db/database.py` – подключение (`get_connection()` с
  `PRAGMA foreign_keys = ON`), создание схемы, функции `fetch_all()` и
  `fetch_one()` с `row_factory = sqlite3.Row`;
* `db/import_json.py` – перенос данных из JSON (`executemany()`,
  параметры `?`, `commit()`/`rollback()`);
* `sql/queries.sql` – 18 проверенных запросов: списки, `WHERE`
  (в том числе `BETWEEN`, `LIKE`), `JOIN`/`LEFT JOIN`, агрегатные
  функции, `GROUP BY`, `HAVING`, подзапрос `NOT IN`, `LIMIT/OFFSET`.

Создание базы и перенос данных:

```text
python -m db.import_json
```

Страницы, получающие данные из SQLite:

| URL | Данные |
|-----|--------|
| `/games/` | список игр (SELECT … ORDER BY) |
| `/games/<id>/` | игра и ее партии (WHERE, LEFT JOIN) |
| `/games/search/?players=5` | подбор игр по числу игроков (параметризованный WHERE) |
| `/matches/` | партии с названием игры и победителем (JOIN) |
| `/matches/<id>/` | партия и ее участники (JOIN через `match_players`) |
| `/matches/statistics/` | итоги (COUNT, SUM, AVG, MIN, MAX), партии по играм и рейтинг игроков (GROUP BY), популярные игры (HAVING), жанры, несыгранные игры (NOT IN) |

Значения от пользователя передаются только параметрами `?`; f-строки для
подстановки значений в SQL не используются.

## Хранение данных

JSON-файлы `data/games.json`, `data/players.json`, `data/matches.json`.
В JSON хранятся только данные и идентификаторы: в `matches.json` связи
записаны как `game_id`, `player_ids`, `winner_id`. Преобразование
JSON ↔ объекты выполняет `storage.py`: при загрузке по идентификаторам
находятся объекты `Game` и `Player`, при сохранении ссылки заменяются
идентификаторами.

Исходные данные (ПР3–ПР6) хранятся в JSON-файлах; в ПР7 они перенесены
в базу SQLite (`python -m db.import_json`), веб-страницы читают данные из
базы SQL-запросами.

## Используемые технологии

* Python 3;
* Django 5.2 – веб-фреймворк;
* Django Template Language (DTL) – шаблоны страниц;
* HTML5, собственный CSS3 и Bootstrap 5.3 – разметка и оформление;
* JavaScript – небольшое поведение интерфейса;
* SQLite и модуль sqlite3 – база данных и SQL-запросы;
* pytest – автоматизированные тесты;
* flake8 – проверка качества кода.

## Страницы веб-интерфейса

| URL | view-функция | Назначение |
|-----|--------------|------------|
| `/` | `homepage.views.index` | главная страница: описание и навигация |
| `/games/` | `games.views.games` | список игр из `data/games.json` |
| `/games/<int:game_id>/` | `games.views.game_detail` | карточка игры и число сыгранных партий |
| `/matches/` | `matches.views.matches` | список партий со статусами |
| `/matches/<int:match_id>/` | `matches.views.match_detail` | карточка партии: игра, участники, победитель |

Если игра или партия с указанным идентификатором не найдена, страница
возвращает код 404. Для адресов, которым не соответствует ни один маршрут,
используется собственный обработчик `handler404`
(`homepage.views.page_not_found`).

## Шаблоны Django (ПР6)

Генерация HTML в Python-коде представлений не используется, функция
`page()` удалена. Представления готовят данные и передают их в шаблоны
через контекст: `render(request, "games/game_list.html", {"games": ...})`.

* Базовый шаблон `templates/base.html`: структура документа, Bootstrap,
  собственный CSS, логотип, навигация, подвал, JavaScript и блоки
  `{% block title %}` и `{% block content %}`.
* Наследование: все страницы начинаются с `{% extends "base.html" %}`.
* Включаемые шаблоны: `templates/includes/navigation.html`,
  `games/includes/game_card.html` (карточка игры),
  `matches/includes/match_status.html` (статус партии – используется
  в списке партий, на странице партии и на странице игры).
* Циклы `{% for %}` с `{% empty %}` и условия `{% if %}` (наличие объекта,
  статус партии, наличие победителя).
* Именованные URL и пространства имен: `homepage:index`, `games:list`,
  `games:detail`, `matches:list`, `matches:detail`; все ссылки строятся
  тегом `{% url %}`.
* Фильтры: `length` (количество игр и партий), `default` (пустой жанр,
  отсутствующий победитель), `capfirst`, `date` (дата партии через свойство
  `Match.played_on`), `floatformat` (продолжительность в часах).
* Статические файлы `homepage/static/homepage/`: `css/style.css`
  (шапка, карточки, статусы), `js/main.js` (текущий год в подвале),
  `img/logo.png` (логотип); подключаются через `{% load static %}` и
  `{% static %}`.
* Собственная страница 404 – шаблон `templates/404.html`.

### Используется в веб-интерфейсе (ПР5)

`load_games()`, `load_players()`, `load_matches()`, `find_game_by_id()`,
`find_match_by_id()`, `matches_for_game()`, `check_duration()`.

### Отложено до следующих работ (нужны формы и POST-запросы)

Добавление игры и игрока, создание и завершение партии, поиск и сортировка
игр, рейтинг игроков.

## Структура проекта

```text
framework_pr1/
├── manage.py
├── boardgames/      настройки Django-проекта (settings.py, urls.py, wsgi/asgi)
├── templates/       base.html, 404.html, includes/navigation.html
├── homepage/        главная страница, static (css, js, img), шаблон index.html
├── games/           представления игр, templates/games/ (+ includes/game_card.html)
├── matches/         представления партий, templates/matches/ (+ includes/match_status.html)
├── sql/             schema.sql, queries.sql
├── db/              database.py, import_json.py
├── main.py          консольное меню (ПР3)
├── storage.py       загрузка и сохранение JSON
├── utils.py         безопасный ввод чисел и дат
├── models/          классы Game, Player, Match и функции работы с ними
├── data/            JSON-файлы и база boardgames.sqlite
└── tests/           тесты pytest
```

Для игроков отдельное Django-приложение пока не создается: страницы
игроков появятся вместе со статистикой.

## Запуск

Веб-версия:

```text
pip install -r requirements.txt
python -m db.import_json
python manage.py migrate
python manage.py runserver
```

После запуска открыть http://127.0.0.1:8000/

Консольная версия (сохранена):

```text
python main.py
```

## Тестирование и качество кода

```text
python manage.py check
pytest -v
flake8 . --extend-exclude=venv
```

## Текущее состояние и план развития

Реализовано (ПР5): Django-проект и три приложения, двухуровневая
маршрутизация, view-функции, страницы предметной области, обработка 404,
навигация, оформление Bootstrap.

Реализовано (ПР6): шаблоны Django, наследование, include, контекст,
циклы и условия, фильтры, именованные URL и namespaces, собственные CSS,
JavaScript и изображение.

Реализовано (ПР7): база SQLite, схема и импорт из JSON, 18 SQL-запросов,
страницы на данных из SQLite: списки, подбор игры, статистика.

Django ORM и формы пока не используются.

Планируется: переход на Django ORM,
формы создания партий, API.
