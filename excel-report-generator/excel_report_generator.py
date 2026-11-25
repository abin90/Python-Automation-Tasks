import pandas as pd
from pathlib import Path
from datetime import datetime


# -----------------------------------------
# STEP 1: Define Folder Locations
# -----------------------------------------

sales_folder = Path("sales")

output_file = "Consolidated_Sales_Report.xlsx"


# -----------------------------------------
# STEP 2: Read All Excel Files
# -----------------------------------------

all_data = []

excel_files = list(sales_folder.glob("*.xlsx"))

print("Reading Excel files...")

for file in excel_files:

    try:

        print("Reading:", file.name)

        # Read Excel file
        df = pd.read_excel(file)

        # Add filename to identify the source
        df["Source File"] = file.name

        # Add data to the list
        all_data.append(df)

    except Exception as e:

        print("Error reading file:", file.name)
        print("Reason:", e)


# Check whether files were found
if len(all_data) == 0:

    print("No valid Excel data found.")

    exit()


# -----------------------------------------
# STEP 3: Combine All Excel Files
# -----------------------------------------

print("\nCombining Excel files...")

sales_data = pd.concat(all_data, ignore_index=True)


# -----------------------------------------
# STEP 4: Clean Column Names
# -----------------------------------------

sales_data.columns = sales_data.columns.str.strip()

# Standardise column names
sales_data.columns = sales_data.columns.str.lower().str.strip()

# Replace spaces with underscores
sales_data.columns = sales_data.columns.str.replace(" ", "_")


# Required columns
required_columns = [
    "date",
    "product",
    "category",
    "quantity",
    "unit_price"
]


# Check required columns
missing_columns = [
    column for column in required_columns
    if column not in sales_data.columns
]

if missing_columns:

    print("Missing required columns:", missing_columns)

    exit()


# -----------------------------------------
# STEP 5: Handle Missing and Incorrect Data
# -----------------------------------------

print("\nCleaning data...")

# Convert date into proper date format
sales_data["date"] = pd.to_datetime(
    sales_data["date"],
    errors="coerce",
    dayfirst=True
)

# Convert quantity into numeric values
sales_data["quantity"] = pd.to_numeric(
    sales_data["quantity"],
    errors="coerce"
)

# Convert unit price into numeric values
sales_data["unit_price"] = pd.to_numeric(
    sales_data["unit_price"],
    errors="coerce"
)

# Remove extra spaces from product names
sales_data["product"] = sales_data["product"].astype("string").str.strip()

# Remove extra spaces from category names
sales_data["category"] = sales_data["category"].astype("string").str.strip()


# Remove rows containing missing values
sales_data = sales_data.dropna(
    subset=required_columns
)

# Remove empty product and category names
sales_data = sales_data[
    (sales_data["product"] != "") &
    (sales_data["category"] != "")
]

# Remove invalid quantities and prices
sales_data = sales_data[
    (sales_data["quantity"] > 0) &
    (sales_data["unit_price"] >= 0)
]

# Remove duplicate transactions
sales_data = sales_data.drop_duplicates(
    subset=required_columns
)


# -----------------------------------------
# STEP 6: Date Range Filtering
# -----------------------------------------

print("\nDate Range Filtering")

start_date_input = input(
    "Enter start date (DD-MM-YYYY) or press Enter to skip: "
)

end_date_input = input(
    "Enter end date (DD-MM-YYYY) or press Enter to skip: "
)

if start_date_input and end_date_input:

    try:

        start_date = pd.to_datetime(
            start_date_input,
            format="%d-%m-%Y"
        )

        end_date = pd.to_datetime(
            end_date_input,
            format="%d-%m-%Y"
        )

        if start_date > end_date:

            print("Start date cannot be greater than end date.")

            exit()

        sales_data = sales_data[
            (sales_data["date"] >= start_date) &
            (sales_data["date"] <= end_date)
        ]

    except ValueError:

        print("Invalid date format. Use DD-MM-YYYY.")

        exit()

elif start_date_input or end_date_input:

    print("Please enter both start date and end date.")

    exit()


if sales_data.empty:

    print("No sales transactions found for the selected period.")

    exit()


