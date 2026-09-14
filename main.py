from datetime import date


def check_player_count(player_count):
    if player_count < 2:
        return "Ошибка: минимум 2 игрока."
    elif player_count > 6:
        return "Ошибка: максимум 6 игроков."
    else:
        return "Количество игроков корректное."


def check_duration(duration_minutes):
    if duration_minutes <= 0:
        return "Ошибка: продолжительность должна быть больше нуля."
    elif duration_minutes > 240:
        return "Предупреждение: партия длится более 4 часов."
    else:
        return "Продолжительность партии корректная."


def get_game_status(is_completed):
    if is_completed:
        return "Партия завершена."
    else:
        return "Партия продолжается."


print("==============================================")
print(" СИСТЕМА УЧЕТА ПАРТИЙ В НАСТОЛЬНЫЕ ИГРЫ")
print("==============================================")

game_name = input("Введите название игры: ")
player_count = int(input("Введите количество игроков: "))
duration_minutes = int(input("Введите продолжительность партии в минутах: "))
winner = input("Введите имя победителя: ")

completed_input = input("Партия завершена? (да/нет): ")

if completed_input.lower() == "да":
    is_completed = True
else:
    is_completed = False

game_date = date.today()
duration_hours = duration_minutes / 60

print()
print("--------------- РЕЗУЛЬТАТ ---------------")
print(f"Игра: {game_name}")
print(f"Дата партии: {game_date}")
print(f"Количество игроков: {player_count}")
print(f"Продолжительность: {duration_minutes} мин.")
print(f"Продолжительность: {duration_hours:.1f} ч.")
print(f"Победитель: {winner}")

print()
print("Проверка игроков:")
print(check_player_count(player_count))

print()
print("Проверка продолжительности:")
print(check_duration(duration_minutes))

print()
print("Статус:")
print(get_game_status(is_completed))

print("------------------------------------------")