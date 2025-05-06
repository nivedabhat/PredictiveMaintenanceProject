import pdfplumber
import re
import json
import sys

def extract_motor_specs(pdf_path):
    specs = {}
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if "Technical specifications" in text:
                lines = text.split('\n')
                start_index = next(
                    (i + 1 for i, line in enumerate(lines) if 'technical specifications' in line.lower()),
                    None  # default if not found
                )
                if start_index is None:
                    raise ValueError("Couldn't find 'Technical specifications' section.")
                for line in lines[start_index:]:
                    line.replace(',','')
                    if ':' in line:
                        print('--------------------------------------------------')
                        print(line)
                        key, value = map(str.strip, line.split(':', 1))
                        print(line.split(':', 1))
                        print(key)
                        print(value)
                        specs[key] = value
                    else:
                        # Possibly a continuation of the previous line
                        if specs:
                            last_key = list(specs.keys())[-1]
                            specs[last_key] += ' ' + line.strip()
                break  # Stop after finding and parsing the section
    return specs

# Example usage
pdf_path = 'induction motors_08_2024.pdf'
specs_dict = extract_motor_specs(pdf_path)

# Convert to JSON string if needed
json_output = json.dumps(specs_dict, indent=2)
print(json_output)
