import logging
import random
from pathlib import Path

import vk_api
import redisworks
from environs import Env
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id

import bot_strings
from quiz_items import QuizItem

logger = logging.getLogger(Path(__file__).stem)


def get_quiz_keyboard():
    keyboard = VkKeyboard()
    keyboard.add_button(bot_strings.new_question_btn, color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button(bot_strings.give_up_btn, color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()


def send_new_question(event: vk_api.longpoll.Event, vk_client: vk_api.vk_api.VkApiMethod,
                      redis: redisworks.Root):
    question_id = random.randrange(redis.available_questions + 1)
    redis[f'vk_user_{event.user_id}'] = question_id
    quiz_item = QuizItem.from_dotobject(
        redis[f'quiz_item_{question_id}']
    )
    vk_client.messages.send(
        user_id=event.user_id,
        message=quiz_item.question,
        random_id=get_random_id(),
        keyboard=get_quiz_keyboard(),
    )
    logger.debug(f'Answer: {quiz_item.answer}')


def evaluate_answer(event: vk_api.longpoll.Event, vk_client: vk_api.vk_api.VkApiMethod,
                    redis: redisworks.Root):
    current_question_id = redis[f'vk_user_{event.user_id}']
    current_quiz_item = QuizItem.from_dotobject(redis[f'quiz_item_{current_question_id}'])
    if event.text.lower() == current_quiz_item.answer.lower():
        vk_client.messages.send(
            user_id=event.user_id,
            message=bot_strings.correct_answer_msg,
            random_id=get_random_id(),
            keyboard=get_quiz_keyboard(),
        )
    else:
        vk_client.messages.send(
            user_id=event.user_id,
            message=bot_strings.wrong_answer_msg,
            random_id=get_random_id(),
            keyboard=get_quiz_keyboard(),
        )


def give_up(event: vk_api.longpoll.Event, vk_client: vk_api.vk_api.VkApiMethod,
            redis: redisworks.Root):
    current_question_id = redis[f'vk_user_{event.user_id}']
    current_quiz_item = QuizItem.from_dotobject(redis[f'quiz_item_{current_question_id}'])
    vk_client.messages.send(
        user_id=event.user_id,
        message=bot_strings.answer_msg.format(current_quiz_item.full_answer),
        random_id=get_random_id(),
        keyboard=get_quiz_keyboard(),
    )
    return send_new_question(event, vk_client, redis)


def handle_message(event: vk_api.longpoll.Event, vk_client: vk_api.vk_api.VkApiMethod,
                   redis: redisworks.Root):
    if event.text == bot_strings.new_question_btn:
        return send_new_question(event, vk_client, redis)
    elif event.text == bot_strings.give_up_btn:
        return give_up(event, vk_client, redis)
    else:
        return evaluate_answer(event, vk_client, redis)


def main():
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.DEBUG
    )

    env = Env()
    env.read_env()
    vk_token = env.str('VK_TOKEN')

    redis = redisworks.Root(
        host=env.str('REDIS_HOST'),
        port=env.int('REDIS_PORT'),
        password=env.str('REDIS_PASS'),
    )

    vk_session = vk_api.VkApi(token=vk_token)
    vk_client = vk_session.get_api()

    longpoll = VkLongPoll(vk_session)
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            handle_message(event, vk_client, redis)


if __name__ == "__main__":
    main()
