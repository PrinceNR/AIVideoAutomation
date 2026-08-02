from dataclasses import asdict
from models.lesson import Lesson
from models.word import Word


class LessonMapper:

    @staticmethod
    def to_dict(lesson: Lesson) -> dict:

        return asdict(lesson)
    
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

                present_sentence=item.get("present_sentence", ""),
                past_sentence=item.get("past_sentence", ""),
                future_sentence=item.get("future_sentence", ""),

                base_form=item.get("base_form", ""),
                present_form=item.get("present_form", ""),
                past_form=item.get("past_form", ""),

                synonyms=item.get("synonyms", []),
                antonyms=item.get("antonyms", []),

                image_keywords=item.get("image_keywords", []),
                search_query=item.get("search_query", ""),

                image_folder=item.get("image_folder"),
                audio_folder=item.get("audio_folder"),

                default_image=item.get("default_image"),
                default_audio=item.get("default_audio"),
            )


            words.append(word)

        return Lesson(
            title=data.get("title", ""),
            topic=data.get("topic", ""),
            words=words,
        )

