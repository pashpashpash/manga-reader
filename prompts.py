BASIC_PROMPT = """
I am giving you a sequence of pages directly out of a manga.
Please write me a SHORT, CONCISE summary of all the pages in a story-telling tone (MAXIMUM 200 WORDS). 
I don't want you to invent new things, just summarize what is happening in the pages provided. 

Your final summary should stick to the plot without over embellishing. The summary you write should be shorter than a minute of reading time.

REQUIRED: Please include in-line citations to the relevant image you are referring to in the format of `[^{image_index}]`. 
The `image_index` is the index of the image in the sequence of pages you are summarizing, NOT the page number written on the image. 
People will DIE if you cite the incorrect `image_index`.

If you'd like to provide multiple `image_index` citations next to each other, simply write them all in sequence, like this: `[^{image_index1}][^{image_index2}][^{image_index3}]`.

SUPER IMPORTANT: Sprinkle in direct quotes from particularly intense parts in your storytelling.
REQUIRED: Every direct quote MUST have an `image_index` citation.

REQUIRED: In-line image_index citations MUST be included in the same sentence as the text they are referencing. NO EXCEPTIONS.
"""

BASIC_INSTRUCTIONS = """Your job is to summarize the sequence of pages out of the manga in a compelling, storytelling tone. Don't be long-winded and stick to the plot. 
The summary you write should be shorter than a minute of reading time (MAXIMUM 200 WORDS).
Please strive to sprinkle in some direct quotes from particularly intense parts to enhance your storytelling.
REQUIRED: You MUST include in-line citations to the relevant image you are referring to in the format of `[^{image_index}]`. 
IMPORTANT: The `image_index` is the index of the image in the sequence of pages you are summarizing, NOT the page number written on the image.
People will DIE if you cite the incorrect `image_index`. 

If you'd like to provide multiple `image_index` citations next to each other, simply write them all in sequence, like this: `[^{image_index1}][^{image_index2}][^{image_index3}]`.

SUPER IMPORTANT: Please strive to sprinkle in some direct quotes from characters during particularly intense parts to enhance your storytelling.
REQUIRED: Every direct quote MUST have an `image_index` citation.

REQUIRED: In-line image_index citations MUST be included in the same sentence as the text they are referencing. NO EXCEPTIONS.
"""

BASIC_PROMPT_WITH_CONTEXT = """
Pasted above is a summary of the chapters up to this point in the volume, just to give you some context.
Your job is to summarize the sequence of pages out of the manga in a compelling, storytelling tone. Don't be long-winded and stick to the plot. 
The summary you write should be shorter than a minute of reading time (MAXIMUM 200 WORDS).

REQUIRED: Please include in-line citations to the relevant image you are referring to in the format of `[^{image_index}]`. 
The `image_index` is the index of the image in the sequence of pages you are summarizing, NOT the page number written on the image. 
People will DIE if you cite the incorrect `image_index`.

If you'd like to provide multiple `image_index` citations next to each other, simply write them all in sequence, like this: `[^{image_index1}][^{image_index2}][^{image_index3}]`.

SUPER IMPORTANT: Sprinkle in direct quotes from particularly intense parts in your storytelling.
REQUIRED: Every direct quote MUST have an `image_index` citation.

REQUIRED: In-line image_index citations MUST be included in the same sentence as the text they are referencing. NO EXCEPTIONS.
"""

DRAMATIC_PROMPT = """
I am giving you the character profiles of manga characters, the story so far, and then a sequence of pages directly out of a manga.
I want you to continue the story were it left off after the "story so far" that includes the new sequence of pages that I have provided. 
Please write me a summary of all the pages in an engaging, story-telling tone. 
I don't want you to invent new things, just summarize what is happening in the pages provided. 
Also, include some direct quotes from particularly intense parts in your storytelling.
"""

CHAIN_OF_DENSITY_PROMPT = """
Pasted above is a summary of the chapters up to this point in the volume. 
I'm also uploading a sequence of pages from a new chapter that hasn't been incorporated into the summary yet, directly from the manga.
I want you to incorporate the new chapter into the existing summary I gave you, while maintaining the same summary length.
The result should be a summary of all of the chapters including the new one I gave you, that is roughly the same length as the summary above.

To help you with the summary task, I am uploading an image of the character profiles of manga characters and then a sequence of pages from the next chapter for you to summarize.
Please incorporate a summary of all the pages in an engaging, story-telling tone, without leaving out important moments and highlights.
I don't want you to invent new things, just incorporate what is happening in the pages provided into the running summary above. 
Also, include some direct quotes from particularly intense parts in your storytelling.

REMEMBER: Your summary should INCLUDE the summary of the chapters up to this point AND the new chapter I gave you, without losing important details from the previous summary.
IT IS A MATTER OF LIFE OR DEATH that you be careful to not exclude important details from the previous chapters' summary.
The end goal is to have a concise, engaging highlight story of ALL the chapters, including the new chapter I gave you.
Please remember to retain direct quotes from particularly intense parts in your storytelling.
"""



KEY_PAGE_IDENTIFICATION_INSTRUCTIONS = """
You are given 20 pages from a manga (indexed 0-19, in order). Your job is to detect if any of the pages are 
1. A character profile page, detailing an introduction of the key characters in the manga
2. A chapter start page, implying the start of a new chapter

If any of the pages given to you contain one of those two things, please return the index of the page and the type of page it is ("profile" or "chapter").
There can be multiple profile pages and chapter pages.

Your response must be in the following format:
{"important_pages": Array<{"image_index": int 0-19, "type": "profile" | "chapter"}>}

Example:
```
{
    "important_pages": [
        {"image_index": 0, "type": "profile"},
        {"image_index": 17, "type": "chapter"}
    ]
}
```

If none of the pages contain a character profile or chapter start, return an empty array:
```
{
    "important_pages": []
}
```

Please respond with nothing else other than a properly formatted JSON object. If you fail to do so, people will die.
"""

KEY_PANEL_IDENTIFICATION_PROMPT = """
Pasted above is a short summary text of what is happening in the manga.
I'm also uploading a sequence of panel images from a manga (indexed starting from 0). 
Your job is to identify which panels are the most relevant to the text provided.

Your response must be in the following format:
{"important_panels": Array<int>}

Example:
```
{
    "important_panels": [0, 2, 5]
}

Each number in the array represents the index number of the panel in the sequence of panels you are given. 
Always return at least one panel index in the array. Limit your selections to the most relevant panels to the text provided.

Please respond with nothing else other than a properly formatted JSON object. If you fail to do so, people will die.
```
"""

KEY_PANEL_IDENTIFICATION_INSTRUCTIONS = """
You are given a sequence of panel images from a manga (indexed starting from 0). Your job is to identify which panels are the most relevant to the text provided.

Your response must be in the following format:
{"important_panels": Array<int>}

Example:
```
{
    "important_panels": [0, 2, 5]
}

Each number in the array represents the index of the panel in the sequence of panels you are given. 
Always return at least one panel index. Limit your selections to the most relevant panels to the text provided.

Please respond with nothing else other than a properly formatted JSON object. If you fail to do so, people will die.
```
"""