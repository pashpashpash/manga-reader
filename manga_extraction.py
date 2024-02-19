import fitz  # Import the PyMuPDF library
from PIL import Image
import io
import base64
import shutil
import os
from panel_extractor.panel_extractor import PanelExtractor



def generate_image_array_from_pdfs(pdf_files):
    images = []  # Initialize an array to store images

    for pdf_file in pdf_files:
        doc = fitz.open(pdf_file)  # Open the PDF file
        for page in doc:  # Iterate through each page
            pix = page.get_pixmap()  # Render page to a pixmap (an image)
            img = pix.tobytes("png")  # Convert the pixmap to PNG bytes (in memory)
            images.append(img)  # Append the PNG image bytes to the array
    
    doc.close()  # Close the PDF file
    return images  # Return the array of images


def scale_image(image_bytes, square_size = 512):
    """
    Scale the image to fit within a 512x512 square, maintaining aspect ratio.

    Args:
    - image_bytes (bytes): The original image in bytes.

    Returns:
    - bytes: The scaled image in bytes.
    """
    # Convert bytes to a PIL Image
    image = Image.open(io.BytesIO(image_bytes))
    
    # Calculate the target size to maintain aspect ratio
    target_size = square_size
    original_width, original_height = image.size
    ratio = min(target_size / original_width, target_size / original_height)
    new_width = int(original_width * ratio)
    new_height = int(original_height * ratio)

    # Resize the image
    resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Convert the PIL Image back to bytes
    img_byte_arr = io.BytesIO()
    resized_image.save(img_byte_arr, format='PNG')  # Save as PNG
    scaled_image_bytes = img_byte_arr.getvalue()
    
    return scaled_image_bytes


# Function to decode base64 to bytes, scale the image, and encode it back to base64
def scale_base64_image(base64_image, square_size=512):
    # Decode base64 to bytes
    image_bytes = base64.b64decode(base64_image)
    
    # Scale the image
    scaled_image_bytes = scale_image(image_bytes, square_size)
    
    # Encode the scaled image back to base64
    scaled_base64_str = base64.b64encode(scaled_image_bytes).decode('utf-8')
    
    return scaled_base64_str


def encode_images_to_base64(image_array):
    base64_images = []
    for img_bytes in image_array:
        base64_images.append(base64.b64encode(img_bytes).decode('utf-8'))
    return base64_images


def extract_all_pages_as_images(filename):
    # Generate the image array from the specified PDFs
    image_array = generate_image_array_from_pdfs([filename])

    scaled_images = [scale_image(img) for img in image_array]

    base_64_images = encode_images_to_base64(scaled_images)

    return {"scaled": encode_images_to_base64(scaled_images), "full": encode_images_to_base64(image_array)}


def save_important_pages(volume, profile_pages, chapter_pages, manga, volume_number):
    profile_dir = f"{manga}/v{volume_number}/profiles"
    chapter_dir = f"{manga}/v{volume_number}/chapters"
    
    # Remove existing content and recreate the directories
    if os.path.exists(profile_dir):
        shutil.rmtree(profile_dir)
    os.makedirs(profile_dir)

    if os.path.exists(chapter_dir):
        shutil.rmtree(chapter_dir)
    os.makedirs(chapter_dir)
    
    # Save profile images
    for i in profile_pages:
        with open(f"{profile_dir}/{i}.png", "wb") as f:
            f.write(base64.b64decode(volume[i]))

    # Save chapter images
    for i in chapter_pages:
        with open(f"{chapter_dir}/{i}.png", "wb") as f:
            f.write(base64.b64decode(volume[i]))

def save_all_pages(volume, manga, volume_number):
    pages_dir = f"{manga}/v{volume_number}/pages"
    
    # Remove existing content and recreate the directories
    if os.path.exists(pages_dir):
        shutil.rmtree(pages_dir)
    os.makedirs(pages_dir)
    
    for i, img in enumerate(volume):
        with open(f"{pages_dir}/{i}.png", "wb") as f:
            f.write(base64.b64decode(img))
    
    return pages_dir

def extract_panels(movie_script):

    panel_extractor = PanelExtractor(keep_text=True, min_pct_panel=2, max_pct_panel=90)

    for segment in movie_script:
        base64_images = segment["images_unscaled"]
        print("Number of unscaled images in segment:", len(base64_images))
        panels = panel_extractor.extract(base64_images)
        print("Number of panels generated:", len(panels))
        segment["panels"] = panels
        print("Panels generated for text:", segment["text"])


def split_volume_into_parts(volume, volume_unscaled, chapter_pages, num_parts):
    total_length = len(volume) - chapter_pages[0] + 1  # Calculate total length of the content we care about
    average_length_per_part = total_length / num_parts  # Determine average size per part
    
    parts = []  # To store the start and end of each part
    start_index = chapter_pages[0]  # Starting from the first page of interest
    for i in range(num_parts - 1):  # -1 because the last part is handled separately
        # Find the chapter page that is closest to the average length for this part
        end_index = min(chapter_pages, key=lambda x: abs((start_index + average_length_per_part) - x))
        # Ensure the end index does not regress or exceed the total length
        if end_index <= start_index or end_index > len(volume):
            break
        parts.append((start_index, end_index))
        start_index = end_index + 1  # Next part starts from the next page
    
    # Ensure the last part ends with the volume
    if parts[-1][1] < len(volume):
        parts.append((start_index, len(volume)))
        
    scaled_images = []
    unscaled_images = []
    # Adjust printing to reflect 0-based index ranges
    for i, (start, end) in enumerate(parts):
        if i == len(parts) - 1:
            print(f"{start}->end ({end})")
        else:
            print(f"{start}->{end}")

    scaled_images = [volume[start:end+1] for start, end in parts]
    unscaled_images = [volume_unscaled[start:end+1] for start, end in parts]

    return {"scaled_images": scaled_images, "unscaled_images": unscaled_images, "parts": parts}
