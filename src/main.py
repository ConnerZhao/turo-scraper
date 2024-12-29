#!/usr/bin/env python3

import json
import csv
import os
import tkinter as tk
from tkinter import ttk, messagebox

# For file drag-and-drop:
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except ImportError:
    messagebox.showerror("Error", "Please install tkinterdnd2:\n  pip install tkinterdnd2")
    raise

###############################################################################
# 1) Flattening & Filtering Logic
###############################################################################
def flatten_json(nested_data, parent_key="", sep="."):
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

COLUMNS_TO_KEEP = [
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
    "location.locationId",
    "location.locationSlugs.en_CA",
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
    "year",
]

def parse_har_for_turo_entries(har_path):
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
                            flattened_rows.append(flatten_json(item))

                if isinstance(parsed_json, list):
                    for item in parsed_json:
                        flattened_rows.append(flatten_json(item))

                all_rows.extend(flattened_rows)

    return all_rows

def write_filtered_csv(dict_list, csv_path):
    if not dict_list:
        raise ValueError("No rows found to export.")

    filtered_rows = []
    for original_row in dict_list:
        filtered = {}
        for col in COLUMNS_TO_KEEP:
            filtered[col] = original_row.get(col, None)
        filtered_rows.append(filtered)

    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS_TO_KEEP)
        writer.writeheader()
        for row in filtered_rows:
            writer.writerow(row)

###############################################################################
# 2) Minimalistic TTK + Drag-and-Drop GUI (Entire Window is Drop Target)
###############################################################################
class MinimalTuroApp(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()

        # Register the entire window as a drop target
        self.drop_target_register(DND_FILES)
        self.dnd_bind("<<Drop>>", self.on_drop_anywhere)

        # --- Appearance Config (Dark Theme) ---
        self.title("Turo HAR → CSV (Drag & Drop)")
        self.configure(background="#2e2e2e")

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(".", 
            background="#2e2e2e",   # background of frames/widgets
            foreground="white"
        )
        style.configure("TLabel", 
            background="#2e2e2e", 
            foreground="white"
        )
        style.configure("TFrame", 
            background="#2e2e2e"
        )
        style.configure("TButton",
            background="#3a3a3a",
            foreground="white",
            borderwidth=0
        )
        style.map("TButton",
            background=[("active", "#444444")]
        )
        style.configure("TEntry", 
            fieldbackground="#404040",
            foreground="white",
            bordercolor="#5e5e5e",
            insertcolor="white"
        )

        # HAR & CSV path variables
        self.har_file_var = tk.StringVar()
        self.csv_file_var = tk.StringVar()

        # Output folder
        self.csv_output_folder = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "csv_output")
        )

        # --- Layout: single frame for everything ---
        container = ttk.Frame(self, padding=10)
        container.pack(fill="both", expand=True)

        # HAR path entry
        self.har_entry = ttk.Entry(container, textvariable=self.har_file_var, width=60)
        self.har_entry.pack(pady=5, fill="x")

        # CSV path (read-only)
        self.csv_entry = ttk.Entry(container, textvariable=self.csv_file_var, width=60, state="readonly")
        self.csv_entry.pack(pady=5, fill="x")

        # Generate button
        generate_btn = ttk.Button(container, text="Generate CSV", command=self.on_generate)
        generate_btn.pack(pady=(10,5))

        # Info hint
        hint_lbl = ttk.Label(container, text="Drag a .har file anywhere on this window or specify a path.")
        hint_lbl.pack(pady=(5,0))

    def on_drop_anywhere(self, event):
        """Handle a HAR file dropped anywhere on the window."""
        har_path = event.data.strip("{}")
        self.set_paths(har_path)

    def set_paths(self, har_path):
        """Set the HAR path and derive the CSV path in csv_output."""
        self.har_file_var.set(har_path)
        base = os.path.basename(har_path)  # e.g. "bmw.har"
        root, _ext = os.path.splitext(base)
        csv_name = root + ".csv"
        csv_path = os.path.join(self.csv_output_folder, csv_name)
        self.csv_file_var.set(os.path.abspath(csv_path))

    def on_generate(self):
        har_path = self.har_file_var.get()
        csv_path = self.csv_file_var.get()

        if not har_path or not os.path.isfile(har_path):
            messagebox.showerror("Error", "Please drop or specify a valid .har file.")
            return

        try:
            rows = parse_har_for_turo_entries(har_path)
            if not rows:
                messagebox.showinfo("No Data", "No Turo listings found in this HAR.")
                return

            write_filtered_csv(rows, csv_path)
            messagebox.showinfo("Success", f"Saved to:\n{csv_path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

def main():
    app = MinimalTuroApp()
    app.resizable(False, False)
    app.mainloop()

if __name__ == "__main__":
    main()