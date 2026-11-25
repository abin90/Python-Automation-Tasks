import pandas as pd
import re


# Step 1: Get CSV file name from the user

file_name = input("Enter the CSV file name: ")


# Step 2: Read the CSV file

try:

    df = pd.read_csv(file_name)

    print("\nCSV file loaded successfully!")

except FileNotFoundError:

    print("Error: CSV file not found!")

    exit()


# Step 3: Remove unnecessary spaces from column names

df.columns = df.columns.str.strip()


# Step 4: Get mandatory columns from the user

print("\nAvailable columns:")

print(", ".join(df.columns))

mandatory_input = input(
    "\nEnter mandatory columns separated by commas: "
)

mandatory_columns = [
    column.strip() for column in mandatory_input.split(",")
]


# Check whether mandatory columns exist

invalid_columns = [
    column for column in mandatory_columns
    if column not in df.columns
]

if invalid_columns:

    print("Error: Invalid column names:", invalid_columns)

    exit()


# Step 5: Remove unnecessary spaces from text fields

for column in df.columns:

    df[column] = df[column].apply(
        lambda value: value.strip()
        if isinstance(value, str)
        else value
    )


# Step 6: Standardise city names

if "City" in df.columns:

    df["City"] = df["City"].str.title()


# Step 7: Identify and remove duplicate records

total_records = len(df)

duplicates = df[df.duplicated(keep="first")].copy()

duplicates["Reason"] = "Duplicate record"

df = df.drop_duplicates(keep="first")

duplicates_removed = len(duplicates)


# Step 8: Identify missing mandatory fields

missing_values = df[mandatory_columns].isnull().any(axis=1)

# Also check empty strings

for column in mandatory_columns:

    missing_values = missing_values | (df[column] == "")


# Step 9: Identify invalid email addresses

invalid_emails = pd.Series(False, index=df.index)

if "Email" in df.columns:

    def validate_email(email):

        pattern = r"^[\w.+-]+@[\w-]+\.[\w.-]+$"

        return bool(re.match(pattern, str(email)))


    invalid_emails = ~df["Email"].apply(validate_email)


# Step 10: Create invalid records report

invalid_records = []

for index, row in df.iterrows():

    reasons = []

    # Check missing mandatory fields

    for column in mandatory_columns:

        if pd.isna(row[column]) or row[column] == "":

            reasons.append("Missing mandatory field: " + column)


    # Check email format

    if "Email" in df.columns:

        if not validate_email(row["Email"]):

            reasons.append("Invalid email address")


    # Add invalid records to the report

    if reasons:

        record = row.to_dict()

        record["Reason"] = "; ".join(reasons)

        invalid_records.append(record)


# Convert invalid records into DataFrame

invalid_df = pd.DataFrame(
    invalid_records,
    columns=list(df.columns) + ["Reason"]
)


# Step 11: Get valid records

valid_records = df[
    ~missing_values & ~invalid_emails
].copy()


# Step 12: Generate cleaned CSV file

valid_records.to_csv(
    "cleaned_customers.csv",
    index=False
)


# Step 13: Generate invalid records CSV file

# Include duplicate records in the invalid report

final_invalid_records = pd.concat(
    [invalid_df, duplicates],
    ignore_index=True
)

final_invalid_records.to_csv(
    "invalid_records.csv",
    index=False
)


# Step 14: Display summary

print("\n========== DATA CLEANING SUMMARY ==========")

print("Total records processed:", total_records)

print("Duplicates removed:", duplicates_removed)

print("Valid records:", len(valid_records))

print("Invalid records:", len(final_invalid_records))

print("\nFiles generated successfully!")

print("1. cleaned_customers.csv")

print("2. invalid_records.csv")

print("===========================================")