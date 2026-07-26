from dataclasses import dataclass, field

from models.word import Word


@dataclass
class Lesson:

    title: str

    topic: str

    words: list[Word] = field(default_factory=list)