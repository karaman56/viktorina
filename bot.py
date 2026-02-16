import os
import redis
import random
import logging
import time
from dotenv import load_dotenv
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
from telegram import ReplyKeyboardMarkup
from common import *

START, WAITING_FOR_ANSWER = range(2)


def create_keyboard():
    return ReplyKeyboardMarkup(
        [['Новый вопрос', 'Сдаться'], ['Мой счёт']],
        resize_keyboard=True
    )


def handle_start(update, context, redis_client, keyboard):
    user = update.message.from_user
    logging.info(f"Start: {user.id} {user.first_name}")
    update.message.reply_text(f'Привет, {user.first_name}!', reply_markup=keyboard)
    return START


def handle_new_question(update, context, redis_client, keyboard, all_quiz_questions):
    user = update.message.from_user
    question_number = random.choice(list(all_quiz_questions.keys()))
    question_text, _ = all_quiz_questions[question_number]
    save_user_question(user.id, question_number, redis_client, platform='tg')
    logging.info(f"New question: {user.id} -> {question_number}")
    update.message.reply_text(f'❓ Вопрос:\n{question_text}', reply_markup=keyboard)
    return WAITING_FOR_ANSWER


def handle_answer(update, context, redis_client, keyboard, all_quiz_questions):
    user = update.message.from_user
    question_number = get_user_question(user.id, redis_client, platform='tg')
    _, correct_answer = all_quiz_questions[question_number]

    if update.message.text.lower().strip() == correct_answer.lower().strip():
        current_score = get_user_score(user.id, redis_client, platform='tg') + 1
        save_user_score(user.id, current_score, redis_client, platform='tg')
        clear_user_question(user.id, redis_client, platform='tg')
        logging.info(f"Correct: {user.id} score:{current_score}")
        update.message.reply_text(f'Правильно! Счёт: {current_score}', reply_markup=keyboard)
        return START
    else:
        logging.info(f"Wrong: {user.id}")
        update.message.reply_text('❌ Неправильно', reply_markup=keyboard)
        return WAITING_FOR_ANSWER


def handle_surrender(update, context, redis_client, keyboard, all_quiz_questions):
    user = update.message.from_user
    question_number = get_user_question(user.id, redis_client, platform='tg')
    _, correct_answer = all_quiz_questions[question_number]
    clear_user_question(user.id, redis_client, platform='tg')
    logging.info(f"Surrender: {user.id}")
    update.message.reply_text(f'📖 Ответ: {correct_answer}', reply_markup=keyboard)
    return START


def handle_score(update, context, redis_client, keyboard):
    user = update.message.from_user
    current_score = get_user_score(user.id, redis_client, platform='tg')
    logging.info(f"Score check: {user.id} -> {current_score}")
    update.message.reply_text(f'🏆 Счёт: {current_score}', reply_markup=keyboard)


def main():
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
    load_dotenv()

    questions_path = os.getenv('QUIZ_QUESTIONS_PATH', 'quiz-questions')
    redis_host = os.getenv('REDIS_HOST')
    redis_port = int(os.getenv('REDIS_PORT', 18571))
    redis_password = os.getenv('REDIS_PASSWORD')
    telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')

    redis_client = init_redis_client(redis_host, redis_port, redis_password)
    all_quiz_questions = load_all_quiz_questions(questions_path)
    logging.info(f"Loaded {len(all_quiz_questions)} questions")

    keyboard = create_keyboard()

    def start_handler(update, context):
        return handle_start(update, context, redis_client, keyboard)

    def new_question_handler(update, context):
        return handle_new_question(update, context, redis_client, keyboard, all_quiz_questions)

    def answer_handler(update, context):
        return handle_answer(update, context, redis_client, keyboard, all_quiz_questions)

    def surrender_handler(update, context):
        return handle_surrender(update, context, redis_client, keyboard, all_quiz_questions)

    def score_handler(update, context):
        return handle_score(update, context, redis_client, keyboard)

    updater = Updater(telegram_bot_token, use_context=True)
    conversation_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start_handler),
            MessageHandler(Filters.text, start_handler)
        ],
        states={
            START: [
                MessageHandler(Filters.regex('Новый вопрос'), new_question_handler),
                MessageHandler(Filters.regex('Мой счёт'), score_handler),
            ],
            WAITING_FOR_ANSWER: [
                MessageHandler(Filters.regex('Сдаться'), surrender_handler),
                MessageHandler(Filters.text, answer_handler),
            ],
        },
        fallbacks=[CommandHandler('start', start_handler)],
    )

    updater.dispatcher.add_handler(conversation_handler)
    logging.info("Telegram bot started")
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()