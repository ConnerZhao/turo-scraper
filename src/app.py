#!/usr/bin/env python3

import os
import tkinter as tk
from tkinter import ttk, messagebox
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except ImportError:
    messagebox.showerror("Error", "Please install tkinterdnd2:\n  pip install tkinterdnd2")
    raise

from generator import parse_har_for_turo_entries, write_filtered_csv


class MinimalTuroApp(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()

        self.drop_target_register(DND_FILES)
        self.dnd_bind("<<Drop>>", self.on_drop_anywhere)

        self.title("Turo HAR → CSV (Drag & Drop)")
        self.configure(background="#2e2e2e")

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(".", background="#2e2e2e", foreground="white")
        style.configure("TLabel", background="#2e2e2e", foreground="white")
        style.configure("TFrame", background="#2e2e2e")
        style.configure("TButton", background="#3a3a3a", foreground="white", borderwidth=0)
        style.map("TButton", background=[("active", "#444444")])
        style.configure("TEntry", fieldbackground="#404040", foreground="white", bordercolor="#5e5e5e", insertcolor="white")

        self.har_file_var = tk.StringVar()
        self.csv_file_var = tk.StringVar()

        container = ttk.Frame(self, padding=10)
        container.pack(fill="both", expand=True)

        har_frame = ttk.Frame(container)
        har_frame.pack(fill="x")

        self.har_entry = ttk.Entry(har_frame, textvariable=self.har_file_var, width=45)
        self.har_entry.pack(side="left", pady=5, expand=True, fill="x")

        browse_btn = ttk.Button(har_frame, text="Browse…", command=self.on_browse)
        browse_btn.pack(side="left", padx=5)

        self.csv_entry = ttk.Entry(container, textvariable=self.csv_file_var, width=60, state="readonly")
        self.csv_entry.pack(pady=5, fill="x")

        generate_btn = ttk.Button(container, text="Generate CSV", command=self.on_generate)
        generate_btn.pack(pady=(10,5))

        info_lbl = ttk.Label(container, text="Drag a .har file anywhere or use ‘Browse…’")
        info_lbl.pack()

    def on_drop_anywhere(self, event):
        har_path = event.data.strip("{}")
        self.set_paths(har_path)

    def on_browse(self):
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(
            title="Select HAR file",
            filetypes=[("HAR files", "*.har"), ("All files", "*.*")]
        )
        if file_path:
            self.set_paths(file_path)

    def set_paths(self, har_path):
        self.har_file_var.set(har_path)
        base = os.path.basename(har_path)
        root, _ext = os.path.splitext(base)
        csv_name = root + ".csv"
        # Save in the same directory as the HAR file
        csv_path = os.path.join(os.path.dirname(har_path), csv_name)
        self.csv_file_var.set(os.path.abspath(csv_path))

    def on_generate(self):
        har_path = self.har_file_var.get()
        csv_path = self.csv_file_var.get()

        if not har_path or not os.path.isfile(har_path):
            messagebox.showerror("Error", "Please drop or select a valid .har file.")
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
