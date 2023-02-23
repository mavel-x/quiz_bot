import logging

import redis
import telegram
from environs import Env
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

from quiz import QuizItem, get_random_quiz_item


logger = logging.getLogger(__name__)

welcome_msg = 'Привет! Я бот для викторины.'

new_question_btn = 'Новый вопрос'
give_up_btn = 'Сдаться'
my_score_btn = 'Мой счет'


def start(update: Update, context: CallbackContext) -> None:
    keyboard = [[new_question_btn, give_up_btn], [my_score_btn]]
    reply_markup = ReplyKeyboardMarkup(keyboard)
    update.message.reply_text(welcome_msg, reply_markup=reply_markup)


def help_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Help!')


def new_question(update: Update, context: CallbackContext) -> None:
    quiz_item = get_random_quiz_item()
    redis_connection: redis.Redis = context.bot_data['redis_connection']
    redis_connection.set(update.effective_user.id, quiz_item.as_json())
    update.message.reply_text(quiz_item.question)


def evaluate_answer(update: Update, context: CallbackContext) -> None:
    redis_connection: redis.Redis = context.bot_data['redis_connection']
    current_question = redis_connection.get(update.effective_user.id)
    print(QuizItem.from_json(current_question))


def text_handler(update: Update, context: CallbackContext):
    selection = update.message.text
    if selection == new_question_btn:
        return new_question(update, context)
    elif selection == give_up_btn:
        pass
    elif selection == my_score_btn:
        pass
    else:
        return evaluate_answer(update, context)


def main() -> None:
    env = Env()
    env.read_env()
    tg_token = env.str('TG_TOKEN')
    redis_connection = redis.Redis(
        host=env.str('REDIS_HOST'),
        port=env.int('REDIS_PORT'),
        password=env.str('REDIS_PASS'),
    )

    updater = Updater(tg_token)
    dispatcher: telegram.ext.Dispatcher = updater.dispatcher
    dispatcher.bot_data['redis_connection'] = redis_connection
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, text_handler))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    main()
