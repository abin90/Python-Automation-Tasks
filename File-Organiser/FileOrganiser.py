import os
import shutil

# Step 1: Get the folder path from the user
folder_path = "E:\File_organiser"

# Step 2: Check whether the folder exists
if os.path.exists(folder_path):

    # Step 3: Create categories and their file extensions
    categories = {
        "Documents": [".pdf", ".docx", ".doc"],
        "Images": [".jpg", ".jpeg", ".png", ".gif"],
        "Spreadsheets": [".xlsx", ".xls", ".csv"],
        "Text Files": [".txt"],
        "Programs": [".py"],
        "Others": []
    }

    # Step 4: Create folders if they do not exist
    for category in categories:
        category_path = os.path.join(folder_path, category)
        os.makedirs(category_path, exist_ok=True)

    # Step 5: Create a dictionary to count moved files
    file_count = {
        "Documents": 0,
        "Images": 0,
        "Spreadsheets": 0,
        "Text Files": 0,
        "Programs": 0,
        "Others": 0
    }

    # Step 6: Read all files in the given folder
    for file in os.listdir(folder_path):

        source_path = os.path.join(folder_path, file)

        # Check whether it is a file
        if os.path.isfile(source_path):

            # Get the file extension
            extension = os.path.splitext(file)[1].lower()

            # Step 7: Identify the file category
            for category, extensions in categories.items():

                if extension in extensions or category == "Others" and extension not in [ext for exts in categories.values() for ext in exts]:

                    destination_folder = os.path.join(folder_path, category)

                    destination_path = os.path.join(destination_folder, file)

                    # Step 8: Avoid overwriting files with the same name
                    if os.path.exists(destination_path):

                        name, ext = os.path.splitext(file)
                        counter = 1

                        while os.path.exists(destination_path):
                            new_file = name + "_" + str(counter) + ext
                            destination_path = os.path.join(destination_folder, new_file)
                            counter = counter + 1

                    # Step 9: Move the file
                    try:
                        shutil.move(source_path, destination_path)

                        file_count[category] = file_count[category] + 1

                        print(file, "moved to", category)

                    except Exception as e:
                        print("Could not move", file, ":", e)

                    break

    # Step 10: Display the summary
    print("\n----- File Organising Summary -----")

    for category, count in file_count.items():
        print(category, ":", count, "files moved")

    print("\nFile organisation completed successfully!")

else:
    print("The specified folder does not exist.")