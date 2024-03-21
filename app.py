from dotenv import load_dotenv
from openai import OpenAI
from elevenlabs.client import AsyncElevenLabs
import asyncio
import json
import os
import argparse
import concurrent.futures

from manga_extraction import extract_all_pages_as_images, save_important_pages, split_volume_into_parts, save_all_pages, extract_panels, scale_base64_image
from vision_analysis import analyze_images_with_gpt4_vision, detect_important_pages, get_important_panels, VISION_PRICE_PER_TOKEN 
from prompts import DRAMATIC_PROMPT, BASIC_PROMPT, BASIC_PROMPT_WITH_CONTEXT,  BASIC_INSTRUCTIONS, KEY_PAGE_IDENTIFICATION_INSTRUCTIONS, KEY_PANEL_IDENTIFICATION_PROMPT, KEY_PANEL_IDENTIFICATION_INSTRUCTIONS
from citation_processing import extract_text_and_citations, extract_script
from movie_director import make_movie
load_dotenv()  # Load environment variables from .env file

async def main(volume_number, manga):
    # Initialize OpenAI client with API key
    client = OpenAI()
    # get elevenlabs api key from dotenv
    narration_client = AsyncElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

    print("Extracting all pages from the volume...")
    volume_scaled_and_unscaled = extract_all_pages_as_images(f"{manga}/v{volume_number}/v{volume_number}.pdf")
    volume = volume_scaled_and_unscaled["scaled"]
    volume_unscaled = volume_scaled_and_unscaled["full"]
    print("Total pages in volume:", len(volume))

    profile_reference = extract_all_pages_as_images(f"{manga}/profile-reference.pdf")["scaled"]
    chapter_reference = extract_all_pages_as_images(f"{manga}/chapter-reference.pdf")["scaled"]

    profile_pages = []
    chapter_pages = [] 

    important_page_tokens = 0

    batch_size = 20

    print("Identifying important pages in the volume...")
    # Function to wrap the detect_important_pages call
    def process_batch(start_idx, pages):
        response = detect_important_pages(profile_reference, chapter_reference, pages, client,
            KEY_PAGE_IDENTIFICATION_INSTRUCTIONS, KEY_PAGE_IDENTIFICATION_INSTRUCTIONS)
        return start_idx, response

    # Using ThreadPoolExecutor to parallelize API calls
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for i in range(0, len(volume), batch_size):
            pages = volume[i:i+batch_size]
            futures.append(executor.submit(process_batch, i, pages))

        for future in concurrent.futures.as_completed(futures):
            start_idx, response = future.result()
            end_index = start_idx + batch_size - 1
            print(f"Processing pages {start_idx} to {min(end_index, len(volume)-1)}")
            
            ip = response["parsed_response"]
            print(json.dumps(ip, indent=2))
            for page in ip:
                if page["type"] == "profile":
                    profile_pages.append(page["image_index"] + start_idx)
                elif page["type"] == "chapter":
                    chapter_pages.append(page["image_index"] + start_idx)

            important_page_tokens += response["total_tokens"]

    profile_pages.sort()
    chapter_pages.sort()

    print("Total tokens to extract profiles and chapters:", important_page_tokens)
    print("\n__________\n")
    print("Profile pages:", profile_pages)
    print("Chapter pages:", chapter_pages)

    chapter_pages = [1]
    profile_pages = [0]
    print(f"{len(volume)}")
    print("\n__________\n")
    print("Saving important pages to disk for QA...")
    save_important_pages(volume, profile_pages, chapter_pages, manga, volume_number)

    character_profiles = [volume[i] for i in profile_pages]    
    jobs = split_volume_into_parts(volume, volume_unscaled, chapter_pages, 1)
    parts = jobs["parts"]
    jobs_unscaled = jobs["unscaled_images"]
    jobs = jobs["scaled_images"]

    # Summarize the images in the first job
    response = analyze_images_with_gpt4_vision(character_profiles, jobs[0], client, BASIC_PROMPT, BASIC_INSTRUCTIONS)
    recap = response.choices[0].message.content
    tokens = response.usage.total_tokens
    movie_script = extract_text_and_citations(response.choices[0].message.content, jobs[0], jobs_unscaled[0])

    print("\n\n\n_____________\n\n\n")
    print(response.choices[0].message.content)

    # iterate thrugh the rest of the jobs while adding context from previous ones
    for i, job in enumerate(jobs):
        if i == 0:
            continue
        response = analyze_images_with_gpt4_vision(character_profiles, job, client, recap + "\n-----\n" + BASIC_PROMPT_WITH_CONTEXT, BASIC_INSTRUCTIONS)
        recap = recap + "\n\n" + response.choices[0].message.content
        tokens += response.usage.total_tokens
        print("\n\n\n_____________\n\n\n")
        print(response.choices[0].message.content)
        movie_script = movie_script + extract_text_and_citations(response.choices[0].message.content, job, jobs_unscaled[i])

    print("\n\n\n_____________\n\n\n")
    print("\n\n\n_____________\n\n\n")
    print("\n\n\n_____________\n\n\n")

    narration_script = extract_script(movie_script)
    print(narration_script)
    print("\n___________\n")

    extract_panels(movie_script)

    await make_movie(movie_script, manga, volume_number, narration_client)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process manga volumes.')
    parser.add_argument('--manga', type=str, default="naruto", help='Volume number to process (default: 10)')
    parser.add_argument('--volume-number', type=int, default=10, help='Volume number to process (default: 10)')
    args = parser.parse_args()
    asyncio.run(main(args.volume_number, args.manga))