# -----------------------------------------
# STEP 7: Calculate Transaction Sales
# -----------------------------------------

print("\nCalculating sales...")

sales_data["total_sales"] = (
    sales_data["quantity"] *
    sales_data["unit_price"]
)


# -----------------------------------------
# STEP 8: Product-wise Revenue
# -----------------------------------------

product_summary = sales_data.groupby(
    "product"
).agg(

    total_quantity=("quantity", "sum"),

    total_revenue=("total_sales", "sum")

).reset_index()


# Sort products by revenue
product_summary = product_summary.sort_values(
    by="total_revenue",
    ascending=False
)


# -----------------------------------------
# STEP 9: Category-wise Revenue
# -----------------------------------------

category_summary = sales_data.groupby(
    "category"
).agg(

    total_quantity=("quantity", "sum"),

    total_revenue=("total_sales", "sum")

).reset_index()


# Sort categories by revenue
category_summary = category_summary.sort_values(
    by="total_revenue",
    ascending=False
)


# -----------------------------------------
# STEP 10: Identify Best-Selling Products
# -----------------------------------------

best_selling_products = product_summary.sort_values(
    by="total_quantity",
    ascending=False
)

# Get the top-selling product
best_product = best_selling_products.iloc[0]["product"]

best_quantity = best_selling_products.iloc[0]["total_quantity"]


# -----------------------------------------
# STEP 11: Calculate Overall Summary
# -----------------------------------------

total_transactions = len(sales_data)

total_products = sales_data["product"].nunique()

total_quantity = sales_data["quantity"].sum()

total_revenue = sales_data["total_sales"].sum()


# Create Overall Summary DataFrame
overall_summary = pd.DataFrame({

    "Metric": [
        "Total Transactions",
        "Total Products",
        "Total Quantity Sold",
        "Total Revenue",
        "Best Selling Product",
        "Best Selling Product Quantity"
    ],

    "Value": [
        total_transactions,
        total_products,
        total_quantity,
        total_revenue,
        best_product,
        best_quantity
    ]

})


# -----------------------------------------
# STEP 12: Generate Excel Report
# -----------------------------------------

print("\nGenerating Excel report...")

with pd.ExcelWriter(
    output_file,
    engine="openpyxl"
) as writer:

    # Worksheet 1: All Transactions
    sales_data.to_excel(
        writer,
        sheet_name="All Transactions",
        index=False
    )

    # Worksheet 2: Product Summary
    product_summary.to_excel(
        writer,
        sheet_name="Product Summary",
        index=False
    )

    # Worksheet 3: Category Summary
    category_summary.to_excel(
        writer,
        sheet_name="Category Summary",
        index=False
    )

    # Worksheet 4: Overall Summary
    overall_summary.to_excel(
        writer,
        sheet_name="Overall Summary",
        index=False
    )


# -----------------------------------------
# STEP 13: Format Excel Report
# -----------------------------------------

from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment

# Open generated Excel file
workbook = load_workbook(output_file)

for worksheet in workbook.worksheets:

    # Format header row
    for cell in worksheet[1]:

        cell.font = Font(
            bold=True,
            color="FFFFFF"
        )

        cell.fill = PatternFill(
            start_color="1F4E78",
            end_color="1F4E78",
            fill_type="solid"
        )

        cell.alignment = Alignment(
            horizontal="center"
        )

    # Automatically adjust column width
    for column in worksheet.columns:

        max_length = 0

        column_letter = column[0].column_letter

        for cell in column:

            if cell.value is not None:

                max_length = max(
                    max_length,
                    len(str(cell.value))
                )

        worksheet.column_dimensions[
            column_letter
        ].width = max_length + 5


# Save formatted workbook
workbook.save(output_file)


# -----------------------------------------
# STEP 14: Display Final Result
# -----------------------------------------

print("\n--------------------------------")

print("SALES REPORT GENERATED SUCCESSFULLY!")

print("--------------------------------")

print("Total Transactions:", total_transactions)

print("Total Products:", total_products)

print("Total Quantity Sold:", total_quantity)

print("Total Revenue:", total_revenue)

print("Best Selling Product:", best_product)

print("Best Selling Quantity:", best_quantity)

print("\nReport Saved As:", output_file)