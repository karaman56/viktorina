import os


def parse_quiz_file(file_path):
    """Читает файл с вопросами и возвращает словарь"""
    with open(file_path, "r", encoding="koi8-r") as f:
        text = f.read()

    qa = {}
    for block in text.split("Вопрос ")[1:]:
        if not block.strip():
            continue

        # Проверяем наличие двоеточия и ответа (разные варианты написания)
        if ":" not in block or "Ответ:" not in block:
            continue

        try:
            num, rest = block.split(":", 1)
            q_num = num.strip()

            # Проверяем еще раз перед разделением
            if "Ответ:" not in rest:
                continue

            q_text, a_text = rest.split("Ответ:", 1)
            question = q_text.strip()
            answer = a_text.strip()

            for marker in ["Комментарий:", "Источник:", "Автор:"]:
                if marker in answer:
                    answer = answer.split(marker)[0].strip()

            qa[q_num] = (question, answer)

        except (ValueError, IndexError) as e:
            # Пропускаем блоки с ошибками
            # Можно добавить логирование: print(f"Ошибка в файле {file_path}: {e}")
            continue

    return qa


# Использование: обрабатываем ВСЕ файлы
quiz_folder = "quiz-questions"
all_questions = {}

for filename in os.listdir(quiz_folder):
    if filename.endswith('.txt'):
        file_path = os.path.join(quiz_folder, filename)
        try:
            file_questions = parse_quiz_file(file_path)
            all_questions.update(file_questions)
            print(f"Обработан файл: {filename} - добавлено {len(file_questions)} вопросов")
        except Exception as e:
            print(f"Ошибка при обработке файла {filename}: {e}")

# Выводим результат
print(f"\nВсего вопросов собрано: {len(all_questions)}")
