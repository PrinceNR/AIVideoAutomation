from pathlib import Path
from pptx.util import Emu
from lxml import etree


class AudioEmbedder:



    def embed(
        self,
        slide,
        audio_path: Path,
        start_time: float = 0.0
    ):

        """
        Embed an audio file into a PowerPoint slide using
        PowerPoint COM automation.

        start_time is currently kept for the timeline system.
        We will handle automatic timing/playback later.
        """

        audio_path = Path(audio_path).resolve()

        if not audio_path.exists():
            raise FileNotFoundError(
                f"Audio file not found: {audio_path}"
            )

        media = slide.Shapes.AddMediaObject2(
            FileName=str(audio_path),
            LinkToFile=False,
            SaveWithDocument=True,
            Left=0,
            Top=0,
            Width=32,
            Height=32
        )

        print(
            f"Audio embedded: {audio_path.name}"
        )

        print(
            f"  Shape: {media.Name}"
        )

        print(
            f"  Type: {media.Type}"
        )

        print(
            f"  ID: {media.Id}"
        )

        return media

        # audio_path = Path(audio_path).resolve()

        # print(
        #     f"Embedding audio: {audio_path.name}"
        # )

        # shape = slide.Shapes.AddMediaObject2(
        #     FileName=str(audio_path),
        #     LinkToFile=False,
        #     SaveWithDocument=True,
        #     Left=0,
        #     Top=0,
        #     Width=32,
        #     Height=32
        # )

        # print(
        #     f"Audio embedded successfully: {shape.Name}"
        # )

        # return shape

        # try:

        #     picture = slide.shapes.add_movie(
        #         movie_file=str(audio_path),

        #         left=Emu(0),
        #         top=Emu(0),

        #         width=Emu(1),
        #         height=Emu(1),

        #         mime_type="audio/mpeg"
        #     )
        #     print("=" * 80)
        #     print(etree.tostring(
        #         picture._element,
        #         pretty_print=True,
        #         encoding="unicode"
        #     ))
        #     print("=" * 80)

        #     print(
        #         f"Embedded: {audio_path}"
        #     )

        # except Exception as e:

        #     print(
        #         "Embedding failed:",
        #         e
        #     )