#!/usr/bin/env python3
"""
Script to fill TTM PDF form from a markdown file.
Preserves the original PDF formatting while filling form fields.

Usage:
    python fill_ttm_pdf.py input.md [output.pdf]

If output.pdf is not specified, it will be named based on the input file.
"""

import re
import sys
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    print("Error: PyMuPDF library required. Install with: pip install pymupdf")
    sys.exit(1)


def parse_markdown(md_path: str) -> dict:
    """Parse the markdown file and extract field values."""
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    fields = {}

    # Define patterns for each field
    field_patterns = [
        (r'\*\*Imię:\*\*\n(.*?)(?=\n\*\*|\n---|\n#|\Z)', 'imie'),
        (r'\*\*Email:\*\*\n(.*?)(?=\n\*\*|\n---|\n#|\Z)', 'email'),
        (r'\*\*Inicjały/Kod identyfikacyjny Klienta:\*\*\n(.*?)(?=\n\*\*|\n---|\n#|\Z)', 'inicjaly'),
        (r'- Dzień:\s*(\d+)', 'dzien'),
        (r'- Miesiąc:\s*(\d+)', 'miesiac'),
        (r'- Rok:\s*(\d+)', 'rok'),
        (r'\*\*Czy ta sesja jest częścią trwającej serii\?\*\*\n(.*?)(?=\n\*\*|\n---|\n#|\Z)', 'seria'),
        (r'\*\*Czas trwania sesji:\*\*\n(.*?)(?=\n\*\*|\n---|\n#|\Z)', 'czas_trwania'),
        (r'\*\*Ile razy już widziałeś się z tym klientem:\*\*\n(.*?)(?=\n\*\*|\n---|\n#|\Z)', 'ile_razy'),
        (r'\*\*Jak się przygotowałeś na tą sesję\?.*?\*\*\n(.*?)(?=\n---|\n#|\Z)', 'przed_sesja'),
        (r'\*\*Jaką intencją/pragnieniem kierował się klient.*?granice\?\*\*\n(.*?)(?=\n\*\*|\n---|\n#|\Z)', 'intencja'),
        (r'\*\*Jakie były uzgodnienia między Tobą.*?sesję\?\*\*\n(.*?)(?=\n---|\n#|\Z)', 'uzgodnienia'),
        (r'\*\*Co się wydarzyło podczas sesji\?.*?klienta\?\*\*\n(.*?)(?=\n\*\*|\n---|\n#|\Z)', 'podczas_sesji'),
        (r'\*\*Jak potoczyła się sesja względem początkowych ustaleń i intencji\?\*\*\n(.*?)(?=\n\*\*|\n---|\n#|\Z)', 'przebieg'),
        (r'\*\*Jaka była reakcja klienta.*?możliwe\)\*\*\n(.*?)(?=\n\*\*|\n---|\n#|\Z)', 'reakcja'),
        (r'\*\*Czy były takie rzeczy które zasugerowałeś.*?rozmowa\?\*\*\n(.*?)(?=\n\*\*|\n---|\n#|\Z)', 'sugestie'),
        (r'\*\*Jaka była Twoja nauka z tej sesji\?\*\*\n(.*?)(?=\n---|\n#|\Z)', 'nauka'),
    ]

    for pattern, key in field_patterns:
        match = re.search(pattern, content, re.DOTALL | re.MULTILINE)
        if match:
            value = match.group(1).strip()
            fields[key] = value
        else:
            fields[key] = ''

    return fields


# Direct mapping from our field keys to PDF form field names
PDF_FIELD_MAPPING = {
    'imie': 'masseursName',
    'email': 'email',
    'inicjaly': 'initialscodeTo',
    'miesiac': 'dateOf140[day]',
    'dzien': 'dateOf140[month]',
    'rok': 'dateOf140[year]',
    'seria': 'isThis',
    'czas_trwania': 'durationOf',
    'ile_razy': 'howMany',
    'przed_sesja': 'howDid',
    'intencja': 'whatWas',
    'uzgodnienia': 'whatWas132',
    'podczas_sesji': 'whatHappened',
    'przebieg': 'howDid135',
    'reakcja': 'whatWas136',
    'sugestie': 'wasThere',
    'nauka': 'whatWas138',
}


