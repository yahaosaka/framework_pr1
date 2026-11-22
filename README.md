# Система учета партий в настольные игры

Учебный проект: каталог настольных игр, игроки, история партий и рейтинг
побед. ПР9 продолжает существующий проект ПР1–ПР7 и переводит веб-слой
с ручного SQL на Django ORM.

## Запуск

Python 3.10+; команды выполняются из корня проекта.

```text
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py import_pr7
python manage.py runserver
```

В Linux/macOS активация: `source venv/bin/activate`.
Открыть http://127.0.0.1:8000/. Сервер разработки работает только локально.
Повторный импорт обновляет записи с прежними ID, поэтому выполнять его
следует до самостоятельного редактирования данных. Посторонние записи
не удаляются; состав участников импортированных партий синхронизируется.

## Страницы

| URL | Возможности |
|---|---|
| `/` | Главная страница |
| `/games/?q=Уно` | Каталог, поиск по названию |
| `/games/<id>/` | Игра и ее партии |
| `/games/search/?players=4&q=стратегия` | Подбор по числу участников, названию или жанру |
| `/matches/` | История с фильтрами, сортировкой и пагинацией |
| `/matches/<id>/` | Партия с участниками и победителем |
| `/matches/statistics/?min=1` | Агрегаты, рейтинг, жанры, популярные и несыгранные игры |

Фильтры истории: `game` (ID), `status=active|completed`,
`from=YYYY-MM-DD`, `to=YYYY-MM-DD`, `q` (название или жанр).
Сортировка: `sort=date|-date|game|duration`. Размер страницы — 5,
параметр — `page`. Ссылки сохраняют фильтры через тег `querystring`.
Некорректные параметры не вызывают 500; неизвестный ID карточки дает 404.
Текстовый поиск использует `icontains`; SQLite не обеспечивает полное
регистронезависимое сопоставление кириллицы без дополнительных расширений.

## Модели и связи

- `games.models.Game`: title (уникальное), min_players, max_players, genre.
  Ограничение базы: 2 ≤ min_players ≤ max_players ≤ 6.
- `players.models.Player`: name, email (необязательный). Это участник игры,
  а не учетная запись Django.
- `matches.models.Match`: game, match_date (DateField), duration_minutes,
  winner (необязательный ForeignKey), is_completed, players (ManyToMany).
- `matches.models.MatchPlayer`: промежуточная таблица; пара match/player
  уникальна. Ее технический ID создается Django.

Django создает первичные ключи BigAutoField. Игра и игрок защищены
`PROTECT`, пока на них ссылаются партии/участие. Удаление партии
каскадно удаляет только ее строки участия. Обратные связи:
`game.matches`, `player.matches`, `player.won_matches`.
Статус завершения согласован с наличием победителя ограничением базы.

Для операций записи применяются сервисы `matches/services.py`:
они проверяют число и уникальность участников, длительность и победителя,
используют `transaction.atomic()`. Повторное завершение отклоняется.
На сайте доступны создание и редактирование партий, изменение статуса и победителя, а также редактирование игр. Дополнительно CRUD демонстрируется командой:

```text
python manage.py orm_demo
```

Команда создает временные сущности, получает партию через get(),
завершает через update(), удаляет через delete() и откатывает транзакцию.
Прямые операции ORM не вызывают full_clean() автоматически; при своих
записях используйте сервисы или явную проверку.

## Стратегия переноса данных

Выбран второй вариант методички: прежняя `data/boardgames.sqlite`
сохраняется неизменной, миграции создают новые таблицы в `db.sqlite3`.
Исходная база открывается только для чтения. Перед переносом рекомендуется
создать резервную копию; для статичного исходного файла достаточно:

```text
python -m db.inspect_source_db
python manage.py migrate
python manage.py import_pr7 --source data/boardgames.sqlite
```

Команда проверяет целостность, внешние ключи, правила партий, сохраняет
ID и связи и записывает все в одной транзакции. Ошибка откатывает импорт.
Порядок: игры → игроки → партии → составы участников.
Для исходных данных: 6 игр, 5 игроков, 8 партий, 23 участия, 7 побед.
Новая база не включается в Git; она воспроизводится миграциями и импортом.
Исходная база ПР7 уже была отслеживаемым файлом и сохранена как источник.

Только старые модули ПР7 и одноразовый импортер читают SQLite напрямую.
Веб-представления не импортируют `db.database` и не содержат SQL.
Консольная версия `python main.py` и ее JSON-файлы сохранены без изменений;
это прежний самостоятельный контур, он не синхронизируется с ORM-базой.

## Структура и материалы ПР9

- `games/models.py`, `players/models.py`, `matches/models.py` — модели.
- `*/migrations/0001_initial.py` — воспроизводимая схема.
- `db/orm_import.py` — чтение источника и транзакционный импорт ORM.
- `matches/management/commands/` — команды импорта и CRUD.
- `games/views.py`, `matches/views.py` — запросы и представления.
- `matches/templates/matches/match_list.html` — фильтры и пагинация.
- `tests/test_orm.py` — проверки переноса, CRUD и веб-сценариев.
- [Отчет ПР9](docs/practical_09.md).
- [Как редактировать данные на сайте](docs/web_usage.md).
- [Карта ORM-запросов и демонстрация](docs/orm_queries.md).

## Проверки и выгрузка

```text
python manage.py check
python manage.py showmigrations
python manage.py makemigrations --check --dry-run
pytest -v
flake8 . --extend-exclude=venv
python manage.py orm_demo
python manage.py dumpdata games players matches --indent 2 --output orm_fixture.json
```

Fixture можно загрузить командой `python manage.py loaddata orm_fixture.json`
в чистую мигрированную базу вместо импорта из ПР7.
Тесты используют отдельную базу и не меняют рабочие данные.

Технологии: Python, Django 5.2, Django ORM, SQLite, HTML/DTL, CSS,
Bootstrap 5.3, JavaScript, pytest, pytest-django, flake8.
Автор исходного проекта — владелец репозитория
[yahaosaka/framework_pr1](https://github.com/yahaosaka/framework_pr1).
ФИО, группу и вариант для титульной части отчета укажите самостоятельно.

