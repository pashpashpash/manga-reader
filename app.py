from dotenv import load_dotenv
from openai import OpenAI
import json
import argparse
from manga_extraction import extract_all_pages_as_images, save_important_pages, split_volume_into_parts
from vision_analysis import analyze_images_with_gpt4_vision, detect_important_pages 
from prompts import DRAMATIC_PROMPT, BASIC_PROMPT, BASIC_PROMPT_WITH_CONTEXT,  BASIC_INSTRUCTIONS, KEY_PAGE_IDENTIFICATION_INSTRUCTIONS

load_dotenv()  # Load environment variables from .env file

def main(volume_number):
    # Initialize OpenAI client with API key
    client = OpenAI()

    volume = extract_all_pages_as_images(f"naruto/v{volume_number}/v{volume_number}.pdf")
    print("Total pages in volume:", len(volume))

    profile_reference = extract_all_pages_as_images("naruto/profile-reference.pdf")
    chapter_reference = extract_all_pages_as_images("naruto/chapter-reference.pdf")

    profile_pages = []
    chapter_pages = [] 

    important_page_tokens = 0

    batch_size = 20
    # iterate through volume batch_size pages at a time 
    for i in range(0, len(volume), batch_size):
        end_index = i + batch_size - 1
        print(f"Processing pages {i} to {min(end_index, len(volume)-1)}")  # Adjusted to avoid going out of range
        pages = volume[i:i+batch_size]
        response = detect_important_pages(profile_reference, chapter_reference, pages, client, 
            KEY_PAGE_IDENTIFICATION_INSTRUCTIONS, KEY_PAGE_IDENTIFICATION_INSTRUCTIONS)
        
        ip = response["parsed_response"]
        print(json.dumps(ip, indent=2))
        for page in ip:
            if page["type"] == "profile":
                profile_pages.append(page["image_index"] + i)
            elif page["type"] == "chapter":
                chapter_pages.append(page["image_index"] + i)

        important_page_tokens += response["total_tokens"]

    print("Total tokens to extract profiles and chapters:", important_page_tokens)
    print("\n__________\n")
    print("Profile pages:", profile_pages)
    print("Chapter pages:", chapter_pages)
    print("\n__________\n")
    print("Saving important pages to disk for QA...")
    save_important_pages(volume, profile_pages, chapter_pages, volume_number)


    character_profiles = [volume[i] for i in profile_pages]    
    jobs = split_volume_into_parts(volume, chapter_pages, 3)

    
    # Analyze images with GPT-4 Vision
    response = analyze_images_with_gpt4_vision(character_profiles, jobs[0], client, BASIC_PROMPT, BASIC_INSTRUCTIONS)
    recap = response.choices[0].message.content
    tokens = response.usage.total_tokens

    print("\n\n\n_____________\n\n\n")
    print(response.choices[0].message.content)

    # iterate thrugh the rest of the jobs
    for job in jobs[1:]:
        response = analyze_images_with_gpt4_vision(character_profiles, job, client, recap + "\n-----\n" + BASIC_PROMPT_WITH_CONTEXT, BASIC_INSTRUCTIONS)
        recap = recap + "\n\n" + response.choices[0].message.content
        tokens += response.usage.total_tokens
        print("\n\n\n_____________\n\n\n")
        print(response.choices[0].message.content)

    print("\n\n\n_____________\n\n\n")
    print(recap)
    print("\n___________\n")
    print("Total tokens to extract profiles and chapters:", important_page_tokens)
    print("Total tokens used for summarization:", tokens)
    print("Grand total tokens:", important_page_tokens + tokens)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process manga volumes.')
    parser.add_argument('--volume-number', type=int, default=10, help='Volume number to process (default: 10)')
    args = parser.parse_args()
    main(args.volume_number)

