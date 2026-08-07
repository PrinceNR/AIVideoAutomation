# from pathlib import Path
# import time

# from presentation.automation.powerpoint_controller import PowerPointController


# class VideoExporter:

#     def export(
#         self,
#         pptx_path,
#         output_video,
#         use_timings=True,
#         default_slide_duration=5,
#         fps=30,
#     ):

#         pptx_path = Path(pptx_path).resolve()
#         output_video = Path(output_video).resolve()

#         with PowerPointController(visible=True) as ppt:

#             ppt.open_presentation(str(pptx_path))

#             presentation = ppt.presentation

#             print("Starting video export...")

#             # ppt.app.ActiveWindow.ViewType = 1  # Normal View
#             presentation.Windows(1).Activate()

#             time.sleep(5)

#             print("Slide Width :", presentation.PageSetup.SlideWidth)
#             print("Slide Height:", presentation.PageSetup.SlideHeight)
#             print("Windows:", ppt.app.Windows.Count)
#             print("Presentations:", ppt.app.Presentations.Count)

#             if output_video.exists():
#                 print("Removing old video...")
#                 output_video.unlink()

#             presentation.CreateVideo(
#                 str(output_video),
#                 True,
#                 5,
#                 1080,
#                 30,
#                 85
#                 # use_timings,
#                 # default_slide_duration,
#                 # fps,
#                 # 85,
#             )
#             print("CreateVideo() returned")
#             print("Waiting 10 seconds...")
#             time.sleep(10)

#             print(output_video.exists())

#             if output_video.exists():
#                 print(output_video.stat().st_size)

#             last_size = -1
#             stable_seconds = 0

#             while True:

#                 time.sleep(1)

#                 if not output_video.exists():
#                     print("Waiting for video...")
#                     continue

#                 size = output_video.stat().st_size

#                 print(f"Video size: {size}")

#                 if size == last_size:
#                     stable_seconds += 1
#                 else:
#                     stable_seconds = 0

#                 last_size = size

#                 # file hasn't changed for 5 seconds
#                 if stable_seconds >= 5:
#                     print("Video export completed.")
#                     break

#             # while presentation.CreateVideoStatus == 1:
#             #     print("Exporting...")
#             #     time.sleep(1)
#             # while True:
#             #     status = presentation.CreateVideoStatus
#             #     print("Status:", status)

#             #     if status == 1:
#             #         time.sleep(1)
#             #         continue

#             #     if status == 2:
#             #         print("Finished")
#             #         break

#             #     if status == 3:
#             #         # raise RuntimeError("Video export failed")
#             #         print("PowerPoint reported failure.")

#             #         if output_video.exists():

#             #             print("Video exists.")

#             #             print(output_video.stat().st_size)

#             #         else:

#             #             print("No video generated.")

#             #     time.sleep(1)

#             print("Finished.")



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
                True,
                5,
                1080,
                30,
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