import os
import pandas as pd

OUTPUT_FOLDER = "/Users/niveda/Desktop/PredictiveMaintenanceProject/data/spec_parser/output"

all_tables = []


for subdir in os.listdir(OUTPUT_FOLDER):
    subpath = os.path.join(OUTPUT_FOLDER, subdir)
    if os.path.isdir(subpath):  # Ensure it's a directory
        for file in os.listdir(subpath):
            if file.endswith(".csv") and "table" in file:  # Only process CSVs containing tables
                csv_path = os.path.join(subpath, file)
                df = pd.read_csv(csv_path)
                df["source_pdf"] = subdir  # Add a column to track the source PDF
                df["table_file"] = file  # Add a column to track the table file
                all_tables.append(df)

# Combine all DataFrames into a single DataFrame
combined_df = pd.concat(all_tables, ignore_index=True)

# Save the combined DataFrame to a CSV file
combined_df.to_csv("/Users/niveda/Desktop/PredictiveMaintenanceProject/data/spec_parser/combined_tables.csv", index=False)
print("✅ All tables combined and saved.")
import os
import json

OUTPUT_FOLDER = "/Users/niveda/Desktop/PredictiveMaintenanceProject/data/spec_parser/output"
combined_data = []

# Traverse subdirectories
for subdir in os.listdir(OUTPUT_FOLDER):
    subpath = os.path.join(OUTPUT_FOLDER, subdir)
    if os.path.isdir(subpath):
        for file in os.listdir(subpath):
            if file.endswith("_sections.json"):
                json_path = os.path.join(subpath, file)
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        for item in data:
                            item["source_pdf"] = subdir  
                        combined_data.extend(data)
                except Exception as e:
                    print(f"❌ Error reading {json_path}: {e}")
