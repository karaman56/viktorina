import random
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.utils import get_random_id
from common import *


log_info("Starting VK bot...")
all_quiz_questions = load_all_quiz_questions()
user_states = {}


def create_keyboard():
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button('Мой счёт', color=VkKeyboardColor.POSITIVE)
    return keyboard


def handle_start(user_id, api, vk):
    user_info = api.users.get(user_ids=user_id)[0]
    user_states[user_id] = 'START'
    log_event(user_id, f"start - {user_info['first_name']}")

    vk.messages.send(
        user_id=user_id,
        random_id=get_random_id(),
        keyboard=create_keyboard().get_keyboard(),
        message=f'Привет, {user_info["first_name"]}! Выберите действие:'
    )


def handle_new_question(user_id, api, vk):
    if not all_quiz_questions:
        vk.messages.send(user_id=user_id, random_id=get_random_id(), message='Вопросы не загружены')
        return

    question_number = random.choice(list(all_quiz_questions.keys()))
    question_text, correct_answer = all_quiz_questions[question_number]

    save_user_question(user_id, question_number)
    user_states[user_id] = 'WAITING_FOR_ANSWER'
    log_event(user_id, "new question")

    vk.messages.send(
        user_id=user_id,
        random_id=get_random_id(),
        keyboard=create_keyboard().get_keyboard(),
        message=f'❓ Вопрос:\n{question_text}\n\nНапишите ответ:'
    )


def handle_answer(user_id, answer, api, vk):
    question_number = get_user_question(user_id)
    if not question_number:
        vk.messages.send(user_id=user_id, random_id=get_random_id(), message='Сначала получите вопрос!')
        return

    _, correct_answer = all_quiz_questions[question_number]

    if answer.lower().strip() == correct_answer.lower().strip():
        current_score = get_user_score(user_id)
        new_score = current_score + 1
        save_user_score(user_id, new_score)
        clear_user_question(user_id)
        user_states[user_id] = 'START'

        log_event(user_id, f"correct answer - score: {new_score}")
        vk.messages.send(
            user_id=user_id,
            random_id=get_random_id(),
            keyboard=create_keyboard().get_keyboard(),
            message=f'✅ Правильно! Счёт: {new_score}'
        )
    else:
        log_event(user_id, f"wrong answer: {answer[:50]}...")
        vk.messages.send(
            user_id=user_id,
            random_id=get_random_id(),
            keyboard=create_keyboard().get_keyboard(),
            message='❌ Неправильно'
        )


def handle_surrender(user_id, api, vk):
    question_number = get_user_question(user_id)
    if not question_number:
        vk.messages.send(user_id=user_id, random_id=get_random_id(), message='Нет активного вопроса')
        return

    _, correct_answer = all_quiz_questions[question_number]
    clear_user_question(user_id)
    user_states[user_id] = 'START'

    log_event(user_id, "surrendered")
    vk.messages.send(
        user_id=user_id,
        random_id=get_random_id(),
        keyboard=create_keyboard().get_keyboard(),
        message=f'📖 Ответ: {correct_answer}'
    )


def handle_score(user_id, api, vk):
    score = get_user_score(user_id)
    log_event(user_id, f"check score: {score}")
    vk.messages.send(
        user_id=user_id,
        random_id=get_random_id(),
        keyboard=create_keyboard().get_keyboard(),
        message=f'🏆 Счёт: {score}'
    )


def process_message(event, api, vk):
    user_id = event.user_id
    text = event.text.strip()
    state = user_states.get(user_id, 'START')

    log_event(user_id, f"message: {text} (state: {state})")

    if text == 'Новый вопрос':
        handle_new_question(user_id, api, vk)
    elif text == 'Сдаться':
        handle_surrender(user_id, api, vk)
    elif text == 'Мой счёт':
        handle_score(user_id, api, vk)
    elif state == 'WAITING_FOR_ANSWER':
        handle_answer(user_id, text, api, vk)
    else:
        handle_start(user_id, api, vk)


def main():
    try:
        session = vk_api.VkApi(token=VK_BOT_TOKEN)
        api = session.get_api()
        longpoll = VkLongPoll(session)

        log_info("VK bot started, listening...")

        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                try:
                    process_message(event, api, api)
                except Exception as e:
                    log_error(f"Processing error: {e}")
                    try:
                        api.messages.send(
                            user_id=event.user_id,
                            random_id=get_random_id(),
                            message='Ошибка обработки'
                        )
                    except:
                        pass
    except Exception as e:
        log_error(f"VK bot fatal error: {e}")


if __name__ == '__main__':
    main()