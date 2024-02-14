import fitz  # Import the PyMuPDF library
from PIL import Image
import io
import base64
import shutil
import os


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

    return base_64_images


def save_important_pages(volume, profile_pages, chapter_pages, volume_number):
    profile_dir = f"naruto/v{volume_number}/profiles"
    chapter_dir = f"naruto/v{volume_number}/chapters"
    
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


def split_volume_into_parts(volume, chapter_pages, num_parts):
    total_pages = len(volume)
    parts = []
    image_arrays = []

    # Adjust the total number of pages to consider only the content's pages
    content_start_page = chapter_pages[0]
    content_pages = total_pages - content_start_page + 1  # +1 to include the first page in the count
    pages_per_part = content_pages // num_parts

    # The start page for the first part is now the first chapter page
    start_page = content_start_page

    for part in range(1, num_parts + 1):
        # For the last part, ensure it ends with the total_pages
        if part == num_parts:
            end_page = total_pages
        else:
            # Target end page for this part within the content
            target_end_page = start_page + pages_per_part - 1  # -1 to adjust for inclusive counting

            # Find the nearest chapter end that is close to the target end page
            for chapter_page in chapter_pages + [total_pages]:  # Ensure total_pages is considered in the loop
                if chapter_page >= target_end_page or chapter_page == total_pages:
                    end_page = chapter_page
                    break
        
        # Append the slice of volume corresponding to this part
        image_arrays.append(volume[start_page-1:end_page])  # -1 because list indexing starts at 0
        parts.append((start_page, end_page))  # Keep track of the start and end pages for printing

        # Update start_page for the next part
        start_page = end_page + 1

    # Printing the parts
    for i, (start, end) in enumerate(parts):
        if i == len(parts) - 1:  # For the last part
            print(f"{start}->end ({end})")
        else:
            print(f"{start}->{end}")

    return image_arrays
