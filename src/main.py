#!/usr/bin/env python3

import pandas as pd

# 1. Adjust this to the path of your original CSV
input_csv = "original.csv"

# 2. Choose your output CSV path
output_csv = "filtered.csv"

# 3. List of columns to keep (as they appear in your CSV headers).
#    Below is just an example based on your screenshot—adjust as needed.
columns_to_keep = [
    "availability",
    "avgDailyPrice.amount",
    "avgDailyPrice.currency",
    "completedTrips",
    "hostId",
    "id",
    "isAllStarHost",
    "isFavoritedBySearcher",
    "isNewListing",
    "location.city",
    "location.isDelivery",
    "location.state",
    "make",
    "model",
    "rating",
    "seoCategory",
    "tags[0].label",
    "tags[0].type",
    "tags[1].label",
    "tags[1].type",
    "tags[2].label",
    "tags[2].type",
    "type",
    "year"
]

# 4. Read the original CSV
df = pd.read_csv(input_csv)

# 5. Filter columns (drop everything else)
#    Only keep columns that actually exist in the DataFrame
existing_cols = [col for col in columns_to_keep if col in df.columns]
df_filtered = df[existing_cols]

# 6. Export the filtered DataFrame to CSV
df_filtered.to_csv(output_csv, index=False)
print(f"Saved filtered CSV with {len(existing_cols)} columns to {output_csv}!")