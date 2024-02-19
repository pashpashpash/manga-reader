import json 

#$0.01/1000 tokens
VISION_PRICE_PER_TOKEN = 0.00001
#0.0005/1000 tokens
GPT_3_5_TURBO_PRICE_PER_TOKEN = 0.0000005

def analyze_images_with_gpt4_vision(character_profiles, pages, client, prompt, instructions, detail="low"):
    # Construct the messages including the prompt and images
    messages = [
        {
            "role": "system",
            "content": instructions
        },
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Here are some character profile pages, for your reference:"}
            ] + [{"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_base64}", "detail": detail}} for img_base64 in character_profiles]
        },
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt}
            ] + [{"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_base64}", "detail": detail}} for img_base64 in pages]
        },
    ]

    response = client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=messages,
        max_tokens=4096
    )
    
    return response


def detect_important_pages(profile_reference, chapter_reference, pages, client, prompt, instructions, detail="low"):
    # Construct the messages including the prompt and images
    messages = [
        {
            "role": "system",
            "content": instructions
        },
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Here are some character profile pages, for your reference:"}
            ] + [{"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_base64}", "detail": detail}} for img_base64 in profile_reference]
        },
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Here are some chapter start pages, for your reference:"}
            ] + [{"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_base64}", "detail": detail}} for img_base64 in chapter_reference]
        },
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt}
            ] + [{"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_base64}", "detail": detail}} for img_base64 in pages]
        },
    ]

    response = client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=messages,
        max_tokens=4096
    )
    response_text = response.choices[0].message.content
    tokens = response.usage.total_tokens

    # parse response text json from response.choices[0].message.content into object
    try:
        # Extract the text content from the first choice's message (if structured as expected)
        parsed_response = json.loads(response_text)
    except (AttributeError, IndexError, json.JSONDecodeError) as e:
        # Handle cases where parsing fails or the structure is not as expected
        print(f"Using GPT as a backup to format JSON object...")
        response = completions(client, response_text, JSON_PARSE_PROMPT)
        tokens += response.usage.total_tokens
        try:
            parsed_response = json.loads(response.choices[0].message.content)
        except (AttributeError, IndexError, json.JSONDecodeError) as e:
            parsed_response = None
            print("Even after using GPT to parse the json, we failed. Fatal error.")
            raise e
    
    return {"total_tokens": tokens, "parsed_response": parsed_response["important_pages"]}


def completions(client, text, prompt):
    messages = [
        {
            "role": "system",
            "content": prompt
        },
        {
            "role": "user",
            "content": [
                {"type": "text", "text": text}
            ]
        },
    ]

    response = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=messages,
        max_tokens=4096,
        response_format={"type": "json_object"},
    )

    return response



def get_important_panels(profile_reference, panels, client, prompt, instructions, detail="low"):
    # Construct the messages including the prompt and images
    messages = [
        {
            "role": "system",
            "content": instructions
        },
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Here are some character profile pages, for your reference:"}
            ] + [{"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_base64}", "detail": detail}} for img_base64 in profile_reference]
        },
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt}
            ] + [{"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_base64}", "detail": detail}} for img_base64 in panels]
        },
    ]
    try:
        response = client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=messages,
            max_tokens=4096
        )
    except Exception as e:
        if 'content_policy_violation' in str(e):
            print("The input image may contain content that is not allowed by OpenAI's safety system.")
            return {"total_tokens": 0, "parsed_response": []}
        else:
            raise e

    response_text = response.choices[0].message.content
    print("GPT RESPONSE:", response_text)
    tokens = response.usage.total_tokens

    # parse response text json from response.choices[0].message.content into object
    try:
        # Extract the text content from the first choice's message (if structured as expected)
        parsed_response = json.loads(response_text)
    except (AttributeError, IndexError, json.JSONDecodeError) as e:
        # Handle cases where parsing fails or the structure is not as expected
        print(f"Using GPT as a backup to format JSON object...")
        response = completions(client, response_text, JSON_PARSE_PROMPT_PANELS)
        tokens += response.usage.total_tokens
        try:
            parsed_response = json.loads(response.choices[0].message.content)
        except (AttributeError, IndexError, json.JSONDecodeError) as e:
            parsed_response = None
            print("Even after using GPT to parse the json, we failed. Fatal error.")
            raise e
    
    return {"total_tokens": tokens, "parsed_response": parsed_response["important_panels"]}


JSON_PARSE_PROMPT ="""
You are a JSON parser. Return a properly formatted json object based on the input from the user.
Your response must be in the following format:
{"important_pages": Array<{"image_index": int 0-19, "type": "profile" | "chapter"}>}

Examples of valid responses:
```
{
    "important_pages": [
        {"image_index": 0, "type": "profile"},
        {"image_index": 17, "type": "chapter"}
    ]
}
```

```
{
    "important_pages": []
}
```

"""


JSON_PARSE_PROMPT_PANELS ="""
You are a JSON parser. Return a properly formatted json object based on the input from the user.
Your response must be in the following format:
{"important_panels": Array<int>}

Examples of valid responses:
```
{
    "important_panels": [
        0, 4,
    ]
}
```

```
{
    "important_panels": []
}
```

"""
