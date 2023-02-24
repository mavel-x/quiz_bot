import enum
import logging

import redis
import telegram
from environs import Env
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (Updater, CommandHandler, ConversationHandler,
                          MessageHandler, Filters, CallbackContext)

from quiz import QuizItem, get_random_quiz_item


logger = logging.getLogger(__name__)

welcome_msg = 'Привет! Я бот для викторины.'
correct_answer_msg = 'Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос».'
wrong_answer_msg = 'Неправильно… Попробуешь ещё раз?'
answer_msg = ('💀 Правильный ответ:\n'
              '{}\n'
              'Удачи со следующим вопросом!')

new_question_btn = 'Новый вопрос'
give_up_btn = 'Сдаться'
my_score_btn = 'Мой счет'


class ConversationState(enum.IntEnum):
    ACTIVE_QUESTION = enum.auto()


def start(update: Update, context: CallbackContext) -> None:
    keyboard = [[new_question_btn, give_up_btn], [my_score_btn]]
    reply_markup = ReplyKeyboardMarkup(keyboard)
    update.message.reply_text(welcome_msg, reply_markup=reply_markup)


def help_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Help!')


def send_new_question(update: Update, context: CallbackContext) -> int:
    quiz_item = get_random_quiz_item()
    redis_connection: redis.Redis = context.bot_data['redis_connection']
    redis_connection.set(update.effective_user.id, quiz_item.as_json())
    update.message.reply_text(quiz_item.question)

    # FIXME debug
    print(quiz_item.answer)

    return ConversationState.ACTIVE_QUESTION


def evaluate_answer(update: Update, context: CallbackContext) -> int:
    redis_connection: redis.Redis = context.bot_data['redis_connection']
    raw_quiz_item = redis_connection.get(update.effective_user.id)
    current_quiz_item = QuizItem.from_json(raw_quiz_item)
    if update.message.text.lower() == current_quiz_item.answer.lower():
        update.message.reply_text(correct_answer_msg)
        return ConversationHandler.END
    else:
        update.message.reply_text(wrong_answer_msg)
        return ConversationState.ACTIVE_QUESTION


def give_up(update: Update, context: CallbackContext) -> int:
    redis_connection: redis.Redis = context.bot_data['redis_connection']
    raw_quiz_item = redis_connection.get(update.effective_user.id)
    current_quiz_item = QuizItem.from_json(raw_quiz_item)
    update.message.reply_text(answer_msg.format(current_quiz_item.answer))
    return send_new_question(update, context)


conv_handler = ConversationHandler(
    entry_points=[
        MessageHandler(Filters.regex(f'^{new_question_btn}$'), send_new_question),
    ],
    states={
        ConversationState.ACTIVE_QUESTION: [
            MessageHandler(Filters.regex(f'^{give_up_btn}$'), give_up),
            MessageHandler(Filters.text & ~Filters.command, evaluate_answer),
        ],
    },
    fallbacks=[CommandHandler('help', help_command)],
    allow_reentry=True,
)


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
    dispatcher.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    main()
