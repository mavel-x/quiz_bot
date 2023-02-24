import dataclasses
import json
from pathlib import Path
from random import choice


QUESTION_DIR = Path('data/quiz-questions')


@dataclasses.dataclass
class QuizItem:
    question: str
    full_answer: str

    @property
    def answer(self):
        return self.full_answer.partition('.')[0].partition('(')[0].strip()

    def as_json(self):
        return json.dumps(dataclasses.asdict(self))

    @classmethod
    def from_json(cls, json_str):
        return cls(**json.loads(json_str))

    @classmethod
    def extract_all_from_file(cls, file: Path):
        split_file = file.read_text(encoding='KOI8-R').split('\n\n')
        raw_questions = filter(lambda text: text.lstrip().startswith('Вопрос'), split_file)
        raw_answers = filter(lambda text: text.lstrip().startswith('Ответ'), split_file)
        quiz_items = []
        for raw_question, raw_answer in zip(raw_questions, raw_answers):
            question = cls.parse_from_txt(raw_question)
            answer = cls.parse_from_txt(raw_answer)
            quiz_items.append(cls(question, answer))
        return quiz_items

    @classmethod
    def random(cls):
        question_file = choice(list(QUESTION_DIR.iterdir()))
        quiz_items = cls.extract_all_from_file(question_file)
        return choice(quiz_items)

    @staticmethod
    def parse_from_txt(quiz_item: str):
        return (
            quiz_item
            .partition(':')[2]
            .strip()
            .replace('\n', ' ')
        )
