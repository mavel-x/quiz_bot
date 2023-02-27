import dataclasses
from pathlib import Path

BASE_DIR = Path(__file__).parent
QUESTION_DIR = BASE_DIR / 'data/quiz-questions'


@dataclasses.dataclass
class QuizItem:
    question: str
    full_answer: str

    @property
    def answer(self):
        return self.full_answer.partition('.')[0].partition('(')[0].strip()

    def as_dict(self):
        return dataclasses.asdict(self)

    @classmethod
    def from_dotobject(cls, dotobject):
        return cls(
            question=dotobject['question'],
            full_answer=dotobject['full_answer'],
        )
