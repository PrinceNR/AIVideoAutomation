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

    video_search_queries: list[str] = field (default_factory=list)

    image_folder: str | None = None
    audio_folder: str | None = None

    default_audio: str | None = None
    default_image: str | None = None

    preferred_media: str | None = None
    media_reason: str | None = None
    requires_motion: bool = False

    media_type: str | None = None
    video_folder: str | None = None
    default_video: str | None = None

    def get_audio(
        self,
        audio_name: str
    ) -> Path | None:

        if self.audio_folder is None:
            return None

        audio_path = Path(self.audio_folder) / f"{audio_name}.mp3"

        if audio_path.exists():
            return audio_path

        return None