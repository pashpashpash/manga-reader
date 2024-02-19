import re

def clean_and_relocate_citations_sequence(text):
    # Clean up the citations first
    cleaned_text = text.replace(" ^[", "[^").replace("^[", "[^").replace(" [^", "[^").replace("[^^", "[^")
    
    # Define a pattern to match sequences of citations that come before a period
    pattern = re.compile(r"((?:\[\^\d+\])+)(\.)")
    # Relocate the entire sequence of citations to after the period
    relocated_text = re.sub(pattern, r"\2\1", cleaned_text)
    
    return relocated_text


def extract_text_and_citations(text, images, images_unscaled):
    text = clean_and_relocate_citations_sequence(text)
    # Split text by citations, capturing the citations as well
    parts = re.split(r'(\[\^[\d\]]+\])', text)
    
    # Initialize variables to store the current text block and its citations
    current_text = ""
    citations = []
    output = []
    
    for part in parts:
        if re.match(r'\[\^[\d\]]+\]', part):
            current_citations = [int(num) for num in re.findall(r'\d+', part)]
            valid_citations = [num for num in current_citations if num < len(images)]
            citations.extend(valid_citations)
        else:
            if current_text and not part.strip().startswith("[^"):
                # We have a new text block, so save the current one
                output.append({
                    "text": current_text.strip(),
                    "citations": citations
                })
                current_text = part
                citations = []
            else:
                # Continue building the current text block
                current_text += part
    
    # Add the last text block if it exists
    if current_text.strip():
        output.append({
            "text": current_text.strip(),
            "citations": citations
        })

    # iterate through the output and add an array of images to each object, corresponding to the citations
    for i, obj in enumerate(output):
        movie_images = []
        movie_images_unscaled = []
        for citation in obj["citations"]:
            if citation < len(images):
                movie_images.append(images[citation])
                movie_images_unscaled.append(images_unscaled[citation])

        obj["images"] = movie_images
        obj["images_unscaled"] = movie_images_unscaled

    # cleanup step -- rolling up blocks with no citations into the next available block with citations, while maintaining the order of the text.
    output.reverse()
    i = len(output) - 1
    while i > 0:
        if not output[i]["citations"]:
            # Merge this block's text with the previous one
            output[i - 1]["text"] = output[i]["text"] + " " + output[i - 1]["text"]
            output[i - 1]["citations"].extend(output[i]["citations"])  # In case there are any
            del output[i]  # Remove the current block after merging
        i -= 1
    
    if len(output) > 1 and not output[0]["citations"]:
        # If the first block has no citations, merge its text with the next block
        output[1]["text"] = output[1]["text"] + " " + output[0]["text"]
        del output[0]
    
    output.reverse()

    # No need for cleaned_output, output is now cleaned
    return output


def extract_script(movie):
    script = ""
    for scene in movie:
        script += scene["text"]
        
    return script