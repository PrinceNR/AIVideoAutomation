

class AudioController:

    def __init__(self, presentation):
        self.presentation = presentation

    def slide(self, index):
        return self.presentation.Slides(index)

    def add_audio(
        self,
        slide_index,
        audio_path,
        left=0,
        top=0,
        width=32,
        height=32
    ):
        slide = self.slide(slide_index)

        shape = slide.Shapes.AddMediaObject2(
            FileName=str(audio_path),
            LinkToFile=False,
            SaveWithDocument=True,
            Left=left,
            Top=top,
            Width=width,
            Height=height
        )

        return shape
    