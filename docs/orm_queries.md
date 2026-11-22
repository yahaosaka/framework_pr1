# Карта ORM-запросов ПР9

Все выражения встроены в страницы или в команду демонстрации.
Это различные операции, а не подсчет методов одного QuerySet.

| № | Файл и операция | Назначение |
|---|---|---|
| 1 | games/views.py: Game.objects.all() | Каталог |
| 2 | games/views.py: filter(title__icontains=query) | Строковый поиск |
| 3 | games/views.py: get_object_or_404(Game, pk=game_id) | Карточка по ID |
| 4 | games/views.py: game.matches.select_related("winner").order_by(...) | Обратная связь и связанные победители |
| 5 | games/views.py: filter(min_players__lte=count, max_players__gte=count) | Несколько условий |
| 6 | games/views.py: filter(Q(title__icontains=...) OR Q(genre__icontains=...)) | Поиск по двум полям |
| 7 | matches/views.py: select_related("game", "winner").annotate(player_count=Count("players")) | Список с JOIN и числом участников |
| 8 | matches/views.py: filter(Q(game__title__icontains=...) OR Q(game__genre__icontains=...)) | Поиск по связанным полям |
| 9 | matches/views.py: filter(game_id=game_id) | Фильтр по одной игре |
| 10 | matches/views.py: filter(is_completed=True) | Фильтр по статусу |
| 11 | matches/views.py: exclude(is_completed=True) | Исключение завершенных |
| 12 | matches/views.py: filter(match_date__gte=...) / __lte | Период |
| 13 | matches/views.py: order_by(*SORTS[sort]) | Сортировка по полю/связанной игре и дате |
| 14 | matches/views.py: select_related(...).prefetch_related("players") + get_object_or_404 | Карточка партии без N+1 |
| 15 | matches/views.py: Match.objects.aggregate(...) | Count, условный Count, Avg, Min, Max, Sum |
| 16 | matches/views.py: Game.objects.values(...).annotate(...) | Статистика по играм, включая игры без партий |
| 17 | matches/views.py: Player.objects.annotate(played=Count(...distinct=True), wins=Count(...distinct=True)) | Рейтинг без умножения строк JOIN |
| 18 | matches/views.py: values(...).annotate(...).filter(matches_count__gt=minimum) | Популярные игры, аналог HAVING |
| 19 | matches/views.py: values("genre").annotate(games_count=Count("pk")) | Группировка по жанрам |
| 20 | matches/views.py: Game.objects.exclude(matches__isnull=False) | Игры без партий |
| 21 | matches/views.py: Paginator(rows, 5).get_page(...) | COUNT и ограниченная выборка страницы |
| 22 | matches/services.py: Match.objects.filter(pk=..., is_completed=False).update(...) | Атомарное завершение |
| 23 | orm_demo.py: objects.create(), objects.get(), delete() | CRUD, транзакция отменяется |
| 24 | db/orm_import.py: update_or_create(), players.set(ids) | Повторяемый импорт с сохранением ID |

## Демонстрация

1. Выполнить migrate, import_pr7, check и showmigrations.
2. Открыть /games/?q=Уно и /games/search/?players=4&q=стратегия.
3. Открыть /matches/?game=1&status=completed&sort=-date.
4. Открыть /matches/?sort=-date, перейти на следующую страницу:
   sort остается в URL; затем проверить page=abc.
5. Открыть /matches/1/ и /matches/999999/ (404).
6. Открыть /matches/statistics/ и сравнить с 8 партиями и 7 победами.
7. Выполнить python manage.py orm_demo.
8. В shell показать разницу filter() (QuerySet) и get() (один объект
   или DoesNotExist/MultipleObjectsReturned).
9. Для схемы показать python manage.py sqlmigrate matches 0001.
10. Для выгрузки использовать dumpdata из README; loaddata проверить
    в чистой базе, не поверх рабочих записей.

select_related загружает FK через JOIN, prefetch_related получает участников
отдельным запросом. Тест карточки подтверждает два запроса независимо от
числа участников. В values()/annotate() выбираются словари с нужными полями,
поэтому дополнительный select_related там не требуется.

Источники для подготовки: [документация Django 5.2](https://docs.djangoproject.com/en/5.2/topics/db/queries/).
Задания Яндекс Практикума в личном кабинете выполняются отдельно; их
прохождение не подтверждается кодом этого репозитория.

