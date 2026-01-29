from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

TOKEN = "8551245274:AAE7lruSmJpyZua5p37PvEp4epWi5xyj1Cs"


def start(update, context):
    update.message.reply_text('Здравствуйте!')


def echo(update, context):
    update.message.reply_text(f'Вы сказали: {update.message.text}')


def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text, echo))

    print("Бот запущен...")
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()