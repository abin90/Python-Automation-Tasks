# ==========================================
# AUTOMATED FOLDER MONITORING
# ==========================================

# Import required libraries

import time
import json
import shutil
import logging
import hashlib
import threading

from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


# ==========================================
# STEP 1: LOAD CONFIGURATION
# ==========================================

# Find the current project folder

BASE_DIR = Path(__file__).parent


# Read the JSON configuration file

with open(BASE_DIR / "config.json", "r") as file:

    config = json.load(file)


# Get folder locations

MONITOR_FOLDER = BASE_DIR / config["monitor_folder"]

DESTINATION_FOLDER = BASE_DIR / config["destination_folder"]


# Get file categories

FILE_CATEGORIES = config["file_categories"]

DEFAULT_CATEGORY = config["default_category"]


# Create required folders automatically

MONITOR_FOLDER.mkdir(exist_ok=True)

DESTINATION_FOLDER.mkdir(exist_ok=True)


# ==========================================
# STEP 2: SETUP LOGGING
# ==========================================

logging.basicConfig(

    filename=BASE_DIR / "file_monitor.log",

    level=logging.INFO,

    format="%(asctime)s - %(levelname)s - %(message)s"

)


# ==========================================
# STEP 3: LOAD PROCESSED FILES
# ==========================================

PROCESSED_FILE = BASE_DIR / "processed_files.json"


# Create an empty JSON file if it does not exist

if not PROCESSED_FILE.exists():

    with open(PROCESSED_FILE, "w") as file:

        json.dump([], file)


# Load previously processed file hashes

with open(PROCESSED_FILE, "r") as file:

    processed_files = set(json.load(file))


# Lock to prevent multiple threads from processing
# the same file simultaneously

processed_lock = threading.Lock()

# Keep track of files currently being processed

processing_files = set()


# ==========================================
# STEP 4: IDENTIFY FILE CATEGORY
# ==========================================

def identify_category(file_path):

    # Get the file extension

    extension = file_path.suffix.lower()

    # Check each category

    for category, extensions in FILE_CATEGORIES.items():

        if extension in extensions:

            return category

    # Return default category if not found

    return DEFAULT_CATEGORY


# ==========================================
# STEP 5: GENERATE FILE HASH
# ==========================================

def generate_file_hash(file_path):

    # Create a SHA256 hash object

    sha256 = hashlib.sha256()

    # Read the file in small chunks

    with open(file_path, "rb") as file:

        for chunk in iter(lambda: file.read(4096), b""):

            sha256.update(chunk)

    # Return the unique hash value

    return sha256.hexdigest()


# ==========================================
# STEP 6: WAIT UNTIL FILE COPYING IS COMPLETE
# ==========================================

def wait_for_file(file_path):

    previous_size = -1

    stable_count = 0

    # Check file size up to 120 times

    for attempt in range(120):

        try:

            # Check whether the file exists

            if not file_path.exists():

                return False

            # Get current file size

            current_size = file_path.stat().st_size

            # Check whether file size is unchanged

            if current_size == previous_size:

                stable_count += 1

            else:

                stable_count = 0

            # If file size remains unchanged for 3 checks,
            # consider copying complete

            if stable_count >= 3:

                return True

            previous_size = current_size

            time.sleep(1)

        except OSError:

            time.sleep(1)

    return False


# ==========================================
# STEP 7: MOVE FILE TO DESTINATION
# ==========================================

def move_file(file_path):

    try:

        # Check whether the file still exists

        if not file_path.exists():

            return

        # Wait until copying is completed

        print(f"\nWaiting for file: {file_path.name}")

        if not wait_for_file(file_path):

            logging.warning(
                f"File was not ready for processing: {file_path.name}"
            )

            return

        # Identify the file category

        category = identify_category(file_path)

        # Create destination category folder

        category_folder = DESTINATION_FOLDER / category

        category_folder.mkdir(exist_ok=True)

        # Generate file hash

        file_hash = generate_file_hash(file_path)

        # Check whether the file was already processed

        with processed_lock:

            if file_hash in processed_files:

                print(f"Duplicate file skipped: {file_path.name}")

                logging.info(
                    f"Duplicate file skipped: {file_path.name}"
                )

                return

            # Prepare destination file path

            destination = category_folder / file_path.name

            # Avoid overwriting an existing file

            counter = 1

            while destination.exists():

                new_name = (
                    f"{file_path.stem}_{counter}{file_path.suffix}"
                )

                destination = category_folder / new_name

                counter += 1

            # Move the file

            shutil.move(str(file_path), str(destination))

            # Save processed file hash

            processed_files.add(file_hash)

            with open(PROCESSED_FILE, "w") as file:

                json.dump(list(processed_files), file, indent=4)

        # Display success notification

        print("\n--------------------------------")

        print("File processed successfully!")

        print(f"File Name: {destination.name}")

        print(f"Category: {category}")

        print(f"Destination: {destination}")

        print("--------------------------------\n")

        # Record activity in log file

        logging.info(
            f"Processed: {destination.name} | Category: {category}"
        )

    except Exception as error:

        print(f"Error processing {file_path.name}: {error}")

        logging.error(
            f"Error processing {file_path.name}: {error}"
        )


# ==========================================
# STEP 8: CREATE FILE EVENT HANDLER
# ==========================================

class FolderMonitor(FileSystemEventHandler):

    def process_event(self, file_path):

        # Ignore folders

        if not file_path.is_file():

            return

        # Create a unique key for this file

        file_key = str(file_path.resolve())

        # Prevent duplicate processing threads

        with processed_lock:

            if file_key in processing_files:

                return

            processing_files.add(file_key)

        try:

            # Process the file in the background

            move_file(file_path)

        finally:

            with processed_lock:

                processing_files.discard(file_key)


    # This function runs when a new file is created

    def on_created(self, event):

        if not event.is_directory:

            file_path = Path(event.src_path)

            threading.Thread(

                target=self.process_event,

                args=(file_path,),

                daemon=True

            ).start()


    # This function runs when a file is moved into
    # the monitored folder

    def on_moved(self, event):

        if not event.is_directory:

            file_path = Path(event.dest_path)

            threading.Thread(

                target=self.process_event,

                args=(file_path,),

                daemon=True

            ).start()


# ==========================================
# STEP 9: START FOLDER MONITORING
# ==========================================

def start_monitoring():

    # Create event handler object

    event_handler = FolderMonitor()

    # Create Watchdog observer

    observer = Observer()

    # Start monitoring the incoming folder

    observer.schedule(

        event_handler,

        str(MONITOR_FOLDER),

        recursive=False

    )

    # Start observer in background

    observer.start()

    print("\n====================================")

    print(" AUTOMATED FOLDER MONITORING STARTED")

    print("====================================")

    print(f"Monitoring Folder: {MONITOR_FOLDER}")

    print(f"Destination Folder: {DESTINATION_FOLDER}")

    print("\nWaiting for new files...")

    print("Press CTRL + C to stop monitoring.\n")

    try:

        # Keep the program running

        while True:

            time.sleep(1)

    except KeyboardInterrupt:

        print("\nStopping folder monitoring...")

        observer.stop()

    observer.join()

    print("Folder monitoring stopped.")


# ==========================================
# STEP 10: RUN THE PROGRAM
# ==========================================

if __name__ == "__main__":

    start_monitoring()