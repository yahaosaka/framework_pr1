def bounded_int(value, minimum, maximum):
    """Не допускать переполнения SQL integer и очень длинных чисел."""
    if not value or len(value) > 10 or not value.isascii():
        return None
    try:
        number = int(value)
    except ValueError:
        return None
    return number if minimum <= number <= maximum else None
