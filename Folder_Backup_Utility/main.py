import os
import json
import zipfile
import shutil
import logging
import hashlib

from pathlib import Path
from datetime import datetime


# ==================================================
# STEP 1: LOAD CONFIGURATION
# ==================================================

def load_config():

    try:

        config_path = Path(__file__).parent / "config.json"

        with open(config_path, "r") as file:

            config = json.load(file)

        return config

    except FileNotFoundError:

        print("Error: config.json file not found.")

        return None

    except json.JSONDecodeError:

        print("Error: Invalid JSON configuration.")

        return None


# ==================================================
# STEP 2: SETUP LOGGING
# ==================================================

def setup_logging():

    project_folder = Path(__file__).parent

    log_folder = project_folder / "logs"

    log_folder.mkdir(exist_ok=True)

    logging.basicConfig(

        filename=log_folder / "backup.log",

        level=logging.INFO,

        format="%(asctime)s - %(levelname)s - %(message)s",

        force=True

    )


# ==================================================
# STEP 3: CALCULATE FILE HASH
# ==================================================

def calculate_file_hash(file_path):

    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:

        while True:

            data = file.read(4096)

            if not data:

                break

            sha256.update(data)

    return sha256.hexdigest()


# ==================================================
# STEP 4: GET ALL FILES AND THEIR HASHES
# ==================================================

def get_file_hashes(source_folder):

    file_hashes = {}

    for root, dirs, files in os.walk(source_folder):

        for filename in files:

            file_path = os.path.join(root, filename)

            relative_path = os.path.relpath(

                file_path,

                source_folder

            )

            file_hash = calculate_file_hash(file_path)

            file_hashes[relative_path] = file_hash

    return file_hashes


# ==================================================
# STEP 5: LOAD PREVIOUS BACKUP INFORMATION
# ==================================================

def load_backup_state(backup_folder):

    state_file = os.path.join(

        backup_folder,

        "backup_state.json"

    )

    if not os.path.exists(state_file):

        return {}

    try:

        with open(state_file, "r") as file:

            return json.load(file)

    except (json.JSONDecodeError, OSError):

        logging.exception("Could not read backup state.")

        raise RuntimeError("Backup state file is unavailable or invalid.")


# ==================================================
# STEP 6: SAVE BACKUP INFORMATION
# ==================================================

def save_backup_state(backup_folder, file_hashes):

    state_file = os.path.join(

        backup_folder,

        "backup_state.json"

    )

    temp_state_file = state_file + ".tmp"

    try:

        with open(temp_state_file, "w") as file:

            json.dump(

                file_hashes,

                file,

                indent=4

            )

        os.replace(temp_state_file, state_file)

    finally:

        if os.path.exists(temp_state_file):

            os.remove(temp_state_file)


# ==================================================
# STEP 7: IDENTIFY NEW AND MODIFIED FILES
# ==================================================

def find_changed_files(current_hashes, previous_hashes):

    changed_files = []

    deleted_files = []

    for filename, current_hash in current_hashes.items():

        if filename not in previous_hashes:

            # New file

            changed_files.append(filename)

        elif current_hash != previous_hashes[filename]:

            # Modified file

            changed_files.append(filename)

    # Identify deleted files

    for filename in previous_hashes:

        if filename not in current_hashes:

            deleted_files.append(filename)

    return changed_files, deleted_files


# ==================================================
# STEP 8: CREATE BACKUP
# ==================================================

