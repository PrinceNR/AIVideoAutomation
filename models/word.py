from dataclasses import dataclass, field


@dataclass
class Word:

    word: str

    meaning: str

    pronunciation: str

    part_of_speech: str

    difficulty: str

    translations: dict[str, str] = field(default_factory=dict)

    sentences: list[str] = field(default_factory=list)

    synonyms: list[str] = field(default_factory=list)

    antonyms: list[str] = field(default_factory=list)

    image_keywords: list[str] = field(default_factory=list)

    audio_path: str | None = None

    image_path: str | None = None