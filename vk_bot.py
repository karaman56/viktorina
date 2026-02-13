import os
import redis
import random
import logging
import time
from dotenv import load_dotenv
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.utils import get_random_id
from common import *

WAITING_STATE = 'WAITING'


def init_redis():
    client = redis.Redis(
        host=os.getenv('REDIS_HOST'),
        port=int(os.getenv('REDIS_PORT', 18571)),
        password=os.getenv('REDIS_PASSWORD'),
        decode_responses=True,
        socket_connect_timeout = 3,
        socket_timeout = 3
    )
    client.ping()
    return client


def create_keyboard():
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button('Мой счёт', color=VkKeyboardColor.POSITIVE)
    return keyboard


def handle_start(user_id, vk, keyboard):
    vk.messages.send(
        user_id=user_id,
        random_id=get_random_id(),
        keyboard=keyboard.get_keyboard(),
        message='Привет! Выберите действие:'
    )


def handle_new_question(user_id, vk, keyboard, redis_client, all_quiz_questions, user_states):
    question_number = random.choice(list(all_quiz_questions.keys()))
    question_text, _ = all_quiz_questions[question_number]
    save_user_question(user_id, question_number, redis_client, platform='vk')
    user_states[user_id] = WAITING_STATE

    vk.messages.send(
        user_id=user_id,
        random_id=get_random_id(),
        keyboard=keyboard.get_keyboard(),
        message=f'❓ Вопрос:\n{question_text}'
    )


def handle_answer(user_id, answer, vk, keyboard, redis_client, all_quiz_questions, user_states):
    question_number = get_user_question(user_id, redis_client, platform='vk')
    _, correct_answer = all_quiz_questions[question_number]

    if answer.lower().strip() == correct_answer.lower().strip():
        current_score = get_user_score(user_id, redis_client, platform='vk') + 1
        save_user_score(user_id, current_score, redis_client, platform='vk')
        clear_user_question(user_id, redis_client, platform='vk')  # ← vk префикс
        user_states[user_id] = 'START'

        vk.messages.send(
            user_id=user_id,
            random_id=get_random_id(),
            keyboard=keyboard.get_keyboard(),
            message=f'✅ Правильно! Счёт: {current_score}'
        )
    else:
        vk.messages.send(
            user_id=user_id,
            random_id=get_random_id(),
            keyboard=keyboard.get_keyboard(),
            message='❌ Неправильно'
        )


def handle_surrender(user_id, vk, keyboard, redis_client, all_quiz_questions, user_states):
    question_number = get_user_question(user_id, redis_client, platform='vk')  # ← vk префикс
    _, correct_answer = all_quiz_questions[question_number]

    clear_user_question(user_id, redis_client, platform='vk')
    user_states[user_id] = 'START'

    vk.messages.send(
        user_id=user_id,
        random_id=get_random_id(),
        keyboard=keyboard.get_keyboard(),
        message=f'📖 Ответ: {correct_answer}'
    )


def handle_score(user_id, vk, keyboard, redis_client):
    current_score = get_user_score(user_id, redis_client, platform='vk')
    vk.messages.send(
        user_id=user_id,
        random_id=get_random_id(),
        keyboard=keyboard.get_keyboard(),
        message=f'🏆 Счёт: {current_score}'
    )


def main():
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
    load_dotenv()

    questions_path = get_questions_path()
    redis_client = init_redis()
    logging.info("Redis connected")
    all_quiz_questions = load_all_quiz_questions(questions_path)
    logging.info(f"Loaded {len(all_quiz_questions)} questions")
    vk_bot_token = os.getenv('VK_BOT_TOKEN')
    keyboard = create_keyboard()
    user_states = {}
    session = vk_api.VkApi(token=vk_bot_token)
    vk = session.get_api()
    longpoll = VkLongPoll(session)

    logging.info("VK bot started")

    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            user_id = event.user_id
            text = event.text.strip()
            state = user_states.get(user_id, 'START')

            if text == 'Новый вопрос':
                handle_new_question(user_id, vk, keyboard, redis_client, all_quiz_questions, user_states)
            elif text == 'Сдаться':
                handle_surrender(user_id, vk, keyboard, redis_client, all_quiz_questions, user_states)
            elif text == 'Мой счёт':
                handle_score(user_id, vk, keyboard, redis_client)
            elif state == WAITING_STATE:
                handle_answer(user_id, text, vk, keyboard, redis_client, all_quiz_questions, user_states)
            else:
                handle_start(user_id, vk, keyboard)


if __name__ == '__main__':
    main()