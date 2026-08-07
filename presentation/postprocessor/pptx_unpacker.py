from pathlib import Path
import shutil
import zipfile


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

        print(
            f"Unpacked: {pptx_file}"
        )