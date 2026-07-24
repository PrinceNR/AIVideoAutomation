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

import json

from ai.content_generator import generate_vocabulary


topic = input("Topic : ")
count = int(input("Number of words : "))

data = generate_vocabulary(topic, count)

print(json.dumps(data, indent=4, ensure_ascii=False))
