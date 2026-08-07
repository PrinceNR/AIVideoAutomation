from pathlib import Path

from presentation.patchers.presentation_patcher import PresentationPatcher
from .pptx_unpacker import PptxUnpacker
from .pptx_repacker import PptxRepacker


class PptxPostProcessor:

    def __init__(self):

        self.unpacker = PptxUnpacker()
        self.repacker = PptxRepacker()
        self.presentation_patcher = PresentationPatcher()

    def process(
        self,
        pptx_file: Path
    ):

        temp_folder = Path("build/temp_pptx")

        self.unpacker.unpack(
            pptx_file,
            temp_folder
        )
        self.presentation_patcher.patch(
            temp_folder
        )

        self.repacker.repack(
            temp_folder,
            pptx_file
        )