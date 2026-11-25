import pandas as pd
import json
import re

from pathlib import Path
from datetime import datetime


# --------------------------------------------------
# 1. DEFINE PROJECT FOLDERS
# --------------------------------------------------

BASE_DIR = Path(__file__).parent

INPUT_FOLDER = BASE_DIR / "input"

OUTPUT_FOLDER = BASE_DIR / "output"

CONFIG_FILE = BASE_DIR / "config.json"


# --------------------------------------------------
# 2. LOAD VALIDATION CONFIGURATION
# --------------------------------------------------

def load_config():

    try:

        with open(CONFIG_FILE, "r") as file:

            config = json.load(file)

        print("Validation configuration loaded successfully.")

        return config

    except FileNotFoundError:

        print("Error: config.json file not found.")

        return None

    except json.JSONDecodeError:

        print("Error: Invalid JSON configuration.")

        return None


# --------------------------------------------------
# 3. LOAD CSV OR EXCEL FILE
# --------------------------------------------------

def load_data(file_path):

    try:

        file_path = Path(file_path)

        if not file_path.exists():

            print("Error: Input file does not exist.")

            return None

        if file_path.suffix.lower() == ".csv":

            df = pd.read_csv(
                file_path,
                dtype=str,
                keep_default_na=False
            )

        elif file_path.suffix.lower() == ".xlsx":

            df = pd.read_excel(
                file_path,
                dtype=str,
                keep_default_na=False,
                engine="openpyxl"
            )

        else:

            print("Unsupported file format.")

            return None

        print("File loaded successfully.")

        print("Total records:", len(df))

        return df

    except Exception as e:

        print("Error loading file:", e)

        return None


# --------------------------------------------------
# 4. CHECK EMPTY VALUES
# --------------------------------------------------

def is_empty(value):

    if value is None:

        return True

    return str(value).strip() == ""


# --------------------------------------------------
# 5. VALIDATE EMAIL
# --------------------------------------------------

def validate_email(email):

    pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"

    return re.fullmatch(pattern, str(email).strip()) is not None


# --------------------------------------------------
# 6. VALIDATE PHONE NUMBER
# --------------------------------------------------

def validate_phone(phone):

    phone = str(phone).strip()

    pattern = r"^\+?[0-9]{10,15}$"

    return re.fullmatch(pattern, phone) is not None


# --------------------------------------------------
# 7. VALIDATE INDIVIDUAL COLUMN
# --------------------------------------------------

def validate_column(value, column_name, rules):

    errors = []

    # Check mandatory field

    if rules.get("required", False):

        if is_empty(value):

            errors.append(
                f"{column_name} is mandatory but is missing"
            )

            return errors

    # Empty optional fields do not need further validation

    if is_empty(value):

        return errors

    value = str(value).strip()

    # Email validation

    if rules.get("type") == "email":

        if not validate_email(value):

            errors.append(
                f"{column_name} has an invalid email format"
            )

    # Phone validation

    if rules.get("type") == "phone":

        if not validate_phone(value):

            errors.append(
                f"{column_name} has an invalid phone number"
            )

    # Integer validation

    if rules.get("type") == "integer":

        try:

            number = int(value)

            minimum = rules.get("min")

            maximum = rules.get("max")

            if minimum is not None and number < minimum:

                errors.append(
                    f"{column_name} must be at least {minimum}"
                )

            if maximum is not None and number > maximum:

                errors.append(
                    f"{column_name} must not exceed {maximum}"
                )

        except ValueError:

            errors.append(
                f"{column_name} must contain an integer"
            )

    # Allowed values validation

    if "allowed_values" in rules:

        allowed_values = rules["allowed_values"]

        if value not in allowed_values:

            errors.append(
                f"{column_name} contains an invalid value: {value}"
            )

    return errors


# --------------------------------------------------
# 8. VALIDATE DUPLICATE RECORDS
# --------------------------------------------------

