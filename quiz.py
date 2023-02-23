import dataclasses
import json
from pathlib import Path
from random import choice
from pprint import pprint


QUESTION_DIR = Path('data/quiz-questions')


@dataclasses.dataclass
class QuizItem:
    question: str
    answer: str

    def as_json(self):
        return json.dumps(dataclasses.asdict(self))

    @classmethod
    def from_json(cls, json_str):
        return cls(**json.loads(json_str))


def format_quiz_item(quiz_item: str):
    return (
        quiz_item
        .partition(':')[2]
        .strip()
        .replace('\n', ' ')
    )


def extract_quiz_items_from_file(file: Path):
    split_file = file.read_text(encoding='KOI8-R').split('\n\n')
    questions = filter(lambda text: text.lstrip().startswith('Вопрос'), split_file)
    answers = filter(lambda text: text.lstrip().startswith('Ответ'), split_file)
    return [QuizItem(format_quiz_item(question), format_quiz_item(answer))
            for question, answer in zip(questions, answers)]


def get_random_quiz_item():
    question_file = choice(list(QUESTION_DIR.iterdir()))
    quiz_items = extract_quiz_items_from_file(question_file)
    return choice(quiz_items)


def main():
    pprint(get_random_quiz_item())


if __name__ == '__main__':
    main()
