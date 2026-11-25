from pathlib import Path
from datetime import datetime
import re


# Function to get the list of files
def get_files(folder_path, extensions):

    files = []

    for file in folder_path.iterdir():

        if file.is_file():

            if not extensions or file.suffix.lower() in extensions:
                files.append(file)

    # Sort files alphabetically
    files.sort()

    return files


# Function to generate new filenames
def generate_names(files, prefix, start_number, mode, date_type):

    new_names = []

    number = start_number

    for file in files:

        if mode == "1":

            # Sequential numbering
            new_name = f"{prefix}_{number:03d}{file.suffix}"

        else:

            # Get file date
            if date_type == "1":
                timestamp = file.stat().st_ctime
            else:
                timestamp = file.stat().st_mtime

            file_date = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")

            new_name = f"{file_date}_{prefix}_{number:03d}{file.suffix}"

        new_names.append(new_name)

        number += 1

    return new_names


# Main function
def bulk_rename():

    try:

        print("\n===== BULK FILE RENAMER =====")

        # Accept folder path
        folder = "E:\File_organiser"

        folder_path = Path(folder)

        if not folder_path.exists() or not folder_path.is_dir():
            print("Error: Invalid folder path!")
            return

        # Accept common prefix
        prefix = input("Enter common prefix: ").strip()

        # Remove unwanted characters from prefix
        prefix = re.sub(r"[^\w-]+", "_", prefix)

        if not prefix:
            print("Error: Please enter a valid prefix!")
            return

        # Accept file extensions
        extension_input = input(
            "Enter file extensions (jpg,png) or press Enter for all: "
        )

        extensions = set()

        if extension_input.strip():

            for ext in extension_input.split(","):

                ext = ext.strip().lower()

                if not ext.startswith("."):
                    ext = "." + ext

                extensions.add(ext)

        # Accept starting number
        start_number = int(input("Enter starting number: "))

        if start_number < 0:
            print("Error: Starting number cannot be negative!")
            return

        # Select naming method
        print("\nChoose Naming Method:")
        print("1. Sequential Numbering")
        print("2. Include File Date")

        mode = input("Enter your choice: ")

        if mode not in ["1", "2"]:
            print("Invalid choice!")
            return

        # Select date type
        date_type = "2"

        if mode == "2":

            print("\nChoose Date Type:")
            print("1. Creation Date")
            print("2. Modification Date")

            date_type = input("Enter your choice: ")

            if date_type not in ["1", "2"]:
                print("Invalid choice!")
                return

        # Get files from the folder
        files = get_files(folder_path, extensions)

        if not files:
            print("No matching files found!")
            return

        # Generate new filenames
        new_names = generate_names(
            files, prefix, start_number, mode, date_type
        )

        # Display preview
        print("\n===== RENAME PREVIEW =====")

        for old_file, new_name in zip(files, new_names):

            print(f"{old_file.name}  -->  {new_name}")

        # Check whether new filenames already exist
        targets = [folder_path / name for name in new_names]

        if len(set(targets)) != len(targets):
            print("\nError: Duplicate new filenames detected!")
            return

        for old_file, new_file in zip(files, targets):

            if old_file != new_file and new_file.exists():
                print(f"\nError: {new_file.name} already exists!")
                print("No files were renamed.")
                return

        # Ask for confirmation
        confirm = input("\nDo you want to rename these files? (yes/no): ")

        if confirm.lower() != "yes":
            print("Renaming cancelled!")
            return

        # Rename files
        for old_file, new_file in zip(files, targets):

            if old_file != new_file:
                old_file.rename(new_file)

        print("\nAll files renamed successfully!")

    except ValueError:
        print("Error: Please enter a valid number!")

    except PermissionError:
        print("Error: Permission denied!")

    except OSError as error:
        print("File operation error:", error)


# Call the main function
bulk_rename()