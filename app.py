from dotenv import load_dotenv
from openai import OpenAI
import os
import json
from manga_extraction import generate_image_array_from_pdfs, scale_image
from vision_analysis import encode_images_to_base64, analyze_images_with_gpt4_vision
from prompts import DRAMATIC_PROMPT, BASIC_PROMPT


load_dotenv()  # Load environment variables from .env file

def main():
    # Initialize OpenAI client with API key
    client = OpenAI()

    # List of PDF files to process
    chapters_to_recap = [82, 83, 84, 85, 86, 87, 88, 89, 90]
    pdf_files = ["naruto-v10/profiles.pdf"]+[f"naruto-v10/{chapter}.pdf" for chapter in chapters_to_recap]

    # Generate the image array from the specified PDFs
    image_array = generate_image_array_from_pdfs(pdf_files)
    print("Images have been extracted and stored in memory.")
    print("Number of images:", len(image_array))

    scaled_images = [scale_image(img) for img in image_array]


    # Encode images to base64
    base64_images = encode_images_to_base64(scaled_images)
    
    # Analyze images with GPT-4 Vision
    response = analyze_images_with_gpt4_vision(base64_images, client, BASIC_PROMPT)
    print(json.dumps(response, indent=2, default=str))

    print("\n\n\n_____________\n\n\n")
    print(response.choices[0].message.content)
    print("Total tokens:", response.usage.total_tokens)

if __name__ == "__main__":
    main()
