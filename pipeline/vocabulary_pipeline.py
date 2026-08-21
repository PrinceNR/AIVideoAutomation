from ai.content_generator import generate_vocabulary
from image_engine.image_downloader import ImageDownloader
from utils.file_manager import FileManager
from audio_engine.audio_generator import AudioGenerator
from models.lesson_mapper import LessonMapper
from verification.content_verifier import ContentVerifier
from media_engine.media_planning_service import MediaPlanningService
from video_engine.video_query_planning_service import VideoQueryPlanningService
from media_engine.media_selection_service import MediaSelectionService
from pipeline.stage1_readiness_assessor import (
    Stage1ReadinessAssessor
)





class VocabularyPipeline:

    def __init__(self):

        self.file_manager = FileManager()
        self.image_downloader = ImageDownloader()
        self.audio_generator = AudioGenerator()
        self.content_verifier = ContentVerifier()
        self.media_planning_service = MediaPlanningService()
        self.video_query_planning_service = VideoQueryPlanningService()
        self.media_selection_service =  MediaSelectionService()
        self.stage1_readiness_assessor = (
            Stage1ReadinessAssessor()
        )



    def run(self, topic: str, count: int, suggestions: str):

        lesson_folder = self.file_manager.create_lesson_folder(topic)
        lesson_path = lesson_folder / "lesson.json"

        if lesson_path.is_file():
            checkpoint_lesson = self.file_manager.load_lesson(
                lesson_path
            )

            if self._can_resume_media(checkpoint_lesson):
                print(
                    "Resuming media selection from "
                    f"checkpoint: {lesson_path}"
                )

                return self._continue_lesson(
                    lesson=checkpoint_lesson,
                    lesson_folder=lesson_folder,
                    lesson_path=lesson_path
                )

        print("Generating lesson...")

        lesson = generate_vocabulary(topic, count, suggestions)
        lesson.suggestions = suggestions

        lesson_dict = LessonMapper.to_dict(lesson)

        self.file_manager.save_json(
            lesson_dict,
            lesson_path
        )

        verification_result = self.content_verifier.verify(
            lesson_path
        )

        content_verification = (
            self._content_verification_state(
                verification_result
            )
        )

        corrected_lesson_dict = verification_result.get(
            "corrected_lesson"
        )

        if corrected_lesson_dict:

            print(
                "\nApplying DeepSeek corrected lesson..."
            )

            lesson = LessonMapper.from_dict(
                corrected_lesson_dict
            )

            lesson.content_verification = (
                content_verification
            )

            self.file_manager.save_json(
                LessonMapper.to_dict(lesson),
                lesson_path
            )

            print("Corrected lesson saved.")

        else:
            lesson.content_verification = (
                content_verification
            )

            self.file_manager.save_json(
                LessonMapper.to_dict(lesson),
                lesson_path
            )

        if not verification_result["passed"]:

            print("\nLesson contains verification errors.")
            print("Images and audio will not be generated.")

            print("\nPlease review:")
            print(
                verification_result["semantic_report"]
            )

            self._finish_stage1(
                lesson=lesson,
                lesson_folder=lesson_folder,
                lesson_path=lesson_path
            )

            return lesson_path

        print(
            "\nPlanning media for lesson..."
        )

        lesson = self.file_manager.load_lesson(
            lesson_path
        )

        self.media_planning_service.plan_lesson(
            lesson
        )

        print(
            "Media planning completed."
        )


        # -----------------------------------------
        # VIDEO QUERY PLANNING
        # -----------------------------------------

        print(
            "\nPlanning video search queries..."
        )

        self.video_query_planning_service.plan_lesson(
            lesson
        )

        print(
            "Video query planning completed."
        )


        # -----------------------------------------
        # SAVE MEDIA PLANNING DATA
        # -----------------------------------------

        lesson_dict = LessonMapper.to_dict(
            lesson
        )

        self.file_manager.save_json(
            lesson_dict,
            lesson_path
        )


        return self._continue_lesson(
            lesson=lesson,
            lesson_folder=lesson_folder,
            lesson_path=lesson_path
        )

    @staticmethod
    def _can_resume_media(lesson) -> bool:

        valid_media_types = {
            "photo",
            "illustration",
            "video"
        }

        return bool(lesson.words) and all(
            word.preferred_media in valid_media_types
            for word in lesson.words
        )

    def _continue_lesson(
        self,
        lesson,
        lesson_folder,
        lesson_path
    ):

        print("\nSelecting lesson media...")

        for word in lesson.words:

            self.media_selection_service.process_word(
                word=word,
                lesson_folder=lesson_folder
            )

            # Save progress after every word
            lesson_dict = LessonMapper.to_dict(
                lesson
            )

            self.file_manager.save_json(
                lesson_dict,
                lesson_path
            )

        self._print_media_summary(
            lesson.words
        )

        for word in lesson.words:
            self.audio_generator.generate_word_audio(
                word,
                lesson_folder
            )

            lesson_dict = LessonMapper.to_dict(
                lesson
            )

            self.file_manager.save_json(
                lesson_dict,
                lesson_path
            )

        self._finish_stage1(
            lesson=lesson,
            lesson_folder=lesson_folder,
            lesson_path=lesson_path
        )

        return lesson_path

    @staticmethod
    def _content_verification_state(
        verification_result
    ):

        return {
            "passed": bool(
                verification_result.get(
                    "passed",
                    False
                )
            ),
            "has_warnings": bool(
                verification_result.get(
                    "has_warnings",
                    False
                )
            ),
            "rule_errors": verification_result.get(
                "rule_errors",
                0
            ),
            "semantic_errors": verification_result.get(
                "semantic_errors",
                0
            ),
            "corrected_rule_errors": (
                verification_result.get(
                    "corrected_rule_errors",
                    0
                )
            )
        }

    def _finish_stage1(
        self,
        lesson,
        lesson_folder,
        lesson_path
    ):

        assessor = getattr(
            self,
            "stage1_readiness_assessor",
            None
        )

        if assessor is None:
            assessor = Stage1ReadinessAssessor()

        readiness = assessor.assess(
            lesson,
            lesson_folder
        )

        lesson.stage1_readiness = readiness

        self.file_manager.save_json(
            LessonMapper.to_dict(lesson),
            lesson_path
        )

        print(
            "\nStage 1 pipeline execution completed."
        )

        assessor.print_report(
            readiness
        )

    @staticmethod
    def _print_media_summary(words):

        labels = {
            "selected": "Selected",
            "fallback_selected": "Fallback selected",
            "media_missing": "Missing",
            "verification_unavailable": (
                "Verification unavailable"
            ),
            "error": "Errors"
        }

        counts = {
            status: 0
            for status in labels
        }
        problem_words = []

        for word in words:
            status = getattr(
                word,
                "media_status",
                None
            )

            if status not in counts:
                status = "error"

            counts[status] += 1

            if status not in (
                "selected",
                "fallback_selected"
            ):
                problem_words.append(
                    (word.word, status)
                )

        print("\nMEDIA SELECTION SUMMARY")
        print(f"Words processed: {len(words)}")

        for status, label in labels.items():
            print(f"{label}: {counts[status]}")

        if problem_words:
            print("\nProblem words:")
            for word_text, status in problem_words:
                print(f"{word_text} -> {status}")

        return counts


if __name__ == "__main__":

    pipeline = VocabularyPipeline()

    topic = input("Enter topic: ").strip()

    count = int(
        input("Enter number of words: ")
    )

    suggestions = input(
        "Enter the suggestions for the video: "
    ).strip()

    pipeline.run(
        topic=topic,
        count=count,
        suggestions=suggestions
    )
