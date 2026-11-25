import os
import hashlib
import csv

def calculate_file_hash(file_path):

    sha256 = hashlib.sha256()

    try:
        with open(file_path, "rb") as file:

            while True:

                chunk = file.read(4096)

                if not chunk:
                    break

                sha256.update(chunk)

        return sha256.hexdigest()

    except (OSError, PermissionError):
        print(f"Unable to read: {file_path}")
        return None

def scan_files(folder_path):

    files_data = []

    for root, directories, files in os.walk(folder_path):

        for filename in files:

            file_path = os.path.join(root, filename)

            try:

                file_size = os.path.getsize(file_path)

                files_data.append({
                    "path": file_path,
                    "size": file_size
                })

            except OSError:
                print(f"Unable to access: {file_path}")

    return files_data

def find_duplicates(files_data):

    size_groups = {}

    # Group files based on their size
    for file_data in files_data:

        size = file_data["size"]

        if size not in size_groups:
            size_groups[size] = []

        size_groups[size].append(file_data)

    duplicate_groups = {}

    # Calculate hashes only for files with matching sizes
    for size, files in size_groups.items():

        if len(files) < 2:
            continue

        hash_groups = {}

        for file_data in files:

            file_hash = calculate_file_hash(file_data["path"])

            if file_hash is None:
                continue

            if file_hash not in hash_groups:
                hash_groups[file_hash] = []

            hash_groups[file_hash].append(file_data)

        # Identify groups containing duplicate files
        for file_hash, matching_files in hash_groups.items():

            if len(matching_files) > 1:

                duplicate_groups[file_hash] = matching_files

    return duplicate_groups

def display_duplicates(duplicate_groups):

    if not duplicate_groups:

        print("\nNo duplicate files found.")
        return

    print("\n========== DUPLICATE FILE REPORT ==========")

    total_savings = 0
    group_number = 1
    file_number = 1

    for file_hash, files in duplicate_groups.items():

        file_size = files[0]["size"]

        duplicate_count = len(files) - 1

        potential_savings = file_size * duplicate_count

        total_savings += potential_savings

        print(f"\nDuplicate Group {group_number}:")

        for file_data in files:

            print(f"  [{file_number}] {file_data['path']}")

            file_number += 1

        print(f"File Size: {file_size / (1024 * 1024):.2f} MB")

        print(f"Duplicate Copies: {duplicate_count}")

        print(
            f"Potential Space Savings: "
            f"{potential_savings / (1024 * 1024):.2f} MB"
        )

        group_number += 1

    print("\n============================================")

    print(
        f"Total Potential Space Savings: "
        f"{total_savings / (1024 * 1024):.2f} MB"
    )

def export_to_csv(duplicate_groups):

    filename = "duplicate_report.csv"

    try:

        with open(filename, "w", newline="", encoding="utf-8") as file:

            writer = csv.writer(file)

            writer.writerow([
                "Group Number",
                "File Path",
                "File Size (Bytes)",
                "File Size (MB)",
                "Duplicate Copies",
                "Potential Space Savings (Bytes)"
            ])

            group_number = 1

            for file_hash, files in duplicate_groups.items():

                file_size = files[0]["size"]

                duplicate_count = len(files) - 1

                potential_savings = file_size * duplicate_count

                for file_data in files:

                    writer.writerow([
                        group_number,
                        file_data["path"],
                        file_size,
                        round(file_size / (1024 * 1024), 2),
                        duplicate_count,
                        potential_savings
                    ])

                group_number += 1

        print(f"\nReport successfully exported to {filename}")

    except OSError as error:

        print(f"Unable to create CSV report: {error}")

def remove_duplicates(duplicate_groups):

    if not duplicate_groups:

        print("No duplicate files available for removal.")
        return

    print("\n========== REMOVE DUPLICATES ==========")

    file_number = 1

    for group_number, (file_hash, files) in enumerate(
        duplicate_groups.items(), start=1
    ):

        print(f"\nDuplicate Group {group_number}:")

        for file_data in files:

            file_data["number"] = file_number

            print(f"[{file_number}] {file_data['path']}")

            file_number += 1

    selected_numbers = input(
        "\nEnter file numbers to remove (comma-separated): "
    )

    try:

        selected_numbers = set(
            int(number.strip())
            for number in selected_numbers.split(",")
            if number.strip()
        )

    except ValueError:

        print("Invalid input. Please enter valid file numbers.")
        return

    selected_files = []

    for files in duplicate_groups.values():

        selected = [
            file_data for file_data in files
            if file_data["number"] in selected_numbers
        ]

        if len(selected) >= len(files):

            print(
                "Cannot remove all files in a duplicate group. "
                "At least one copy must be retained."
            )
            return

        selected_files.extend(selected)

    if not selected_files:

        print("No valid files selected.")
        return

    print("\nFiles selected for deletion:")

    for file_data in selected_files:

        print(file_data["path"])

    confirmation = input(
        "\nType DELETE to permanently remove these files: "
    )

    if confirmation != "DELETE":

        print("Deletion cancelled.")
        return

    for file_data in selected_files:

        try:

            os.remove(file_data["path"])

            print(f"Deleted: {file_data['path']}")

        except OSError as error:

            print(f"Unable to delete {file_data['path']}: {error}")

    print("\nDeletion process completed.")

def main():

    print("====================================")
    print("       DUPLICATE FILE FINDER")
    print("====================================")

    folder_path = "E:/Python Automation Tasks/Duplicate-File-FInder/test-files"

    # Check whether the folder exists
    if not os.path.isdir(folder_path):

        print("Invalid folder path. Please try again.")
        return

    print("\nScanning files...")

    # Step 1: Scan all files
    files_data = scan_files(folder_path)

    print(f"Total files scanned: {len(files_data)}")

    # Step 2: Find duplicate files
    print("\nIdentifying duplicate files...")

    duplicate_groups = find_duplicates(files_data)

    # Step 3: Display duplicate report
    display_duplicates(duplicate_groups)

    if not duplicate_groups:
        return

    # Step 4: Export CSV report
    export_choice = input(
        "\nDo you want to export the report as CSV? (yes/no): "
    ).lower().strip()

    if export_choice == "yes":

        export_to_csv(duplicate_groups)

    # Step 5: Remove selected duplicate files
    remove_choice = input(
        "\nDo you want to remove selected duplicate files? (yes/no): "
    ).lower().strip()

    if remove_choice == "yes":

        remove_duplicates(duplicate_groups)

    print("\nProgram completed successfully!")


if __name__ == "__main__":

    main()