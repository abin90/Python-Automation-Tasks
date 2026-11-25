import os
import csv
from pathlib import Path
from PIL import Image, ImageOps


# ==========================================
# 1. SUPPORTED IMAGE FORMATS
# ==========================================

SUPPORTED_FORMATS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".bmp",
    ".gif",
    ".tiff",
    ".tif"
}


# ==========================================
# 2. GET FILE SIZE
# ==========================================

def get_file_size(file_path):

    size = os.path.getsize(file_path)

    # Convert bytes into KB
    size_kb = size / 1024

    return round(size_kb, 2)


# ==========================================
# 3. RESIZE IMAGE
# ==========================================

def resize_image(input_path, output_path, width, height, output_format, quality):

    try:

        # Open original image
        with Image.open(input_path) as original_image:

            # Correct image orientation using EXIF data
            image = ImageOps.exif_transpose(original_image)

            # Get original dimensions
            original_dimensions = image.size

            # Handle animated images by processing the first frame
            if getattr(image, "is_animated", False):
                image.seek(0)

            # Convert image to RGB when saving as JPEG
            if output_format == "JPEG":

                if image.mode in ("RGBA", "LA", "P"):
                    image = image.convert("RGBA")

                    # Create white background
                    background = Image.new(
                        "RGB",
                        image.size,
                        (255, 255, 255)
                    )

                    # Paste image using transparency mask
                    background.paste(image, mask=image.getchannel("A"))

                    image = background

                else:
                    image = image.convert("RGB")

            elif output_format == "PNG":

                if image.mode == "P":
                    image = image.convert("RGBA")

            # Resize while maintaining aspect ratio
            image.thumbnail(
                (width, height),
                Image.Resampling.LANCZOS
            )

            # Get resized dimensions
            resized_dimensions = image.size

            # Save processed image
            if output_format == "JPEG":

                image.save(
                    output_path,
                    format="JPEG",
                    quality=quality,
                    optimize=True
                )

            else:

                image.save(
                    output_path,
                    format="PNG",
                    optimize=True
                )

            return original_dimensions, resized_dimensions, None

    except Exception as error:

        return None, None, str(error)


# ==========================================
# 4. GENERATE THUMBNAIL
# ==========================================

def generate_thumbnail(input_path, thumbnail_path, width, height):

    try:

        with Image.open(input_path) as original_image:

            # Correct image orientation
            image = ImageOps.exif_transpose(original_image)

            # Process the first frame of animated images
            if getattr(image, "is_animated", False):
                image.seek(0)

            # Resize thumbnail
            image.thumbnail(
                (width, height),
                Image.Resampling.LANCZOS
            )

            # Save thumbnail as JPEG
            if image.mode in ("RGBA", "LA", "P"):
                image = image.convert("RGBA")

                background = Image.new(
                    "RGB",
                    image.size,
                    (255, 255, 255)
                )

                background.paste(
                    image,
                    mask=image.getchannel("A")
                )

                image = background

            else:
                image = image.convert("RGB")

            image.save(
                thumbnail_path,
                format="JPEG",
                quality=85,
                optimize=True
            )

        return True

    except Exception as error:

        print("Thumbnail error:", error)

        return False


# ==========================================
# 5. GENERATE CSV REPORT
# ==========================================

def generate_report(report_path, report_data):

    with open(report_path, "w", newline="", encoding="utf-8") as file:

        writer = csv.writer(file)

        # Column headings
        writer.writerow([
            "Image Name",
            "Original Dimensions",
            "Resized Dimensions",
            "Original Size (KB)",
            "Resized Size (KB)",
            "Size Reduction (KB)",
            "Status"
        ])

        # Write image information
        for row in report_data:

            writer.writerow(row)

    print("\nReport generated successfully!")


# ==========================================
# 6. MAIN PROGRAM
# ==========================================

