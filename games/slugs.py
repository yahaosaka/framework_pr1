from django.utils.text import slugify

RUSSIAN = dict(zip(
    "абвгдеёжзийклмнопрстуфхцчшщъыьэюя",
    ("a", "b", "v", "g", "d", "e", "yo", "zh", "z", "i", "y", "k",
     "l", "m", "n", "o", "p", "r", "s", "t", "u", "f", "kh", "ts",
     "ch", "sh", "sch", "", "y", "", "e", "yu", "ya")))


def title_slug(title):
    return slugify("".join(RUSSIAN.get(c, c) for c in title.lower()))[:200]
