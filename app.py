from dotenv import load_dotenv
from openai import OpenAI
from elevenlabs.client import AsyncElevenLabs
import asyncio
import json
import os
import argparse
import concurrent.futures
import time
import random

from manga_extraction import (
    extract_all_pages_as_images,
    save_important_pages,
    split_volume_into_parts,
    save_all_pages,
    extract_panels,
    scale_base64_image,
)
from vision_analysis import (
    analyze_images_with_gpt4_vision,
    detect_important_pages,
    get_important_panels,
    VISION_PRICE_PER_TOKEN,
)
from prompts import (
    DRAMATIC_PROMPT,
    BASIC_PROMPT,
    BASIC_PROMPT_WITH_CONTEXT,
    BASIC_INSTRUCTIONS,
    KEY_PAGE_IDENTIFICATION_INSTRUCTIONS,
    KEY_PANEL_IDENTIFICATION_PROMPT,
    KEY_PANEL_IDENTIFICATION_INSTRUCTIONS,
)
from citation_processing import extract_text_and_citations, extract_script
from movie_director import make_movie

from openai import APIError, RateLimitError
from tenacity import retry, stop_after_attempt, wait_exponential

load_dotenv()  # Load environment variables from .env file

def write_text_to_file(movie_script, manga, volume_number):
    output_dir = f"{manga}/v{volume_number}"
    os.makedirs(output_dir, exist_ok=True)
    output_file = f"{output_dir}/extracted_text.txt"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for segment in movie_script:
            f.write(f"Segment Text:\n{segment['text']}\n\n")
            if 'citations' in segment:
                f.write(f"Citations: {', '.join(map(str, segment['citations']))}\n\n")
            f.write("-" * 50 + "\n\n")
    
    print(f"Extracted text has been written to {output_file}")

