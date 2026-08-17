from pathlib import Path
import time

from presentation.automation.powerpoint_controller import PowerPointController


class VideoExporter:

    def export(
        self,
        pptx_path,
        output_video,
        use_timings=True,
        default_slide_duration=5,
        fps=30,
    ):

        pptx_path = Path(pptx_path).resolve()
        output_video = Path(output_video).resolve()

        # IMPORTANT:
        # Use a new filename for testing.
        if output_video.exists():
            print("Removing old video...")
            output_video.unlink()

        with PowerPointController(visible=True) as ppt:

            ppt.open_presentation(str(pptx_path))

            presentation = ppt.presentation

            print("Starting video export...")

            presentation.Windows(1).Activate()

            time.sleep(3)

            print(
                "Slide Width:",
                presentation.PageSetup.SlideWidth
            )

            print(
                "Slide Height:",
                presentation.PageSetup.SlideHeight
            )

            print(
                "Windows:",
                ppt.app.Windows.Count
            )

            print(
                "Presentations:",
                ppt.app.Presentations.Count
            )

            print("Calling CreateVideo...")

            presentation.CreateVideo(
                str(output_video),
                use_timings,
                default_slide_duration,
                1080,
                fps,
                85
            )

            print("CreateVideo() returned.")

            # PowerPoint creates the video asynchronously.
            while True:

                time.sleep(2)

                try:
                    status = presentation.CreateVideoStatus

                    print("CreateVideoStatus:", status)

                except Exception as e:

                    print(
                        "Could not read CreateVideoStatus:",
                        e
                    )

                    break

                # 0 = None
                if status == 0:
                    print("Status: None")
                    continue

                # 1 = In Progress
                if status == 1:
                    print("Status: In Progress")
                    continue

                # 2 = Queued
                if status == 2:
                    print("Status: Queued")
                    continue

                # 3 = Done
                if status == 3:

                    print("Status: DONE")

                    if output_video.exists():

                        size = output_video.stat().st_size

                        print(
                            "Final video size:",
                            size
                        )

                        if size > 0:
                            print(
                                "Video export completed successfully."
                            )

                        else:
                            print(
                                "PowerPoint reports DONE, "
                                "but the video is 0 bytes."
                            )

                    else:

                        print(
                            "PowerPoint reports DONE, "
                            "but video file does not exist."
                        )

                    break

                # 4 = Failed
                if status == 4:

                    print(
                        "Status: FAILED"
                    )

                    if output_video.exists():

                        print(
                            "Video file exists."
                        )

                        print(
                            "Video size:",
                            output_video.stat().st_size
                        )

                    break

                print(
                    "Unknown CreateVideoStatus:",
                    status
                )

                break

            print("Finished.")