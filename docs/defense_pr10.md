# Защита ПР10 все 30 пунктов таблицы 7.3

Проект: C:\Users\user\Desktop\framework_pr1.
Все пути далее начинаются от этой папки. Ctrl+P в VS Code открывает файл.
Это инструкция по обеим графам таблицы ПР10: где показать, что выполнить
и что объяснить. Вопросы ПР9 имеют другую нумерацию.

## Подготовка

В первом PowerShell:

~~~powershell
cd C:\Users\user\Desktop\framework_pr1
.\venv\Scripts\python.exe manage.py runserver
~~~

Сайт: http://127.0.0.1:8000/. Админка: /admin/.
Логин и пароль созданной учетной записи выданы отдельно.
Для безопасной демонстрации можно создать явно подписанные тестовые записи:

~~~powershell
.\venv\Scripts\python.exe manage.py pr10_demo
~~~

Запиши выведенные ID тестовых игры и партии на 2026-12-01.
Команда не заменяет настоящие записи и не сбрасывает статус при повторе.

Во втором PowerShell:

~~~powershell
cd C:\Users\user\Desktop\framework_pr1
.\venv\Scripts\python.exe manage.py shell
~~~

После появления >>> вводи Python:

~~~python
from datetime import date
from django.db.models import Count, F, Q
from games.models import Game
from players.models import Player
from matches.models import Match
~~~

Сейчас статусы: SCHEDULED, ACTIVE, COMPLETED, CANCELLED.
Команды shell показывают результат в терминале, не меняют код файлов.
Для выхода: exit(). После изменения модели shell открой заново.

### 1 Настройка Admin

Где: games/admin.py, players/admin.py, matches/admin.py.
В /admin/ открой Игры, Игроки и Партии. Найди «Каркассон», примени
фильтр статуса, нажми заголовок даты для сортировки.
Скажи: «list_display задает столбцы, search_fields — поиск, list_filter —
фильтры, ordering — порядок, list_per_page — размер страницы.
Поиск партий учитывает связанные game__title и players__name».

### 2 Связанные объекты

Где: games/admin.py и matches/admin.py, MatchInline.
В админке игры внизу измени длительность тестовой партии, сохрани,
затем открой саму партию. В карточке игрока показано его участие.
Скажи: «Inline позволяет редактировать связанную запись. ForeignKey
связывает партию с игрой. PROTECT защищает используемые игры и игроков,
CASCADE удаляет строки участия вместе с партией».

### 3 Изменение модели и миграция

Где: games/models.py, genre.
Временно измени max_length=100 на 150. В PowerShell:

~~~powershell
.\venv\Scripts\python.exe manage.py makemigrations games
.\venv\Scripts\python.exe manage.py migrate
~~~

Открой созданный файл. Скажи: «makemigrations создает описание,
migrate применяет его к базе». Чтобы вернуть исходное состояние,
поставь 100 и снова создай и примени миграцию. Примененные файлы не удаляй.

### 4 Перенос старых статусов

Где: matches/migrations/0003_pr10_status.py, migrate_statuses.
Покажи RunPython и условия. Скажи: «В моей области прежние флаги
is_completed и is_scheduled преобразованы в COMPLETED, SCHEDULED и
ACTIVE. Победители сохранены. CANCELLED добавлен для отмены.
Флаги пока оставлены для совместимости ПР9. Преобразование должно быть
выполнено до возможного удаления исходных полей».
Подтверждение: test_status_data_migration_preserves_completed_and_scheduled
в tests/test_pr10.py.

### 5 Работа через shell

Где: players/models.py. В shell:

~~~python
p = Player.objects.create(name="ПР10 тест чтения")
demo_id = p.pk
print(list(Player.objects.filter(pk=demo_id)))
p.name = "ПР10 измененное имя"
print(Player.objects.get(pk=demo_id).name)
p.save()
print(Player.objects.get(pk=demo_id).name)
p.delete()
~~~

Скажи: «До save новое имя только в памяти, после save — в базе».

### 6 CRUD

В shell:

~~~python
p = Player.objects.create(name="ПР10 CRUD")
demo_id = p.pk
p.name = "ПР10 CRUD обновлен"
p.save()
print(Player.objects.get(pk=demo_id).name)
p.delete()
print(Player.objects.filter(pk=demo_id).exists())
~~~

Скажи: «ORM выполняет INSERT, SELECT, UPDATE и DELETE. False подтверждает
удаление тестовой записи. Реальные связанные записи защищены on_delete».

### 7 Несколько условий

Где: matches/views.py, matches(). В shell:

~~~python
list(Match.objects.completed().filter(game_id=1, match_date__gte=date(2026, 9, 10)))
list(Match.objects.completed().filter(game_id=1, match_date__gte=date(2026, 10, 1)))
~~~

