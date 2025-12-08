from pathlib import Path
import pandas as pd
from tqdm import tqdm  # pip install tqdm

# Output CSV path
output_csv = Path("clean_trade_data.csv")

# Root directory containing import/export CSVs
out_dir = Path("results")

# List all CSV files for tqdm progress bar
csv_files = list(out_dir.rglob("*.csv"))

all_rows = []

# Iterate over CSV files with progress bar
for csv_file in tqdm(csv_files, desc="Processing CSV files"):
    # Extract metadata from path
    trade_flow = csv_file.parts[-4]   # import/export
    product = csv_file.parts[-3]      # product code
    unit = csv_file.parts[-2]         # Ton/USDollar
    reporter_country = csv_file.stem  # filename without .csv

    try:
        # Read CSV
        df = pd.read_csv(csv_file)

        # Remove rows where country is "World" or "Total"
        df = df[~df["Country"].isin(["World", "Total"])]

        # Drop year columns where all values are invalid (<=0 or non-numeric)
        year_cols = df.columns[1:]  # skip "Country"
        valid_cols = [
            col for col in year_cols
            if (pd.to_numeric(df[col], errors="coerce") > 0).any()
        ]
        df = df[["Country"] + valid_cols]

        # Melt to long format
        df_long = df.melt(id_vars="Country", var_name="year", value_name="value")

        # Rename columns to match database schema
        df_long = df_long.rename(columns={"Country": "partner_country"})
        df_long["reporter_country"] = reporter_country
        df_long["trade_flow"] = trade_flow
        df_long["product"] = product
        df_long["unit"] = unit

        # Convert year and value to numeric types
        df_long["year"] = df_long["year"].astype(int)
        df_long["value"] = pd.to_numeric(df_long["value"], errors="coerce")

        # Keep only positive values
        df_long = df_long[df_long["value"] > 0]

        # Strip quotes from country names
        df_long["reporter_country"] = df_long["reporter_country"].str.strip('"')
        df_long["partner_country"] = df_long["partner_country"].str.strip('"')

        # Append to list
        all_rows.append(df_long)

    except Exception as e:
        print("Error processing file:", csv_file)
        raise e

# Combine all CSVs into a single DataFrame
final_df = pd.concat(all_rows, ignore_index=True)

# Reorder columns to match database schema
final_df = final_df[
    ["reporter_country", "partner_country", "trade_flow", "product", "unit", "year", "value"]
]

# Save to single CSV
final_df.to_csv(output_csv, index=False)

print(f"All CSVs combined into: {output_csv} ({len(final_df)} rows)")
