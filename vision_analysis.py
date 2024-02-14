import base64
import openai
import os

def encode_images_to_base64(image_array):
    base64_images = []
    for img_bytes in image_array:
        base64_images.append(base64.b64encode(img_bytes).decode('utf-8'))
    return base64_images


#image object:
# {
#           "type": "image_url",
#           "image_url": {
#             "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg",
#             "detail": "high"
#           },
#         },

def analyze_images_with_gpt4_vision(base64_images, client, prompt, detail="low"):
    # Construct the messages including the prompt and images
    messages = [
        {
            "role": "system",
            "content": """Your job is to summarize the sequence of pages out of the manga in a compelling, storytelling tone.
            Please strive to sprinkle in some direct quotes from particularly intense parts to enhance your storytelling."""
        },
       {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt}
            ] + [{"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_base64}", "detail": detail}} for img_base64 in base64_images]
        },
    ]

    # Adjusted API call to match the new SDK structure
    response = client.chat.completions.create(
        model="gpt-4-vision-preview",  # Ensure this model ID is correct for your use case
        messages=messages,
        max_tokens=4096,
    )
    
    return response
