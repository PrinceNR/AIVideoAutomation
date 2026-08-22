from pathlib import Path
import shutil
import zipfile
from presentation.presentation_logger import (
    presentation_logger as log,
)


class PptxUnpacker:

    def unpack(
        self,
        pptx_file: Path,
        output_folder: Path
    ):

        if output_folder.exists():

            shutil.rmtree(output_folder)

        output_folder.mkdir(parents=True)

        with zipfile.ZipFile(
            pptx_file,
            "r"
        ) as zip_file:

            zip_file.extractall(
                output_folder
            )

        log.detail(
            f"Unpacked: {pptx_file}"
        )
