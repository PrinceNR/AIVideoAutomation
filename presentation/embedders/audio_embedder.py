# from pathlib import Path
# from pptx.util import Emu
# from lxml import etree


# class AudioEmbedder:



#     def embed(
#         self,
#         slide,
#         audio_path: Path,
#         start_time: float = 0.0
#     ):

#         """
#         Embed an audio file into a PowerPoint slide using
#         PowerPoint COM automation.

#         start_time is currently kept for the timeline system.
#         We will handle automatic timing/playback later.
#         """

#         audio_path = Path(audio_path).resolve()

#         if not audio_path.exists():
#             raise FileNotFoundError(
#                 f"Audio file not found: {audio_path}"
#             )

#         media = slide.Shapes.AddMediaObject2(
#             FileName=str(audio_path),
#             LinkToFile=False,
#             SaveWithDocument=True,
#             Left=0,
#             Top=0,
#             Width=32,
#             Height=32
#         )

#         print(
#             f"Audio embedded: {audio_path.name}"
#         )

#         print(
#             f"  Shape: {media.Name}"
#         )

#         print(
#             f"  Type: {media.Type}"
#         )

#         print(
#             f"  ID: {media.Id}"
#         )

#         return media

# from pathlib import Path


# class AudioEmbedder:

#     MEDIA_PLAY_EFFECT = 83
#     AFTER_PREVIOUS = 3

#     def embed(
#         self,
#         slide,
#         audio_path: Path,
#         start_time: float = 0.0,
#         delay: float = 0.3
#     ):

#         audio_path = Path(audio_path).resolve()

#         if not audio_path.exists():
#             raise FileNotFoundError(
#                 f"Audio file not found: {audio_path}"
#             )

#         # ---------------------------------------------------------
#         # 1. Embed the audio into the PowerPoint slide
#         # ---------------------------------------------------------

#         media = slide.Shapes.AddMediaObject2(
#             FileName=str(audio_path),
#             LinkToFile=False,
#             SaveWithDocument=True,
#             Left=0,
#             Top=0,
#             Width=32,
#             Height=32
#         )

#         print(
#             f"Audio embedded: {audio_path.name}"
#         )

#         print(
#             f"  Shape: {media.Name}"
#         )

#         print(
#             f"  Type: {media.Type}"
#         )

#         print(
#             f"  ID: {media.Id}"
#         )

#         # ---------------------------------------------------------
#         # 2. Add the media object to PowerPoint's animation timeline
#         # ---------------------------------------------------------

#         sequence = slide.TimeLine.MainSequence

#         # effect = sequence.AddEffect(
#         #     Shape=media,
#         #     effectId=self.MEDIA_PLAY_EFFECT,
#         #     Trigger=self.AFTER_PREVIOUS
#         # )

#         effect = sequence.AddEffect(
#             media,
#             self.MEDIA_PLAY_EFFECT
#         )
#         # effect.Timing.TriggerType = self.AFTER_PREVIOUS
#         # ---------------------------------------------------------
#         # 3. Set the audio timing
#         # ---------------------------------------------------------

#         # The audio starts after the previous animation/audio.
#         effect.Timing.TriggerType = self.AFTER_PREVIOUS

#         # Gap before this audio starts.
#         effect.Timing.TriggerDelayTime = delay

#         effect.Timing.Duration = 0.001

        

#         # Gap before this audio starts.
#         effect.Timing.TriggerDelayTime = delay

#         # Make sure the media actually plays when the effect starts.
#         try:
#             effect.EffectInformation.PlaySettings.PlayOnEntry = True
#         except Exception:
#             pass

#         print(
#             f"  Animation effect created"
#         )

#         print(
#             f"  Start time: {start_time:.2f}s"
#         )

#         print(
#             f"  Delay: {delay:.2f}s"
#         )

#         return media


from pathlib import Path


class AudioEmbedder:

    MEDIA_PLAY_EFFECT = 83
    AFTER_PREVIOUS = 3

    # def embed(
    #     self,
    #     slide,
    #     audio_path: Path,
    #     start_time: float = 0.0,
    #     delay: float = 0.3
    # ):
    def embed(
        self,
        slide,
        audio_path: Path,
        start_time: float = 0.0,
        duration: float = 0.0,
        delay: float = 0.3
    ):

        audio_path = Path(audio_path).resolve()

        if not audio_path.exists():
            raise FileNotFoundError(
                f"Audio file not found: {audio_path}"
            )

        # ---------------------------------------------------------
        # 1. Embed audio
        # ---------------------------------------------------------

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

        # ---------------------------------------------------------
        # 2. Add audio to PowerPoint animation timeline
        # ---------------------------------------------------------

        sequence = slide.TimeLine.MainSequence

        effect = sequence.AddEffect(
            media,
            self.MEDIA_PLAY_EFFECT
        )

        # Play after the previous audio finishes.
        effect.Timing.TriggerType = self.AFTER_PREVIOUS

        # Small gap between audio clips.
        effect.Timing.TriggerDelayTime = delay

        # Keep the animation effect itself very short.
        # The media playback continues according to the audio.
        effect.Timing.Duration = duration

        # Make sure the media plays when its effect starts.
        try:
            effect.EffectInformation.PlaySettings.PlayOnEntry = True
        except Exception:
            pass

        print(
            "  Animation effect created"
        )

        print(
            f"  Start time: {start_time:.2f}s"
        )

        print(
            f"  Delay: {delay:.2f}s"
        )

        return media