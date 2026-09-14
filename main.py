from datetime import date


def check_player_count(player_count):
    if player_count < 2:
        return "ошибка: минимум 2 игрока."
    elif player_count > 6:
        return "ошибка: максимум 6 игроков."
    else:
        return "количество игроков корректное."


def check_duration(duration_minutes):
    if duration_minutes <= 0:
        return "ошибка: продолжительность должна быть больше нуля."
    elif duration_minutes > 240:
        return "предупреждение: партия длится более 4 часов."
    else:
        return "продолжительность партии корректная."


def get_game_status(is_completed):
    if is_completed:
        return "партия завершена."
    else:
        return "партия продолжается."


print("==============================================")
print(" СИСТЕМА УЧЕТА ПАРТИЙ В НАСТОЛЬНЫЕ ИГРЫ")
print("==============================================")

game_name = input("введите название игры: ")
player_count = int(input("введите количество игроков: "))
duration_minutes = int(input("введите продолжительность партии в минутах: "))
winner = input("имя победителя: ")

completed_input = input("партия завершена? (да/нет): ")

if completed_input.lower() == "да":
    is_completed = True
else:
    is_completed = False


game_date = date.today()
duration_hours = duration_minutes / 60

print()
print("-------------- РЕЗУЛЬТАТ --------------")
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