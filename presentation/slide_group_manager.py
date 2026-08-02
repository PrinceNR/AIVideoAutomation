class SlideGroupManager:

    GROUP_SIZE = 4

    def get_group(
        self,
        presentation,
        word_index: int
    ):
        start = word_index * self.GROUP_SIZE

        return [
            presentation.slides[start + i]
            for i in range(self.GROUP_SIZE)
        ]