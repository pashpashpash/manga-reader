from dotenv import load_dotenv
from openai import OpenAI
import json
from manga_extraction import extract_pages_images
from vision_analysis import analyze_images_with_gpt4_vision
from prompts import DRAMATIC_PROMPT, BASIC_PROMPT, BASIC_PROMPT_WITH_CONTEXT,  BASIC_INSTRUCTIONS

load_dotenv()  # Load environment variables from .env file

def main():
    # Initialize OpenAI client with API key
    client = OpenAI()

    # List of PDF files to process
    chapters_to_recap = [82, 83, 84]
   
    base64_images = extract_pages_images(chapters_to_recap)
    
    # Analyze images with GPT-4 Vision
    response = analyze_images_with_gpt4_vision(base64_images, client, BASIC_PROMPT, BASIC_INSTRUCTIONS)
    recap = response.choices[0].message.content
    tokens = response.usage.total_tokens

    print("\n\n\n_____________\n\n\n")
    print(response.choices[0].message.content)
    print("Total tokens:", tokens)

    chapters_to_recap = [85, 86, 87]

    base64_images = extract_pages_images(chapters_to_recap)
    response = analyze_images_with_gpt4_vision(base64_images, client, recap + "\n-----\n" + BASIC_PROMPT_WITH_CONTEXT, BASIC_INSTRUCTIONS)
    recap = recap + "\n\n" + response.choices[0].message.content
    tokens += response.usage.total_tokens

    print("\n\n\n_____________\n\n\n")
    print(response.choices[0].message.content)
    print("Total tokens:", tokens)


    chapters_to_recap = [88, 89, 90]

    base64_images = extract_pages_images(chapters_to_recap)
    response = analyze_images_with_gpt4_vision(base64_images, client, recap + "\n-----\n" + BASIC_PROMPT_WITH_CONTEXT, BASIC_INSTRUCTIONS)
    recap = recap + "\n\n" + response.choices[0].message.content
    tokens += response.usage.total_tokens

    print("\n\n\n_____________\n\n\n")
    print(response.choices[0].message.content)
    print("Total tokens:", tokens)

    print("\n\n\n_____________\n\n\n")
    print(recap)


if __name__ == "__main__":
    main()