def validate_duplicates(df, config, row_errors):

    duplicate_columns = config.get("duplicate_check", [])

    if not duplicate_columns:

        return

    # Check whether configured columns exist

    missing_columns = [
        column for column in duplicate_columns
        if column not in df.columns
    ]

    if missing_columns:

        raise ValueError(
            f"Duplicate check columns not found: {missing_columns}"
        )

    # Identify duplicate records

    duplicate_rows = df.duplicated(
        subset=duplicate_columns,
        keep=False
    )

    # Add duplicate error to affected rows

    for index in df.index[duplicate_rows]:

        row_errors[index].append(
            f"Duplicate record found based on: {', '.join(duplicate_columns)}"
        )


# --------------------------------------------------
# 9. VALIDATE COMPLETE DATASET
# --------------------------------------------------

def validate_data(df, config):

    # Store validation errors for each row

    row_errors = {
        index: []
        for index in df.index
    }

    # Check whether configured columns exist

    for column_name, rules in config.items():

        if column_name == "duplicate_check":

            continue

        if column_name not in df.columns:

            raise ValueError(
                f"Required column not found in file: {column_name}"
            )

    # Validate individual columns

    for index, row in df.iterrows():

        for column_name, rules in config.items():

            if column_name == "duplicate_check":

                continue

            value = row[column_name]

            errors = validate_column(
                value,
                column_name,
                rules
            )

            row_errors[index].extend(errors)

    # Validate duplicate records

    validate_duplicates(
        df,
        config,
        row_errors
    )

    # Separate valid and invalid records

    valid_indices = [
        index
        for index, errors in row_errors.items()
        if len(errors) == 0
    ]

    invalid_indices = [
        index
        for index, errors in row_errors.items()
        if len(errors) > 0
    ]

    valid_df = df.loc[valid_indices].copy()

    invalid_df = df.loc[invalid_indices].copy()

    # Add error descriptions to invalid records

    invalid_df["Validation Errors"] = [
        "; ".join(row_errors[index])
        for index in invalid_indices
    ]

    return valid_df, invalid_df


# --------------------------------------------------
# 10. GENERATE OUTPUT REPORTS
# --------------------------------------------------

def generate_reports(valid_df, invalid_df, total_records):

    try:

        # Create output folder if it does not exist

        OUTPUT_FOLDER.mkdir(
            parents=True,
            exist_ok=True
        )

        # Generate timestamp

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Define output file names

        valid_file = OUTPUT_FOLDER / f"valid_records_{timestamp}.csv"

        invalid_file = OUTPUT_FOLDER / f"invalid_records_{timestamp}.csv"

        # Save valid records

        valid_df.to_csv(
            valid_file,
            index=False
        )

        # Save invalid records

        invalid_df.to_csv(
            invalid_file,
            index=False
        )

        # Calculate summary

        valid_count = len(valid_df)

        invalid_count = len(invalid_df)

        # Display summary

        print("\n================================")

        print("DATA VALIDATION SUMMARY")

        print("================================")

        print("Total records processed:", total_records)

        print("Valid records:", valid_count)

        print("Invalid records:", invalid_count)

        print("Validation failures:", invalid_count)

        print("================================")

        print("\nOutput files generated successfully!")

        print("\nValid records:", valid_file)

        print("Invalid records:", invalid_file)

    except Exception as e:

        print("Error generating reports:", e)


# --------------------------------------------------
# 11. MAIN FUNCTION
# --------------------------------------------------

def main():

    print("\nAUTOMATED DATA VALIDATION TOOL")

    print("--------------------------------")

    # Load configuration

    config = load_config()

    if config is None:

        return

    # Get input file name

    file_name = input(
        "\nEnter CSV or Excel file name: "
    )

    file_path = INPUT_FOLDER / file_name

    # Load dataset

    df = load_data(file_path)

    if df is None:

        return

    try:

        # Validate dataset

        valid_df, invalid_df = validate_data(
            df,
            config
        )

        # Generate reports

        generate_reports(
            valid_df,
            invalid_df,
            len(df)
        )

    except Exception as e:

        print("\nValidation error:", e)


# --------------------------------------------------
# 12. EXECUTE PROGRAM
# --------------------------------------------------

if __name__ == "__main__":

    main()