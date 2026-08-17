from pathlib import Path


class VideoEmbedder:

    def embed(
        self,
        slide,
        video_path,
        left,
        top,
        width,
        height
    ):
        video_path = str(
            Path(video_path).resolve()
        )

        media_shape = slide.Shapes.AddMediaObject2(
            video_path,
            False,   # LinkToFile
            True,    # SaveWithDocument
            left,
            top,
            width,
            height
        )

        media_shape.LockAspectRatio = False

        media_shape.Left = left
        media_shape.Top = top
        media_shape.Width = width
        media_shape.Height = height

        play_settings = (
            media_shape
            .AnimationSettings
            .PlaySettings
        )

        play_settings.PlayOnEntry = True
        play_settings.PauseAnimation = False
        play_settings.LoopUntilStopped = True
        play_settings.HideWhileNotPlaying = False

        return media_shape