import json
import os
import sys

# Ensure local package is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from wordtemplater import WordTemplate

def main():
    template_path = os.path.join("examples", "templates", "Template.docx")
    data_path = os.path.join("examples", "Data.json")
    output_path = os.path.join("examples", "Output.docx")

    print(f"Loading template: {template_path}")
    template = WordTemplate.load(template_path)

    # Optional: configure watermark and zebra-striping
    template.set_watermark("CONFIDENTIAL", color="C0C0C0", angle=-45, font_size=72)
    template.enable_table_zebra_striping(odd_color="F9FAFB", even_color="FFFFFF")

    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print("Exporting document with data...")
    template.export(data, output_file=output_path)

    print(f"Successfully generated: {output_path}")
    print(f"File size: {os.path.getsize(output_path)} bytes")

if __name__ == "__main__":
    main()
