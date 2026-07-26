from ai.content_generator import generate_vocabulary
from image_engine.image_downloader import ImageDownloader
from utils.file_manager import FileManager


class VocabularyPipeline:

    def __init__(self):

        self.file_manager = FileManager()
        self.image_downloader = ImageDownloader()

    def run(self, topic: str, count: int):

        print("Generating lesson...")

        lesson = generate_vocabulary(topic, count)

        lesson_folder = self.file_manager.create_lesson_folder(topic)

        lesson_path = lesson_folder / "lesson.json"

        self.file_manager.save_json(
            lesson,
            lesson_path
        )

        print("Downloading images...")

        # lesson_data = self.file_manager.load_json(
        #     lesson_path
        # )

        # for word in lesson_data["words"]:

        lesson = self.file_manager.load_lesson(lesson_path)

        for word in lesson.words:

            self.image_downloader.download_word_images(
                word,
                lesson_folder
            )

        print("\nPipeline completed successfully!")