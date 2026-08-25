import unittest
from types import SimpleNamespace

from presentation.video_presentation_processor import (
    VideoPresentationProcessor,
)


class _UppercaseOnlyComPicture:

    def __init__(self):
        self.Name = "VOCAB_IMAGE"
        self.Left = 10
        self.Top = 20
        self.Width = 300
        self.Height = 200
        self.ZOrderPosition = 4
        self.deleted = False

    def Delete(self):
        self.deleted = True


class _Locator:

    def __init__(self, picture):
        self.picture = picture

    def find_picture(self, slide):
        return self.picture


class _MediaShape:

    Name = "candidate_video"
    Id = 20
    ZOrderPosition = 4


class _RecordingVideoEmbedder:

    def __init__(self):
        self.arguments = None
        self.media_shape = _MediaShape()

    def embed(self, **arguments):
        self.arguments = arguments
        return self.media_shape


class VideoPresentationProcessorTests(unittest.TestCase):

    def test_video_replacement_reads_uppercase_com_geometry(self):
        processor = VideoPresentationProcessor()
        picture = _UppercaseOnlyComPicture()
        embedder = _RecordingVideoEmbedder()
        slide = SimpleNamespace(
            SlideShowTransition=SimpleNamespace(AdvanceTime=7.5),
            TimeLine=SimpleNamespace(
                MainSequence=SimpleNamespace(
                    Count=0,
                    Item=lambda index: None,
                )
            ),
        )

        processor.locator = _Locator(picture)
        processor.video_embedder = embedder
        processor.video_normalizer = SimpleNamespace(
            prepare=lambda path: path
        )

        was_embedded = processor._replace_picture_with_video(
            slide=slide,
            word=SimpleNamespace(default_video="video.mp4"),
            slide_index=1,
            slide_type="vocabulary",
        )

        self.assertTrue(was_embedded)
        self.assertTrue(picture.deleted)
        self.assertEqual(
            {
                "left": embedder.arguments["left"],
                "top": embedder.arguments["top"],
                "width": embedder.arguments["width"],
                "height": embedder.arguments["height"],
            },
            {
                "left": picture.Left,
                "top": picture.Top,
                "width": picture.Width,
                "height": picture.Height,
            },
        )
        self.assertIs(embedder.arguments["slide"], slide)
        self.assertEqual(
            embedder.media_shape.Name,
            "VOCAB_IMAGE",
        )


if __name__ == "__main__":
    unittest.main()
