import enum
import logging
import random
from pathlib import Path

import redisworks
import telegram
from environs import Env
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (Updater, CommandHandler, ConversationHandler,
                          MessageHandler, Filters, CallbackContext)

import bot_strings
from quiz_items import QuizItem

logger = logging.getLogger(Path(__file__).stem)


class ConversationState(enum.IntEnum):
    ACTIVE_QUESTION = enum.auto()


def start(update: Update, context: CallbackContext) -> None:
    keyboard = [[bot_strings.new_question_btn, bot_strings.give_up_btn]]
    reply_markup = ReplyKeyboardMarkup(keyboard)
    update.message.reply_text(bot_strings.welcome_msg, reply_markup=reply_markup)


def help_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Help!')


def send_new_question(update: Update, context: CallbackContext) -> int:
    redis: redisworks.Root = context.bot_data['redis']
    question_id = random.randrange(redis.available_questions + 1)
    redis[f'tg_user_{update.effective_user.id}'] = question_id
    quiz_item = QuizItem.from_dotobject(
        redis[f'quiz_item_{question_id}']
    )
    update.message.reply_text(quiz_item.question)
    logger.debug(f'Answer: {quiz_item.answer}')
    return ConversationState.ACTIVE_QUESTION


def evaluate_answer(update: Update, context: CallbackContext) -> int:
    redis: redisworks.Root = context.bot_data['redis']
    current_question_id = redis[f'tg_user_{update.effective_user.id}']
    current_quiz_item = QuizItem.from_dotobject(redis[f'quiz_item_{current_question_id}'])
    if update.message.text.lower() == current_quiz_item.answer.lower():
        update.message.reply_text(bot_strings.correct_answer_msg)
        return ConversationHandler.END
    else:
        update.message.reply_text(bot_strings.wrong_answer_msg)
        return ConversationState.ACTIVE_QUESTION


def give_up(update: Update, context: CallbackContext) -> int:
    redis: redisworks.Root = context.bot_data['redis']
    current_question_id = redis[f'tg_user_{update.effective_user.id}']
    current_quiz_item = QuizItem.from_dotobject(redis[f'quiz_item_{current_question_id}'])
    update.message.reply_text(bot_strings.answer_msg.format(current_quiz_item.full_answer))
    return send_new_question(update, context)


conv_handler = ConversationHandler(
    entry_points=[
        MessageHandler(Filters.regex(f'^{bot_strings.new_question_btn}$'), send_new_question),
    ],
    states={
        ConversationState.ACTIVE_QUESTION: [
            MessageHandler(Filters.regex(f'^{bot_strings.give_up_btn}$'), give_up),
            MessageHandler(Filters.text & ~Filters.command, evaluate_answer),
        ],
    },
    fallbacks=[CommandHandler('help', help_command)],
    allow_reentry=True,
)


def main() -> None:
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.DEBUG
    )

    env = Env()
    env.read_env()
    tg_token = env.str('TG_TOKEN')
    redis = redisworks.Root(
        host=env.str('REDIS_HOST'),
        port=env.int('REDIS_PORT'),
        password=env.str('REDIS_PASS'),
    )

    updater = Updater(tg_token)
    dispatcher: telegram.ext.Dispatcher = updater.dispatcher
    dispatcher.bot_data['redis'] = redis
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
