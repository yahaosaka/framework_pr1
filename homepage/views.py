from django.http import HttpResponse


def page(title, content):
    """Общий HTML-каркас всех страниц проекта."""
    bootstrap = (
        "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3"
        "/dist/css/bootstrap.min.css"
    )
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title}</title>
    <link rel="stylesheet" href="{bootstrap}">
</head>
<body>
    <nav class="nav bg-dark mb-4">
        <a class="nav-link text-white" href="/">Главная</a>
        <a class="nav-link text-white" href="/games/">Игры</a>
        <a class="nav-link text-white" href="/matches/">Партии</a>
    </nav>
    <main class="container">{content}</main>
</body>
</html>"""


def index(request):
    content = """
    <h1 class="display-5">Учет партий в настольные игры</h1>
    <p class="lead">
        Справочник игр, список игроков и история сыгранных партий.
    </p>
    <p>Основные разделы:</p>
    <a href="/games/" class="btn btn-primary me-2">Игры</a>
    <a href="/matches/" class="btn btn-secondary">Партии</a>
    """
    return HttpResponse(page("Учет партий", content))


def page_not_found(request, exception):
    content = """
    <h1 class="text-danger">404 – страница не найдена</h1>
    <p>Проверьте адрес или вернитесь на главную.</p>
    <a href="/" class="btn btn-primary">На главную</a>
    """
    return HttpResponse(
        page("404 – страница не найдена", content),
        status=404,
    )
