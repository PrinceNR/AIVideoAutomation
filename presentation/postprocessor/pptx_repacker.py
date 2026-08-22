from pathlib import Path
import zipfile
from presentation.presentation_logger import (
    presentation_logger as log,
)


class PptxRepacker:

    def repack(
        self,
        folder: Path,
        output_pptx: Path
    ):

        with zipfile.ZipFile(
            output_pptx,
            "w",
            zipfile.ZIP_DEFLATED
        ) as zip_file:

            for file in folder.rglob("*"):

                if file.is_file():

                    zip_file.write(
                        file,
                        file.relative_to(folder)
                    )

        log.detail(
            f"Repacked: {output_pptx}"
        )
