from pathlib import Path


class SlideXmlPatcher:

    def patch(
        self,
        slides_folder: Path
    ):

        slide_files = sorted(
            slides_folder.glob("slide*.xml")
        )

        for slide_file in slide_files:

            xml = slide_file.read_text(
                encoding="utf-8"
            )

            if "<a:videoFile" not in xml:
                continue

            # xml = xml.replace(
            #     "<a:videoFile",
            #     "<a:audioFile"
            # )

            # xml = xml.replace(
            #     "</a:videoFile>",
            #     "</a:audioFile>"
            # )

            slide_file.write_text(
                xml,
                encoding="utf-8"
            )

            print(
                f"Patched slide xml: {slide_file.name}"
            )
