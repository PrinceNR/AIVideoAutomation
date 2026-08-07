from pathlib import Path
import zipfile


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

        print(
            f"Repacked: {output_pptx}"
        )