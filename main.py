# import os
# from openai import OpenAI
# from dotenv import load_dotenv
# from google import genai


# Load the .env file
# load_dotenv()

# Get the API key
# api_key = os.getenv("OPENAI_API_KEY")
# api_key = os.getenv("GEMINI_API_KEY")

# Create OpenAI client
# client = OpenAI(api_key=api_key)
# client = genai.Client(api_key=api_key)

# for model in client.models.list():
    # print(model.name)


# topic = input("Enter a topic: ")

# prompt = f"""
# Generate 10 English vocabulary words for the topic '{topic}'.

# Return only the words.


# """
# Format:

# [
#   {{
#     "word": "",
#     "meaning": ""
#   }}
# ]

# response = client.chat.completions.create(
#     model="gemini-2.5-flash",
#     messages=[
#         {
#             "role": "user",
#             "content": prompt
#         }
#     ]
# )

# response = client.models.generate_content(
#     model="gemini-2.5-flash",
#     contents=prompt
# )

# print(response.choices[0].message.content)

# response = client.models.generate_content(
#     model="gemini-2.5-flash",
#     contents=prompt
# )

# print("\nGenerated Words:\n")
# print(response.text)

# from ai.content_generator import generate_vocabulary

# topic = input("Enter Topic : ")
# count = int(input("Number of words : "))

# generate_vocabulary(topic, count)

# import json

# from ai.content_generator import generate_vocabulary


# topic = input("Topic : ")
# count = int(input("Number of words : "))

# data = generate_vocabulary(topic, count)

# print(json.dumps(data, indent=4, ensure_ascii=False))


# import json

# from ai.content_generator import generate_vocabulary
# from utils.file_manager import FileManager
# from image_engine.image_downloader import ImageDownloader


# topic = input("Topic : ")
# count = int(input("Number of words : "))

# data = generate_vocabulary(topic, count)

# file_manager = FileManager()

# lesson_folder = file_manager.create_lesson_folder(topic)

# json_file = lesson_folder / "lesson.json"

# file_manager.save_json(data, json_file)

# downloader = ImageDownloader()

# lesson = file_manager.load_json(json_file)

# for word in lesson["words"]:

#     downloader.download_word_images(
#         word["word"],
#         lesson_folder
#     )

# print("\nLesson saved successfully!")

# print(json.dumps(data, indent=4, ensure_ascii=False))


# from pipeline.vocabulary_pipeline import VocabularyPipeline

# topic = input("Topic: ")

# count = int(input("Number of words: "))

# pipeline = VocabularyPipeline()

# pipeline.run(topic, count)


from pipeline.vocabulary_pipeline import VocabularyPipeline
from pipeline.presentation_pipeline import PresentationPipeline
from pipeline.video_pipeline import VideoPipeline


def main():

    print("\n========================================")
    print("VOCABULARY VIDEO AUTOMATION")
    print("========================================")

    topic = input("Enter topic: ").strip()

    count = int(
        input("Enter number of words: ")
    )

    print("\nStarting full pipeline...")

    # ---------------------------------------------
    # Stage 1
    # Lesson + Images + Audio
    # ---------------------------------------------

    vocabulary_pipeline = VocabularyPipeline()

    vocabulary_pipeline.run(
        topic=topic,
        count=count
    )

    # ---------------------------------------------
    # Stage 2
    # Presentation
    # ---------------------------------------------

    presentation_pipeline = PresentationPipeline()

    presentation_path = presentation_pipeline.run()

    # ---------------------------------------------
    # Stage 3
    # Video
    # ---------------------------------------------

    video_pipeline = VideoPipeline()

    video_path = video_pipeline.run()

    # ---------------------------------------------
    # Completed
    # ---------------------------------------------

    print("\n========================================")
    print("FULL PIPELINE COMPLETED")
    print("========================================")

    print(f"Topic: {topic}")
    print(f"Presentation: {presentation_path}")
    print(f"Video: {video_path}")


if __name__ == "__main__":
    main()
