from presentation.exporter.video_exporter import VideoExporter


def main():

    exporter = VideoExporter()

    exporter.export(
        pptx_path="research/audio_full_test.pptx",
        output_video="research/audio_full_test_1.mp4",
    )


if __name__ == "__main__":
    main()