Скажи: «Условия соединены И. Новая дата исключает более ранние записи».

### 8 Связанные поля

Где: matches/views.py, game__title и game__genre. В shell:

~~~python
list(Match.objects.filter(game__title="Каркассон"))
list(Match.objects.filter(game__genre="стратегия"))
~~~

Скажи: «Двойное подчеркивание переходит к полю связанной игры.
Первый запрос по названию, второй по жанру. game_id проверяет сам ключ».

### 9 Менеджер и QuerySet

Где: matches/querysets.py и matches/models.py, objects.

~~~python
list(Match.objects.active())
list(Match.objects.cancelled())
list(Match.objects.completed())
list(Match.objects.scheduled())
list(Match.objects.for_date(date(2026, 9, 5)))
list(Match.objects.active().for_date(date(2026, 12, 1)))
~~~

Скажи: «as_manager подключает методы QuerySet к objects. Они возвращают
новые QuerySet и объединяются в цепочки, чтобы не дублировать условия».

### 10 Пользовательский ввод

Где: matches/views.py, request.GET, bounded_int, date.fromisoformat.
В браузере: /matches/?date=2026-09-05, /matches/?date=wrong,
/matches/?player=abc.
Скажи: «Дата и ID проверяются до запроса. Ошибка ввода дает сообщение
без необработанного исключения».

### 11 Сортировка

Где: matches/views.py, SORTS.
В браузере сравни /matches/?sort=date, ?sort=-date, ?sort=duration
и ?sort=wrong.
Скажи: «Разрешенные поля заданы словарем, минус меняет направление.
Неизвестный ключ заменяется на date».

### 12 values

Где: matches/views.py, начало matches(). В shell:

~~~python
list(Match.objects.values("id", "game__title", "winner__name"))
list(Match.objects.values("id", "game__title", "winner__name", "duration_minutes"))
~~~

Скажи: «values возвращает словари. Добавленное поле создает новый ключ,
а шаблон должен обращаться к реально выбранным ключам».

### 13 annotate и F

Где: matches/views.py, game_title=F("game__title"). В shell:

~~~python
list(Match.objects.annotate(game_name=F("game__title")).values("id", "game_name"))
list(Match.objects.annotate(game_name=F("game__title"), minutes_x2=F("duration_minutes") * 2).values("id", "game_name", "minutes_x2"))
~~~

Скажи: «F ссылается на поле базы, annotate добавляет вычисляемый
результат запроса. Исходные значения не меняются».

### 14 Отсутствующий объект

Где: games/views.py, get_object_or_404.
В браузере /games/1/, затем /games/by-slug/missing-game/.
Скажи: «Существующий объект открывается, отсутствующий возвращает 404».

### 15 slug и get_absolute_url

Где: games/models.py и games/urls.py. В shell:

~~~python
g = Game.objects.get(pk=1)
print(g.slug)
print(g.get_absolute_url())
~~~

Открой URL, затем в админке игры нажми «Смотреть на сайте».
Скажи: «reverse использует games:by_slug. Старые записи получили game-ID,
новые — слаг из названия. Старые адреса по ID сохранены».

### 16 GeneratedField

Где: games/models.py, is_large_group. В shell:

~~~python
g = Game.objects.create(title="ПР10 вычисляемое поле", min_players=2, max_players=4)
g.refresh_from_db()
print(g.is_large_group)
g.max_players = 6
g.save()
g.refresh_from_db()
print(g.is_large_group)
g.delete()
~~~

Скажи: «База вычисляет max_players >= 5. db_persist=True означает
хранение результата. После изменения получаю новое значение из базы».

### 17 Статистика статусов

Где: matches/views.py, statistics(), totals.
Открой /matches/statistics/. В shell:

~~~python
Match.objects.aggregate(total=Count("pk"), active=Count("pk", filter=Q(status=Match.Status.ACTIVE)), cancelled=Count("pk", filter=Q(status=Match.Status.CANCELLED)), completed=Count("pk", filter=Q(status=Match.Status.COMPLETED)))
~~~

Скажи: «Общее число включает все статусы, условные Count — конкретные.
Запланированные показаны отдельно».

### 18 Групповая статистика

Где: matches/views.py, by_genre и popular. В shell:

~~~python
list(Game.objects.values("genre").annotate(n=Count("pk")).order_by("-n", "genre"))
list(Game.objects.values("genre").annotate(n=Count("pk")).filter(n__gt=1).order_by("-n"))
~~~

Скажи: «values определяет группы, Count считает игры в жанре.
Второй запрос оставляет группы с числом больше одного, аналог HAVING».

### 19 select_related

Где: matches/views.py, match_detail.
Открой /matches/1/ → Debug Toolbar → SQL, найди JOIN с games_game и
players_player. Скажи: «Игра и победитель загружаются с партией одним
запросом. Участники — отдельным prefetch, это многие ко многим».