@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=4, max=10))
def retry_api_call(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except RateLimitError as e:
        print(f"Rate limit reached. Retrying in a moment...")
        raise e
    except APIError as e:
        if "rate limit" in str(e).lower():
            print(f"API error related to rate limit. Retrying...")
            raise RateLimitError(str(e))
        raise e

async def main(volume_number, manga, text_only=False):
    # Initialize OpenAI client with API key
    client = OpenAI()
    # Only initialize ElevenLabs client if we're not in text-only mode
    narration_client = None
    if not text_only:
        narration_client = AsyncElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

    print("Extracting all pages from the volume...")
    volume_scaled_and_unscaled = extract_all_pages_as_images(
        f"{manga}/v{volume_number}/v{volume_number}.pdf"
    )
    volume = volume_scaled_and_unscaled["scaled"]
    volume_unscaled = volume_scaled_and_unscaled["full"]
    print("Total pages in volume:", len(volume))

    if len(volume) == 0:
        print("Error: No images extracted from the PDF. Please check the PDF file.")
        return

    profile_reference = extract_all_pages_as_images(f"{manga}/profile-reference.pdf")[
        "scaled"
    ]
    chapter_reference = extract_all_pages_as_images(f"{manga}/chapter-reference.pdf")[
        "scaled"
    ]

    profile_pages = []
    chapter_pages = []

    important_page_tokens = 0

    batch_size = 20

    print("Identifying important pages in the volume...")

    def process_batch(start_idx, pages):
        response = retry_api_call(
            detect_important_pages,
            profile_reference,
            chapter_reference,
            pages,
            client,
            KEY_PAGE_IDENTIFICATION_INSTRUCTIONS,
            KEY_PAGE_IDENTIFICATION_INSTRUCTIONS,
        )
        return start_idx, response

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for i in range(0, len(volume), batch_size):
            pages = volume[i : i + batch_size]
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
    NUMBER_OF_JOBS = 7
    jobs = split_volume_into_parts(
        volume, volume_unscaled, chapter_pages, NUMBER_OF_JOBS
    )
    parts = jobs["parts"]
    jobs_unscaled = jobs["unscaled_images"]
    jobs = jobs["scaled_images"]

    # Summarize the images in the first job
    response = retry_api_call(
        analyze_images_with_gpt4_vision,
        character_profiles, jobs[0], client, BASIC_PROMPT, BASIC_INSTRUCTIONS
    )
    recap = response.choices[0].message.content
    tokens = response.usage.total_tokens
    movie_script = extract_text_and_citations(
        response.choices[0].message.content, jobs[0], jobs_unscaled[0]
    )

    print("\n\n\n_____________\n\n\n")
    print(response.choices[0].message.content)

    # iterate through the rest of the jobs while adding context from previous ones
    for i, job in enumerate(jobs):
        if i == 0:
            continue
        response = retry_api_call(
            analyze_images_with_gpt4_vision,
            character_profiles,
            job,
            client,
            recap + "\n-----\n" + BASIC_PROMPT_WITH_CONTEXT,
            BASIC_INSTRUCTIONS,
        )
        recap = recap + "\n\n" + response.choices[0].message.content
        tokens += response.usage.total_tokens
        print("\n\n\n_____________\n\n\n")
        print(response.choices[0].message.content)
        movie_script = movie_script + extract_text_and_citations(
            response.choices[0].message.content, job, jobs_unscaled[i]
        )

    print("\n\n\n_____________\n\n\n")
    print("\n\n\n_____________\n\n\n")
    print("\n\n\n_____________\n\n\n")

    narration_script = extract_script(movie_script)
    print(narration_script)
    print("\n___________\n")

    extract_panels(movie_script)
    print("Extracting panels from movie script...")
    for i, segment in enumerate(movie_script):
        print(f"Processing segment {i}")
        print(f"Number of images in segment: {len(segment['images'])}")
        print(f"Number of unscaled images in segment: {len(segment['images_unscaled'])}")

        if len(segment['images']) == 0:
            print(f"Warning: No images found in segment {i}. Skipping panel extraction.")
            continue

        extract_panels(segment)

        all_panels_base64 = [
            panel for sublist in segment["panels"].values() for panel in sublist
        ]
        print(f"Number of panels extracted: {len(all_panels_base64)}")


    print("number of segments:", len(movie_script))

    for i, segment in enumerate(movie_script):
        print("segment", i, ": ", segment["text"])
        all_panels_base64 = [
            panel for sublist in segment["panels"].values() for panel in sublist
        ]
        print(len(all_panels_base64))
        print("number of panels:", len(all_panels_base64))
        print("number of images:", len(segment["images"]))

    def process_segment(segment_tuple):
        i, segment = segment_tuple
        panels = []
        for j, page in enumerate(segment["images"]):
            if "panels" in segment:
                if j not in segment["panels"]:
                    panels.append(page)
                else:
                    for panel in segment["panels"][j]:
                        panels.append(panel)
            else:
                panels.append(page)

        scaled_panels = [scale_base64_image(p) for p in panels]

        response = retry_api_call(
            get_important_panels,
            profile_reference,
            scaled_panels,
            client,
            segment["text"] + "\n________\n" + KEY_PANEL_IDENTIFICATION_PROMPT,
            KEY_PANEL_IDENTIFICATION_INSTRUCTIONS,
        )

        important_panels = response["parsed_response"]
        if not isinstance(important_panels, list):
            important_panels = []

        ip = []
        for p in important_panels:
            number = p
            if isinstance(number, str):
                if number.isdigit():
                    number = int(number)
            if not isinstance(number, int):
                continue

            if number < len(panels):
                ip.append(panels[number])

        return i, ip, response["total_tokens"]

    panel_tokens = 0
    important_panels_info = {}

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(process_segment, (i, segment))
            for i, segment in enumerate(movie_script)
        ]

        for future in concurrent.futures.as_completed(futures):
            i, ip, tokens = future.result()
            if ip:
                print("Important panels for segment", i, "exist.")
            else:
                print("No important panels for segment", i)
            movie_script[i]["important_panels"] = ip
            panel_tokens += tokens

    ELEVENLABS_PRICE_PER_CHARACTER = 0.0003
    print(
        "Tokens for extracting profiles and chapters:",
        important_page_tokens,
        " | ",
        "${:,.4f}".format(VISION_PRICE_PER_TOKEN * important_page_tokens),
    )
    print(
        "Tokens for summarization:",
        tokens,
        " | ",
        "${:,.4f}".format(VISION_PRICE_PER_TOKEN * tokens),
    )
    print(
        "Tokens for extracting important panels:",
        panel_tokens,
        " | ",
        "${:,.4f}".format(VISION_PRICE_PER_TOKEN * panel_tokens),
    )
    total_gpt_tokens = important_page_tokens + tokens + panel_tokens
    print(
        "Total GPT tokens:",
        total_gpt_tokens,
        " | ",
        "${:,.4f}".format(VISION_PRICE_PER_TOKEN * (total_gpt_tokens)),
    )
    
    if not text_only:
        narration_script = extract_script(movie_script)
        print(
            "Total elevenlabs characters:",
            len(narration_script),
            " | ",
            "${:,.4f}".format(ELEVENLABS_PRICE_PER_CHARACTER * (len(narration_script))),
        )
        print(
            "GRAND TOTAL COST",
            " | ",
            "${:,.4f}".format(
                VISION_PRICE_PER_TOKEN * (total_gpt_tokens)
                + ELEVENLABS_PRICE_PER_CHARACTER * (len(narration_script))
            ),
        )
    else:
        print(
            "GRAND TOTAL COST (GPT only)",
            " | ",
            "${:,.4f}".format(VISION_PRICE_PER_TOKEN * (total_gpt_tokens)),
        )

    if text_only:
        write_text_to_file(movie_script, manga, volume_number)
        print("Text-only mode: Skipping narration and video creation.")
    else:
        await make_movie(movie_script, manga, volume_number, narration_client)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process manga volumes.")
    parser.add_argument(
        "--manga",
        type=str,
        default="naruto",
        help="Manga name to process (default: naruto)",
    )
    parser.add_argument(
        "--volume-number",
        type=int,
        default=10,
        help="Volume number to process (default: 10)",
    )
    parser.add_argument(
        "--text-only",
        action="store_true",
        help="Output extracted text to a file instead of creating a video",
    )
    args = parser.parse_args()
    asyncio.run(main(args.volume_number, args.manga, args.text_only))
