from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Word:
    word: str
    meaning: str
    pronunciation: str
    part_of_speech: str
    difficulty: str

    translations: dict[str, str]

    present_sentence: str
    past_sentence: str
    future_sentence: str

    base_form: str
    present_form: str
    past_form: str

    synonyms: list[str]
    antonyms: list[str]

    image_keywords: list[str]
    search_query: str

    image_folder: str | None = None
    audio_folder: str | None = None

    default_audio: str | None = None
    default_image: str | None = None