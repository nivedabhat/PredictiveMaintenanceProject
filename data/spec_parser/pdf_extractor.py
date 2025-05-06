import os
import logging
import json
import re
import camelot
import pdfplumber

# Setup logging
logging.basicConfig(level=logging.INFO)

# Define the input and output folders
PDF_FOLDER = "/Users/niveda/Desktop/PredictiveMaintenanceProject/data/spec_parser/sample_pdfs"
OUTPUT_FOLDER = "/Users/niveda/Desktop/PredictiveMaintenanceProject/data/spec_parser/output"

# Extract text from PDF using pdfplumber
def extract_text(pdf_path):
    """Extracts text from the PDF file using pdfplumber for better formatting."""
    try:
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
    except Exception as e:
        logging.error(f"Error extracting text from {pdf_path} using pdfplumber: {e}")
        return ""

# Improved regex pattern to extract structured sections
def extract_sections_from_text(text):
    """Extracts structured sections from the text using regex."""
    section_pattern = r"([A-Za-z \(\)/\d\-\–\[\]]+:\s*[\d\w °±µ%/.×+\-–~><=]+)"
    sections = re.findall(section_pattern, text)
    return sections

# Parse extracted sections into key-value pairs
def parse_sections(sections):
    """Parses section strings into a dictionary."""
    parsed = {}
    for section in sections:
        if ":" in section:
            key, value = section.split(":", 1)
            parsed[key.strip()] = value.strip()
    return parsed

# Extract tables using both lattice and stream, and choose the better one
def extract_tables_from_pdf(pdf_path):
    """Extracts tables using both stream and lattice to maximize coverage."""
    try:
        tables_lattice = camelot.read_pdf(pdf_path, pages='1-end', flavor='lattice')
        tables_stream = camelot.read_pdf(pdf_path, pages='1-end', flavor='stream')

        if len(tables_lattice) >= len(tables_stream):
            logging.info(f"Using lattice flavor: {len(tables_lattice)} tables extracted.")
            return tables_lattice
        else:
            logging.info(f"Using stream flavor: {len(tables_stream)} tables extracted.")
            return tables_stream
    except Exception as e:
        logging.error(f"Error extracting tables from {pdf_path}: {e}")
        return []

# Save text, parsed sections, and tables
def save_data(text, sections, tables, output_path, base_name):
    """Saves the extracted text, structured sections, and tables to files."""
    try:
        os.makedirs(output_path, exist_ok=True)

        # Save raw text
        text_file = os.path.join(output_path, f"{base_name}.txt")
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(text)
        logging.info(f"Saved text to: {text_file}")

        # Save parsed sections to JSON
        parsed_sections = parse_sections(sections)
        json_file = os.path.join(output_path, f"{base_name}_sections.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(parsed_sections, f, indent=4)
        logging.info(f"Saved sections to: {json_file}")

        # Save each table as CSV
        for i, table in enumerate(tables, start=1):
            table_file = os.path.join(output_path, f"{base_name}_table_{i}.csv")
            table.to_csv(table_file)
            logging.info(f"Saved table {i} to: {table_file}")
    except Exception as e:
        logging.error(f"Error saving data to {output_path}: {e}")

# Extract text and tables from the PDF
def extract_text_and_tables_from_pdf(pdf_path, output_folder):
    """Extracts text and tables from a PDF and saves them."""
    logging.info(f"Extracting text and tables from {pdf_path}")
    
    # Extract text
    text = extract_text(pdf_path)
    if not text:
        logging.warning(f"No text found in {pdf_path}")
        return

    # Extract sections from the text
    sections = extract_sections_from_text(text)
    
    # Extract tables from the PDF
    tables = extract_tables_from_pdf(pdf_path)
    
    # Get the base name of the PDF (without extension) for file naming
    base_name = os.path.splitext(os.path.basename(pdf_path))[0].replace(" ", "_")
    output_path = os.path.join(output_folder, base_name)
    
    # Save extracted data
    save_data(text, sections, tables, output_path, base_name)

# Process all PDFs in the folder
def process_all_pdfs(pdf_folder, output_folder):
    """Process all PDFs in the folder."""
    for filename in os.listdir(pdf_folder):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(pdf_folder, filename)  # Full path to the PDF
            logging.info(f"Processing PDF: {pdf_path}")
            extract_text_and_tables_from_pdf(pdf_path, output_folder)

# Run the script
if __name__ == "__main__":
    process_all_pdfs(PDF_FOLDER, OUTPUT_FOLDER)

