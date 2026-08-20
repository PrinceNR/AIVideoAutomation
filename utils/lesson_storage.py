from models.lesson_mapper import (
    LessonMapper
)


class LessonStorage:

    def __init__(
        self,
        file_manager
    ):
        self.file_manager = file_manager

    def save(
        self,
        lesson,
        lesson_path
    ):

        lesson_dict = (
            LessonMapper.to_dict(
                lesson
            )
        )

        self.file_manager.save_json(
            lesson_dict,
            lesson_path
        )

        return lesson_dict