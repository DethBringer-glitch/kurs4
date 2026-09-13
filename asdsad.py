def binary_search_game():
    print("🤖 Загадайте число от 1 до 100 в уме.")
    print("⌨️ Отвечайте компьютеру символами:")
    print("   '>' — если ваше число больше")
    print("   '<' — если ваше число меньше")
    print("   '=' — если компьютер угадал\n")

    low = 1
    high = 100
    attempts = 0

    while low <= high:
        attempts += 1
        # Находим середину текущего диапазона
        guess = (low + high) // 2

        print(sub_attempt := f"Попытка №{attempts}. Моё предположение: {guess}")
        user_input = input("Ваш ответ (>, <, =): ").strip()

        if user_input == '=':
            print(f"🎉 Ура! Компьютер угадал число {guess} за {attempts} попыток!")
            break
        elif user_input == '>':
            # Если число больше, отсекаем левую (меньшую) половину
            low = guess + 1
        elif user_input == '<':
            # Если число меньше, отсекаем правую (большую) половину
            high = guess - 1
        else:
            print("❌ Неверный ввод. Используйте только '>', '<' или '='.")
            attempts -= 1  # Не считаем попытку, если ввод был ошибочным

    else:
        print("🤔 Кажется, вы где-то ошиблись в подсказках. Игра окончена.")


if __name__ == "__main__":
    binary_search_game()