import json
import csv
import os

###############################################################################
# 1) Flattening & Filtering Logic
###############################################################################

def flatten_json(nested_data, parent_key="", sep="."):
    """
    Recursively flattens nested dicts/lists into a single-level dict with 
    dot/bracket paths (e.g., "location.city" or "tags[0].label").
    """
    items = []
    if isinstance(nested_data, dict):
        for k, v in nested_data.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            items.extend(flatten_json(v, new_key, sep=sep).items())
    elif isinstance(nested_data, list):
        for i, v in enumerate(nested_data):
            new_key = f"{parent_key}[{i}]"
            items.extend(flatten_json(v, new_key, sep=sep).items())
    else:
        items.append((parent_key, nested_data))
    return dict(items)

# Only keep these columns (in this exact order)
COLUMNS_TO_KEEP = [
    "type",
    "year",
    "make",
    "model",
    "rating",
    "isAllStarHost",
    "avgDailyPrice.amount",
    "avgDailyPrice.currency",
    "completedTrips",
    "location.locationSlugs.en_CA",
    "location.isDelivery",
    "location.city",
    "isNewListing",
    "tags[0].label",
    "tags[0].type",
    "tags[1].label",
    "tags[1].type",
    "tags[2].label",
    "tags[2].type",
]

def calculate_profitability(row):
    """
    Calculate the profitability score for each vehicle entry.
    """
    rating = row.get('rating', 5)  # Default to 5 if rating is missing
    rating = rating if rating is not None else 5  # Handle None values explicitly
    rating_factor = rating / 5.0

    all_star_bonus = 1.1 if row.get('isAllStarHost') == 'True' else 1.0
    avg_price = row.get('avgDailyPrice.amount', 0)  # Default to 0 if missing
    trips = row.get('completedTrips', 0)  # Default to 0 if missing

    return round((avg_price * trips * rating_factor * all_star_bonus), 2)


def parse_har_for_turo_entries(har_path):
    """
    Loads the HAR file, finds Turo /api/v2/search JSON responses, and returns
    a list of flattened listing dictionaries.
    """
    with open(har_path, "r", encoding="utf-8") as f:
        har_data = json.load(f)

    all_rows = []
    for entry in har_data.get("log", {}).get("entries", []):
        request = entry.get("request", {})
        response = entry.get("response", {})
        url = request.get("url", "")
        method = request.get("method", "")

        if method == "POST" and "turo.com/api/v2/search" in url.lower():
            content = response.get("content", {})
            mime_type = content.get("mimeType", "").lower()
            text_data = content.get("text", "")

            if "json" in mime_type and text_data:
                try:
                    parsed_json = json.loads(text_data)
                except json.JSONDecodeError:
                    continue

                flattened_rows = []

                for key_guess in ["vehicles", "results", "data", "banners"]:
                    if key_guess in parsed_json and isinstance(parsed_json[key_guess], list):
                        for item in parsed_json[key_guess]:
                            flattened = flatten_json(item)
                            flattened['Profitability Score'] = calculate_profitability(flattened)
                            flattened_rows.append(flattened)

                if isinstance(parsed_json, list):
                    for item in parsed_json:
                        flattened = flatten_json(item)
                        flattened['Profitability Score'] = calculate_profitability(flattened)
                        flattened_rows.append(flattened)

                all_rows.extend(flattened_rows)

    return all_rows


def write_filtered_csv(dict_list, csv_path):
    """
    Write only the columns in COLUMNS_TO_KEEP to csv_path, in the specified order,
    and add the Profitability Score to each row.
    """
    if not dict_list:
        raise ValueError("No rows found to export.")

    # Add Profitability Score to columns
    columns_with_profit = COLUMNS_TO_KEEP + ['Profitability Score']

    filtered_rows = []
    for original_row in dict_list:
        filtered = {col: original_row.get(col, None) for col in columns_with_profit}
        filtered_rows.append(filtered)

    os.makedirs(os.path.dirname(csv_path), exist_ok=True)

    # Write CSV with profitability score
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns_with_profit)
        writer.writeheader()
        for row in filtered_rows:
            writer.writerow(row)
