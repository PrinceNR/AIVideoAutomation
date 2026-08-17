from ai.content_generator import generate_vocabulary
from image_engine.image_downloader import ImageDownloader
from utils.file_manager import FileManager
from audio_engine.audio_generator import AudioGenerator
from models.lesson_mapper import LessonMapper
from verification.content_verifier import ContentVerifier
from media_engine.media_planning_service import MediaPlanningService
from video_engine.video_query_planning_service import VideoQueryPlanningService
from media_engine.media_selection_service import MediaSelectionService





class VocabularyPipeline:

    def __init__(self):

        self.file_manager = FileManager()
        self.image_downloader = ImageDownloader()
        self.audio_generator = AudioGenerator()
        self.content_verifier = ContentVerifier()
        self.media_planning_service = MediaPlanningService()
        self.video_query_planning_service = VideoQueryPlanningService()
        self.media_selection_service =  MediaSelectionService()



    def run(self, topic: str, count: int, suggestions: str):

        print("Generating lesson...")

        lesson = generate_vocabulary(topic, count, suggestions)
        lesson.suggestions = suggestions

        lesson_folder = self.file_manager.create_lesson_folder(topic)
        lesson_path = lesson_folder / "lesson.json"

        lesson_dict = LessonMapper.to_dict(lesson)

        self.file_manager.save_json(
            lesson_dict,
            lesson_path
        )

        verification_result = self.content_verifier.verify(
            lesson_path
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

            self.file_manager.save_json(
                corrected_lesson_dict,
                lesson_path
            )

            print("Corrected lesson saved.")

        if not verification_result["passed"]:

            print("\nLesson contains verification errors.")
            print("Images and audio will not be generated.")

            print("\nPlease review:")
            print(
                verification_result["semantic_report"]
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


        print(
            "\nSelecting lesson media..."
        )

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

        # for word in lesson.words:
        #     self.audio_generator.generate_word_audio(
        #         word,
        #         lesson_folder
        #     )

        lesson_dict = LessonMapper.to_dict(lesson)

        self.file_manager.save_json(
            lesson_dict,
            lesson_path
        )

        print("\nPipeline completed successfully!")

        return lesson_path


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