def create_backup(source_folder, backup_folder, incremental_backup):

    source_path = Path(source_folder).resolve()

    backup_path = Path(backup_folder).resolve()

    # Check source folder

    if not source_path.exists():

        print("Error: Source folder does not exist.")

        logging.error("Source folder does not exist.")

        return False

    if not source_path.is_dir():

        print("Error: Source path is not a directory.")

        return False

    # Prevent backup folder from being inside source folder

    if backup_path == source_path or source_path in backup_path.parents:

        print("Error: Backup folder cannot be inside source folder.")

        logging.error("Backup folder is inside source folder.")

        return False

    # Create backup folder

    backup_path.mkdir(parents=True, exist_ok=True)

    try:

        # Get current file hashes

        print("\nScanning source folder...")

        current_hashes = get_file_hashes(source_folder)

        # Load previous backup information

        previous_hashes = load_backup_state(backup_folder)

        # Determine backup type

        if incremental_backup and previous_hashes:

            print("Incremental backup enabled.")

            changed_files, deleted_files = find_changed_files(

                current_hashes,

                previous_hashes

            )

            backup_type = "incremental"

        else:

            print("Creating full backup.")

            changed_files = list(current_hashes.keys())

            deleted_files = []

            backup_type = "full"

        # Display file information

        print("\nBackup Analysis")

        print("---------------------------")

        print("Total files:", len(current_hashes))

        print("New or modified files:", len(changed_files))

        print("Deleted files:", len(deleted_files))

        # Generate backup filename

        current_time = datetime.now().strftime(

            "%Y-%m-%d_%H-%M-%S"

        )

        backup_filename = f"backup_{current_time}.zip"

        backup_file_path = os.path.join(

            backup_folder,

            backup_filename

        )

        temp_file_path = backup_file_path + ".tmp"

        try:

            # Estimate required storage

            required_space = sum(

                os.path.getsize(source_path / filename)

                for filename in changed_files

            )

            available_space = shutil.disk_usage(backup_folder).free

            if required_space > available_space:

                print("Error: Insufficient storage space.")

                logging.error("Insufficient storage space.")

                return False

            # Create ZIP archive

            with zipfile.ZipFile(

                temp_file_path,

                "w",

                compression=zipfile.ZIP_DEFLATED

            ) as zip_file:

                # Add changed files

                for filename in changed_files:

                    file_path = source_path / filename

                    zip_file.write(

                        file_path,

                        arcname=filename

                    )

                    print("Added:", filename)

                    logging.info(f"Added file: {filename}")

                # Store backup metadata

                metadata = {

                    "backup_type": backup_type,

                    "created_at": current_time,

                    "changed_files": changed_files,

                    "deleted_files": deleted_files

                }

                zip_file.writestr(

                    "backup_metadata.json",

                    json.dumps(metadata, indent=4)

                )

            # Rename temporary ZIP file

            os.replace(temp_file_path, backup_file_path)

            # Update backup state only after ZIP creation succeeds

            save_backup_state(

                backup_folder,

                current_hashes

            )

            print("\nBackup created successfully!")

            print("Backup type:", backup_type)

            print("Backup file:", backup_file_path)

            logging.info(

                f"{backup_type.capitalize()} backup created: "

                f"{backup_filename}"

            )

            return True

        finally:

            if os.path.exists(temp_file_path):

                os.remove(temp_file_path)

    except (OSError, zipfile.BadZipFile, RuntimeError) as error:

        print("\nBackup failed:", error)

        logging.exception("Backup creation failed.")

        return False


# ==================================================
# STEP 9: MANAGE BACKUP VERSIONS
# ==================================================

def manage_backups(backup_folder, max_backups):

    try:

        backup_files = [

            os.path.join(backup_folder, file)

            for file in os.listdir(backup_folder)

            if file.startswith("backup_") and file.endswith(".zip")

        ]

        # Sort backups by modification time

        backup_files.sort(key=os.path.getmtime)

        # Calculate number of backups to delete

        backups_to_delete = len(backup_files) - max_backups

        if backups_to_delete > 0:

            for i in range(backups_to_delete):

                old_backup = backup_files[i]

                os.remove(old_backup)

                print("Deleted old backup:", old_backup)

                logging.info(f"Deleted old backup: {old_backup}")

        print("\nBackup versions managed successfully.")

    except OSError as error:

        print("Error managing backups:", error)

        logging.exception("Backup management failed.")


# ==================================================
# STEP 10: DISPLAY BACKUP HISTORY
# ==================================================

def display_backups(backup_folder):

    print("\n========== BACKUP HISTORY ==========")

    if not os.path.exists(backup_folder):

        print("No backup folder found.")

        return

    backup_files = [

        file for file in os.listdir(backup_folder)

        if file.startswith("backup_") and file.endswith(".zip")

    ]

    backup_files.sort()

    if not backup_files:

        print("No backups available.")

        return

    for index, filename in enumerate(backup_files, start=1):

        print(f"{index}. {filename}")

    print("====================================")


# ==================================================
# STEP 11: MAIN FUNCTION
# ==================================================

def main():

    # Load configuration

    config = load_config()

    if config is None:

        return

    # Read configuration values

    project_folder = Path(__file__).parent

    source_folder = project_folder / config["source_folder"]

    backup_folder = project_folder / config["backup_folder"]

    max_backups = config["max_backups"]

    incremental_backup = config["incremental_backup"]

    # Validate configuration

    if not isinstance(max_backups, int) or isinstance(max_backups, bool) or max_backups < 1:

        print("Error: max_backups must be a positive integer.")

        return

    if not isinstance(incremental_backup, bool):

        print("Error: incremental_backup must be true or false.")

        return

    # Setup logging

    setup_logging()

    print("\n===================================")

    print("       FOLDER BACKUP UTILITY       ")

    print("===================================")

    print("Source Folder:", source_folder)

    print("Backup Folder:", backup_folder)

    print("Maximum Backups:", max_backups)

    print("Incremental Backup:", incremental_backup)

    # Create backup

    success = create_backup(

        source_folder,

        backup_folder,

        incremental_backup

    )

    # Manage backup versions

    if success:

        manage_backups(

            backup_folder,

            max_backups

        )

    # Display backup history

    display_backups(backup_folder)

    print("\nBackup process completed.")


# ==================================================
# PROGRAM EXECUTION
# ==================================================

if __name__ == "__main__":

    main()