def list_pdf_fields(pdf_path: str) -> dict:
    """List all form fields in the PDF."""
    doc = fitz.open(pdf_path)
    fields = {}

    for page in doc:
        for widget in page.widgets():
            if widget.field_name:
                fields[widget.field_name] = {
                    'type': widget.field_type,
                    'value': widget.field_value,
                    'page': page.number
                }

    doc.close()
    return fields


def fill_pdf(template_path: str, output_path: str, data: dict) -> None:
    """Fill PDF form fields with data from markdown."""
    doc = fitz.open(template_path)

    # Get all form fields
    pdf_fields = list_pdf_fields(template_path)

    if not pdf_fields:
        print("Warning: No fillable form fields found in PDF.")
        doc.close()
        return

    # Print discovered fields
    print(f"\nDiscovered PDF form fields ({len(pdf_fields)}):")
    for name in sorted(pdf_fields.keys()):
        print(f"  - {name}")

    # Create mapping from PDF field names to our data
    fields_to_fill = {}
    for our_key, pdf_field_name in PDF_FIELD_MAPPING.items():
        value = data.get(our_key, '')
        if value and pdf_field_name in pdf_fields:
            fields_to_fill[pdf_field_name] = value

    if not fields_to_fill:
        print("No fields to fill.")
        doc.close()
        return

    print(f"\nFilling {len(fields_to_fill)} fields...")

    # Fill the fields
    for page in doc:
        for widget in page.widgets():
            if widget.field_name in fields_to_fill:
                value = fields_to_fill[widget.field_name]
                display = value.replace('\n', ' ')
                print(f"  {widget.field_name}: {display[:50]}{'...' if len(display) > 50 else ''}")

                widget.field_value = value
                widget.update()

    # Save the document
    doc.save(output_path)
    doc.close()

    print(f"\nOutput written to: {output_path}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nAvailable commands:")
        print("  python fill_ttm_pdf.py <markdown_file> [output.pdf]  - Fill PDF from markdown")
        print("  python fill_ttm_pdf.py --list-fields                  - List PDF form fields")
        sys.exit(1)

    # Template PDF path (in template subdirectory)
    template_path = str(Path(__file__).parent / 'template' / 'TTM.pdf')

    if sys.argv[1] == '--list-fields':
        if not Path(template_path).exists():
            print(f"Error: Template PDF not found: {template_path}")
            sys.exit(1)
        fields = list_pdf_fields(template_path)
        print(f"PDF form fields in {template_path}:")
        for name, info in sorted(fields.items()):
            print(f"  - {name} (page {info['page'] + 1}, type {info['type']})")
        return

    md_path = sys.argv[1]

    if not Path(md_path).exists():
        print(f"Error: Markdown file not found: {md_path}")
        sys.exit(1)

    # Determine output path (default to raporty directory)
    if len(sys.argv) >= 3:
        output_path = sys.argv[2]
    else:
        md_stem = Path(md_path).stem
        raporty_dir = Path(__file__).parent / 'raporty'
        output_path = str(raporty_dir / f"{md_stem}.pdf")

    if not Path(template_path).exists():
        print(f"Error: Template PDF not found: {template_path}")
        sys.exit(1)

    print(f"Reading markdown: {md_path}")
    data = parse_markdown(md_path)

    print("\nParsed fields:")
    for key, value in data.items():
        if value:
            display = value[:60] + '...' if len(value) > 60 else value
            display = display.replace('\n', ' ')
            print(f"  {key}: {display}")

    print(f"\nUsing template: {template_path}")
    fill_pdf(template_path, output_path, data)


if __name__ == '__main__':
    main()
