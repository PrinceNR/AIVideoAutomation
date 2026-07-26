from dataclasses import asdict
from models.lesson import Lesson
from models.word import Word


class LessonMapper:

    @staticmethod
    def from_dict(data: dict) -> Lesson:

        words = []

        for item in data.get("words", []):

            word = Word(
                word=item.get("word", ""),
                meaning=item.get("meaning", ""),
                pronunciation=item.get("pronunciation", ""),
                part_of_speech=item.get("part_of_speech", ""),
                difficulty=item.get("difficulty", ""),
                translations=item.get("translations", {}),
                sentences=item.get("sentences", []),
                synonyms=item.get("synonyms", []),
                antonyms=item.get("antonyms", []),
                image_keywords=item.get("image_keywords", []),
                audio_path=item.get("audio_path"),
                image_path=item.get("image_path"),
            )

            words.append(word)

        return Lesson(
            title=data.get("title", ""),
            topic=data.get("topic", ""),
            words=words,
        )