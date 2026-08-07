from pathlib import Path


class RelationshipPatcher:

    VIDEO_REL = (
        "http://schemas.openxmlformats.org/"
        "officeDocument/2006/relationships/video"
    )

    AUDIO_REL = (
        "http://schemas.openxmlformats.org/"
        "officeDocument/2006/relationships/audio"
    )

    def patch(
        self,
        rels_folder: Path
    ):

        rel_files = sorted(
            rels_folder.glob("slide*.xml.rels")
        )

        for rel_file in rel_files:

            xml = rel_file.read_text(
                encoding="utf-8"
            )

            if self.VIDEO_REL not in xml:
                continue

            xml = xml.replace(
                self.VIDEO_REL,
                self.AUDIO_REL
            )

            rel_file.write_text(
                xml,
                encoding="utf-8"
            )

            print(
                f"Patched relationship: {rel_file.name}"
            )