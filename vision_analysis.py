def analyze_images_with_gpt4_vision(base64_images, client, prompt, instructions, detail="low"):
    # Construct the messages including the prompt and images
    messages = [
        {
            "role": "system",
            "content": instructions
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
