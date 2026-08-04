from presentation.processors.text_processor import TextProcessor
from presentation.processors.image_processor import ImageProcessor
from presentation.processors.audio_processor import AudioProcessor


class ProcessorManager:

    def __init__(self):

        self.processors = {
            "text": TextProcessor(),
            "image": ImageProcessor(),
            "audio": AudioProcessor(),
        }

    def get(self, processor_name):

        return self.processors[processor_name]