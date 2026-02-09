import random
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
from telegram import ReplyKeyboardMarkup
from common import *


log_info("Starting Telegram bot...")
all_quiz_questions = load_all_quiz_questions()


START, WAITING_FOR_ANSWER = range(2)

keyboard = ReplyKeyboardMarkup([['Новый вопрос', 'Сдаться'], ['Мой счёт']], resize_keyboard=True)


def handle_start(update, context):
    user = update.message.from_user
    if get_user_score(user.id) == 0:
        save_user_score(user.id, 0)

    log_event(user.id, f"start - {user.first_name}")
    update.message.reply_text(f'Привет, {user.first_name}!', reply_markup=keyboard)
    return START


def handle_new_question(update, context):
    user = update.message.from_user

    if not all_quiz_questions:
        update.message.reply_text('Вопросы не загружены')
        return START

    question_number = random.choice(list(all_quiz_questions.keys()))
    question_text, correct_answer = all_quiz_questions[question_number]

    save_user_question(user.id, question_number)
    log_event(user.id, "new question")

    update.message.reply_text(f'❓ Вопрос:\n{question_text}', reply_markup=keyboard)
    return WAITING_FOR_ANSWER


def handle_answer(update, context):
    user = update.message.from_user
    user_answer = update.message.text

    question_number = get_user_question(user.id)
    if not question_number:
        update.message.reply_text('Сначала получите вопрос!', reply_markup=keyboard)
        return START

    _, correct_answer = all_quiz_questions[question_number]

    if user_answer.lower().strip() == correct_answer.lower().strip():
        current_score = get_user_score(user.id)
        new_score = current_score + 1
        save_user_score(user.id, new_score)
        clear_user_question(user.id)

        log_event(user.id, f"correct answer - score: {new_score}")
        update.message.reply_text(f'Правильно! Счёт: {new_score}', reply_markup=keyboard)
        return START
    else:
        log_event(user.id, f"wrong answer: {user_answer[:50]}...")
        update.message.reply_text(' Неправильно', reply_markup=keyboard)
        return WAITING_FOR_ANSWER


def handle_surrender(update, context):
    user = update.message.from_user

    question_number = get_user_question(user.id)
    if not question_number:
        update.message.reply_text('Нет активного вопроса', reply_markup=keyboard)
        return START

    _, correct_answer = all_quiz_questions[question_number]
    clear_user_question(user.id)

    log_event(user.id, "surrendered")
    update.message.reply_text(f' Ответ: {correct_answer}', reply_markup=keyboard)
    return START


def handle_score(update, context):
    user = update.message.from_user
    score = get_user_score(user.id)

    log_event(user.id, f"check score: {score}")
    update.message.reply_text(f'🏆 Счёт: {score}', reply_markup=keyboard)
    return None


def main():
    try:
        updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
        dispatcher = updater.dispatcher

        conv_handler = ConversationHandler(
            entry_points=[
                MessageHandler(Filters.text & ~Filters.command, handle_start),
                CommandHandler('start', handle_start)
            ],
            states={
                START: [
                    MessageHandler(Filters.regex('Новый вопрос'), handle_new_question),
                    MessageHandler(Filters.regex('Мой счёт'), handle_score),
                ],
                WAITING_FOR_ANSWER: [
                    MessageHandler(Filters.regex('Сдаться'), handle_surrender),
                    MessageHandler(Filters.text & ~Filters.command, handle_answer),
                ],
            },
            fallbacks=[CommandHandler('cancel', handle_start)],
        )

        dispatcher.add_handler(conv_handler)
        log_info("Telegram bot started")
        updater.start_polling()
        updater.idle()
    except Exception as e:
        log_error(f"Telegram bot fatal error: {e}")


if __name__ == '__main__':
    main()