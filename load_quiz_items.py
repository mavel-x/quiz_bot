import logging
from pathlib import Path

from environs import Env
import redisworks

from quiz_items import QuizItem


logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent


def parse_quiz_item_from_txt(quiz_item: str):
    return (
        quiz_item
        .partition(':')[2]
        .strip()
        .replace('\n', ' ')
    )


def read_quiz_items_from_file(file: Path):
    split_file = file.read_text(encoding='KOI8-R').split('\n\n')
    raw_questions = filter(lambda text: text.lstrip().startswith('Вопрос'), split_file)
    raw_answers = filter(lambda text: text.lstrip().startswith('Ответ'), split_file)
    quiz_items = []
    for raw_question, raw_answer in zip(raw_questions, raw_answers):
        quiz_items.append(
            QuizItem(
                question=parse_quiz_item_from_txt(raw_question),
                full_answer=parse_quiz_item_from_txt(raw_answer),
            ))
    return quiz_items


def get_quiz_items_from_files(files: list[Path], limit: int):
    quiz_items = []
    for file in files:
        quiz_items.extend(read_quiz_items_from_file(file))
        if len(quiz_items) > limit:
            return quiz_items[:limit]
    return quiz_items


def load_quiz_items_to_redis(quiz_items: list, redis: redisworks.Root):
    try:
        for item_num, quiz_item in enumerate(quiz_items, start=1):
            redis[f'quiz_item_{item_num}'] = quiz_item.as_dict()
            logger.info(f'Uploaded question {item_num}.')
    except KeyboardInterrupt:
        redis.available_questions = item_num - 1
    else:
        redis.available_questions = item_num
    logger.info('Finished uploading.')


def main():
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.DEBUG
    )

    env = Env()
    env.read_env()
    question_limit = env.int('QUESTION_LIMIT', 1_000)
    question_dir = BASE_DIR / env.path('QUESTION_DIR', BASE_DIR / 'data/quiz-questions')

    redis = redisworks.Root(
        host=env.str('REDIS_HOST'),
        port=env.int('REDIS_PORT'),
        password=env.str('REDIS_PASS'),
    )

    question_files = [file for file in question_dir.iterdir() if file.suffix == '.txt']
    quiz_items = get_quiz_items_from_files(question_files, limit=question_limit)
    load_quiz_items_to_redis(quiz_items, redis)


if __name__ == '__main__':
    main()
