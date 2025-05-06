import os
import re
import json
import logging
import pdfplumber
import camelot
import pandas as pd

# Setup logging
logging.basicConfig(level=logging.INFO)

# Configurable folders (update paths as needed)
PDF_FOLDER = "/Users/niveda/Desktop/PredictiveMaintenanceProject/data/spec_parser/sample_pdfs"
OUTPUT_FOLDER = "/Users/niveda/Desktop/PredictiveMaintenanceProject/data/spec_parser/output"

# Normalize known units
UNIT_NORMALIZATION = {
    "KW": "kW", "kw": "kW", "K.W.": "kW", "kVA": "kVA",
    "RPM": "rpm", "r/min": "rpm", "Hz": "Hz",
    "V": "V", "kV": "kV", "A": "A",
    "°C": "degC", "C": "degC",
    "IP55": "IP", "IP56": "IP", "IP66": "IP"
}

def normalize_unit(unit):
    if not unit:
        return None
    return UNIT_NORMALIZATION.get(unit.strip(), unit.strip())

def clean_parameter_name(param):
    param = re.sub(r"\(.*?\)", "", param)
    return param.strip().title()

def extract_model_id_from_text(text):
    match = re.search(r"(NXR\s+(EN|US)|AMD\s+[RT]|AMI)", text)
    return match.group(0) if match else "UnknownModel"

def extract_text(pdf_path):
    try:
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
    except Exception as e:
        logging.error(f"Error extracting text from {pdf_path}: {e}")
        return ""

def extract_sections_from_text(text, page_number, model_id):
    pattern = r"([A-Za-z0-9 \(\)/\-\–%\u00b0µ±\.><=]+)[\s:]{1,3}([\d.,\-\–±><=]+(?:\s*[\u00b1\-\–]?\s*\d+)?(?:[a-zA-Z/%\u00b0]+)?)"
    matches = re.findall(pattern, text)

    results = []
    for param, value_unit in matches:
        value_unit = value_unit.strip()
        embedded = re.match(r"([\d.,\-\–±><=]+)([a-zA-Z/%\u00b0]+)?", value_unit)
        if embedded:
            value = embedded.group(1)
            unit = embedded.group(2) if embedded.group(2) else ""
        else:
            value, unit = value_unit, None

        entry = {
            "model_id": model_id,
            "parameter": clean_parameter_name(param),
            "raw_value": value.strip(),
            "unit": normalize_unit(unit),
            "source_page": page_number + 1
        }

        if "±" in value:
            parts = value.split("±")
            try:
                entry["value"] = float(parts[0].strip())
                entry["tolerance"] = float(parts[1].strip())
            except:
                pass
        elif "–" in value or "-" in value:
            parts = re.split(r"[–\-]", value)
            if len(parts) == 2:
                try:
                    entry["min"] = float(parts[0].strip())
                    entry["max"] = float(parts[1].strip())
                except:
                    pass
        elif any(op in value for op in [">=", "<=", ">", "<"]):
            entry["comparison"] = value.strip()
        else:
            try:
                entry["value"] = float(value.strip())
            except:
                entry["value"] = value.strip()

        results.append(entry)
    return results

def extract_tables_from_pdf(pdf_path):
    try:
        tables = camelot.read_pdf(pdf_path, pages='all', flavor='lattice')
        return tables
    except:
        return []

def save_data(text, parsed_sections, tables, output_path, base_name):
    os.makedirs(output_path, exist_ok=True)

    with open(os.path.join(output_path, f"{base_name}.txt"), 'w', encoding='utf-8') as f:
        f.write(text)

    with open(os.path.join(output_path, f"{base_name}_parsed.json"), 'w', encoding='utf-8') as f:
        json.dump(parsed_sections, f, indent=4)

    for i, table in enumerate(tables, start=1):
        table_file = os.path.join(output_path, f"{base_name}_table_{i}.csv")
        table.to_csv(table_file)

    logging.info(f"✅ Saved all outputs for {base_name}")

def extract_from_pdf(pdf_path, output_folder):
    base_name = os.path.splitext(os.path.basename(pdf_path))[0].replace(" ", "_")
    output_path = os.path.join(output_folder, base_name)

    all_sections = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
            model_id = extract_model_id_from_text(full_text)

            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    sections = extract_sections_from_text(text, i, model_id)
                    all_sections.extend(sections)

        tables = extract_tables_from_pdf(pdf_path)
        # save_data(full_text, all_sections, tables, output_path, base_name)
        return all_sections
    except Exception as e:
        logging.error(f"❌ Failed to extract {pdf_path}: {e}")

def process_all_pdfs(pdf_folder, output_folder):
    all_pdf_data = []
    for filename in os.listdir(pdf_folder):
        if filename.endswith(".pdf"):
            all_sections =extract_from_pdf(os.path.join(pdf_folder, filename), output_folder)
            all_pdf_data.extend(all_sections)
    with open("combined.json", "w", encoding="utf-8") as f:
        json.dump(all_pdf_data, f, indent=4)
    
    df = pd.read_json('combined.json')
    print(df.head())
    df.to_csv('combined.csv', index=False)
            

# Run this when executing directly
if __name__ == "__main__":
    process_all_pdfs(PDF_FOLDER, OUTPUT_FOLDER)