def main():

    print("\n========== BULK IMAGE RESIZER ==========\n")

    # Get input and output folders
    input_folder = input("Enter input folder: ").strip()
    output_folder = input("Enter output folder: ").strip()

    # Validate input folder
    if not os.path.isdir(input_folder):

        print("\nError: Input folder does not exist!")

        return

    # Create output folders
    os.makedirs(output_folder, exist_ok=True)

    # Get image dimensions
    try:

        width = int(input("\nEnter maximum width: "))
        height = int(input("Enter maximum height: "))

        if width <= 0 or height <= 0:
            print("Width and height must be positive numbers.")
            return

    except ValueError:

        print("Please enter valid numbers!")

        return

    # Select output format
    print("\nSelect output format:")

    print("1. JPEG")
    print("2. PNG")

    format_choice = input("\nEnter your choice: ").strip()

    if format_choice == "1":

        output_format = "JPEG"
        extension = ".jpg"

        # Get JPEG quality
        try:

            quality = int(input("\nEnter JPEG quality (1-95): "))

            if quality < 1 or quality > 95:
                print("Quality must be between 1 and 95.")
                return

        except ValueError:

            print("Please enter a valid quality value!")

            return

    elif format_choice == "2":

        output_format = "PNG"
        extension = ".png"

        quality = None

    else:

        print("Invalid format selection!")

        return

    # Thumbnail option
    thumbnail_choice = input(
        "\nGenerate thumbnails? (yes/no): "
    ).strip().lower()

    generate_thumbnails = thumbnail_choice in ("yes", "y")

    if generate_thumbnails:

        try:

            thumbnail_width = int(
                input("Enter thumbnail width: ")
            )

            thumbnail_height = int(
                input("Enter thumbnail height: ")
            )

            if thumbnail_width <= 0 or thumbnail_height <= 0:
                print("Thumbnail dimensions must be positive.")
                return

            thumbnail_folder = "thumbnails"

            os.makedirs(thumbnail_folder, exist_ok=True)

        except ValueError:

            print("Please enter valid thumbnail dimensions!")

            return

    # Create report folder
    report_folder = "reports"

    os.makedirs(report_folder, exist_ok=True)

    report_path = os.path.join(
        report_folder,
        "image_report.csv"
    )

    # Get all files
    files = os.listdir(input_folder)

    # Filter supported image files
    image_files = []

    for filename in files:

        file_extension = Path(filename).suffix.lower()

        if file_extension in SUPPORTED_FORMATS:

            image_files.append(filename)

    print("\n========== PROCESSING IMAGES ==========\n")

    total_images = len(image_files)

    successful = 0
    failed = 0
    thumbnail_count = 0

    report_data = []

    # ======================================
    # PROCESS EACH IMAGE
    # ======================================

    for filename in image_files:

        input_path = os.path.join(
            input_folder,
            filename
        )

        # Get original file size
        original_size = get_file_size(input_path)

        # Generate output filename
        output_name = Path(filename).stem + extension

        output_path = os.path.join(
            output_folder,
            output_name
        )

        # Resize image
        original_dimensions, resized_dimensions, error = resize_image(
            input_path,
            output_path,
            width,
            height,
            output_format,
            quality
        )

        if error:

            print(f"Failed: {filename}")
            print("Reason:", error)

            failed += 1

            report_data.append([
                filename,
                "N/A",
                "N/A",
                original_size,
                "N/A",
                "N/A",
                "Failed"
            ])

            continue

        # Get resized file size
        resized_size = get_file_size(output_path)

        # Calculate size reduction
        size_reduction = round(
            original_size - resized_size,
            2
        )

        successful += 1

        print(f"Processed: {filename}")

        print(
            f"Original dimensions: {original_dimensions}"
        )

        print(
            f"Resized dimensions: {resized_dimensions}"
        )

        print(
            f"Original size: {original_size} KB"
        )

        print(
            f"New size: {resized_size} KB\n"
        )

        # Generate thumbnail
        if generate_thumbnails:

            thumbnail_name = (
                Path(filename).stem + ".jpg"
            )

            thumbnail_path = os.path.join(
                thumbnail_folder,
                thumbnail_name
            )

            thumbnail_success = generate_thumbnail(
                input_path,
                thumbnail_path,
                thumbnail_width,
                thumbnail_height
            )

            if thumbnail_success:

                thumbnail_count += 1

        # Add information to report
        report_data.append([

            filename,

            f"{original_dimensions[0]}x{original_dimensions[1]}",

            f"{resized_dimensions[0]}x{resized_dimensions[1]}",

            original_size,

            resized_size,

            size_reduction,

            "Success"

        ])

    # ======================================
    # GENERATE REPORT
    # ======================================

    generate_report(report_path, report_data)

    # ======================================
    # FINAL SUMMARY
    # ======================================

    print("\n========== PROCESSING COMPLETED ==========\n")

    print("Total images found:", total_images)

    print("Successfully processed:", successful)

    print("Failed images:", failed)

    if generate_thumbnails:

        print("Thumbnails generated:", thumbnail_count)

    print("\nOutput folder:", output_folder)

    print("Report saved:", report_path)

    print("\n==========================================\n")


# ==========================================
# 7. START PROGRAM
# ==========================================

if __name__ == "__main__":

    main()