### 20 SQL списка

Открой /matches/?from=2026-09-01&sort=-date, перейди на другую страницу,
открой Toolbar → SQL. Покажи COUNT и запрос с LIMIT.
Скажи: «COUNT нужен для числа страниц, LIMIT/OFFSET — для текущей.
Запросы авторизации и общего счетчика ожидаемы; повторные запросы
игры для каждой строки могли бы означать N+1».

### 21 Фильтры сортировка пагинация

Где: matches/views.py и matches/templates/matches/match_list.html.
Открой /matches/?from=2026-09-01&sort=-date и нажми «Вперед».
Покажи Paginator(rows, 5) и querystring.
Скажи: «Сначала фильтрация, затем сортировка и пагинация. GET-параметры
сохраняются. Меньше записей на странице — больше страниц».

### 22 Доступность на дату

Где: games/views.py, available_games; matches/querysets.py, blocking.
Используй тестовую партию pr10_demo на 2026-12-01.
В админке поставь «Идет». Открой /games/available/?date=2026-12-01:
тестовой игры нет среди свободных. Отмени партию и обнови страницу:
игра появится.
Скажи: «При одном экземпляре active и scheduled занимают игру на день.
Cancelled и completed не занимают. Подзапрос выбирает занятые game_id,
exclude исключает их из свободных».

### 23 Контекстный процессор

Где: homepage/context_processors.py, boardgames/settings.py,
templates/base.html. Покажи project_info и регистрацию.
Открой /games/ и /matches/, покажи подвал.
Скажи: «Процессор передает site_title и games_count общему шаблону без
повторения в каждой view. Контекст view относится к отдельной странице».

### 24 TextChoices

Где: matches/models.py, Status; matches/querysets.py.
В админке измени статус тестовой партии, открой /matches/ и статистику.
Скажи: «В базе код статуса, в интерфейсе подпись. Константы Match.Status
снижают риск опечаток. Победитель нужен только для COMPLETED».

### 25 Связанные поля через values

Где: matches/views.py, values и annotate в matches().
В списке партий открой Toolbar → SQL, покажи SELECT с JOIN.
Скажи: «Названия уже выбраны запросом и находятся в словаре.
select_related здесь не нужен, связанные модельные объекты не создаются».

### 26 Пересчет после изменения

Повтори тест GeneratedField из пункта 16 либо у тестовой игры через
админку измени максимум с 4 на 6 и сохрани.
Скажи: «max_players — исходное поле, is_large_group пересчитывается
базой. Название игры в партиях получается по связи, а не дублируется».

### 27 Именованные ссылки

Где: games/urls.py, games/models.py,
games/templates/games/game_detail.html.
Покажи games:by_slug, reverse и ссылку get_absolute_url.
В браузере перейди из каталога к игре, по ссылке слага и обратно.
Скажи: «Имя и аргумент маршрута должны совпадать с reverse. Изменение
имени только в urls.py даст NoReverseMatch».

### 28 Безопасная проверка ошибки базы

Где: games/views.py, except DatabaseError.
Тест: tests/test_pr10.py, test_availability_database_error_is_readable.
PowerShell:

~~~powershell
.\venv\Scripts\python.exe -m pytest -v tests/test_pr10.py::test_availability_database_error_is_readable
~~~

Скажи: «Mock имитирует DatabaseError. База не повреждается. Пользователь
видит сообщение о повторной попытке, без технического traceback».

### 29 Проверка моделей и миграций

PowerShell:

~~~powershell
.\venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\venv\Scripts\python.exe manage.py check
.\venv\Scripts\python.exe manage.py showmigrations games players matches
~~~

Скажи: «Первая команда проверяет изменения без подготовленных миграций,
вторая конфигурацию, третья применение. При изменении модели создаю
миграцию и применяю migrate».

### 30 Автоматизированный сценарий

Где: tests/test_pr10.py, test_manager_and_availability.
Покажи исключение занятой игры и появление после отмены.
PowerShell:

~~~powershell
.\venv\Scripts\python.exe -m pytest -v tests/test_pr10.py::test_manager_and_availability
~~~

Скажи: «Тест подтверждает, что активная партия занимает игру, а отмена
освобождает. Выполняется в отдельной тестовой базе».

## Общие проверки

~~~powershell
.\venv\Scripts\python.exe manage.py check
.\venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\venv\Scripts\python.exe -m pytest -v
.\venv\Scripts\python.exe -m flake8 . --extend-exclude=venv
~~~

Не запускай import_pr7 поверх своих изменений. Удаляй только собственные
тестовые записи. После изменения модели перезапускай shell. Временные
правки схемы возвращай обратной миграцией, а не удалением примененной.
