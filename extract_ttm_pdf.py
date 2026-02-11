#!/usr/bin/env python3
"""
Script to extract TTM PDF form fields into a markdown report.
Reverse of fill_ttm_pdf.py.

Usage:
    python extract_ttm_pdf.py <filled_report.pdf>

Output is saved to markdown/<pdf_stem>.md based on the PDF filename.
"""

import sys
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    print("Error: PyMuPDF library required. Install with: pip install pymupdf")
    sys.exit(1)

# Reverse mapping: PDF field name -> our key
PDF_FIELD_TO_KEY = {
    'masseursName': 'imie',
    'email': 'email',
    'initialscodeTo': 'inicjaly',
    'dateOf140[month]': 'dzien',
    'dateOf140[day]': 'miesiac',
    'dateOf140[year]': 'rok',
    'isThis': 'seria',
    'durationOf': 'czas_trwania',
    'howMany': 'ile_razy',
    'howDid': 'przed_sesja',
    'whatWas': 'intencja',
    'whatWas132': 'uzgodnienia',
    'whatHappened': 'podczas_sesji',
    'howDid135': 'przebieg',
    'whatWas136': 'reakcja',
    'wasThere': 'sugestie',
    'whatWas138': 'nauka',
}


def extract_fields(pdf_path: str) -> dict:
    """Extract form field values from a filled PDF."""
    doc = fitz.open(pdf_path)
    data = {}

    for page in doc:
        for widget in page.widgets():
            if widget.field_name and widget.field_name in PDF_FIELD_TO_KEY:
                key = PDF_FIELD_TO_KEY[widget.field_name]
                value = widget.field_value or ''
                value = value.replace('\r\n', '\n').replace('\r', '\n')
                data[key] = value.strip()

    doc.close()
    return data


def fill_template(data: dict) -> str:
    """Fill the markdown template with extracted data."""
    template_path = Path(__file__).parent / 'template' / 'TTM_template.md'
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Simple fields: insert value on the line after the label
    simple_fields = {
        '**Imię:**': data.get('imie', ''),
        '**Email:**': data.get('email', ''),
        '**Inicjały/Kod identyfikacyjny Klienta:**': data.get('inicjaly', ''),
        '**Czy ta sesja jest częścią trwającej serii?**': data.get('seria', ''),
        '**Czas trwania sesji:**': data.get('czas_trwania', ''),
        '**Ile razy już widziałeś się z tym klientem:**': data.get('ile_razy', ''),
    }

    for label, value in simple_fields.items():
        if value:
            content = content.replace(f'{label}\n\n', f'{label}\n{value}\n\n')

    # Date fields
    dzien = data.get('dzien', '')
    miesiac = data.get('miesiac', '')
    rok = data.get('rok', '')
    if dzien:
        content = content.replace('- Dzień:', f'- Dzień: {dzien}')
    if miesiac:
        content = content.replace('- Miesiąc:', f'- Miesiąc: {miesiac}')
    if rok:
        content = content.replace('- Rok:', f'- Rok: {rok}')

    # Multi-line text fields: match the full bold label and insert value after
    multiline_fields = [
        ('**Jak się przygotowałeś na tą sesję? Co zauważyłeś w ciele - fizycznie, w emocjach, na poziomie erotycznym i duchowym?**', 'przed_sesja'),
        ('**Jaką intencją/pragnieniem kierował się klient/ka przychodząc do Ciebie? Czy klient/ka miał/a jakieś specjalne wymagania? Jaka była Twoja odpowiedź na wymagania/intencję klienta? Czy Twoja intuicja podpowiadała Ci coś o potrzebach klienta? Czy musiałeś/aś wyjaśniać swoją rolę jako Praktyk Transformującego Masażu Tantrycznego? Jak zostały wyjaśnione granice?**', 'intencja'),
        ('**Jakie były uzgodnienia między Tobą, a klientem? Jakie granice i intencja zostały ustalone na tą sesję?**', 'uzgodnienia'),
        ('**Co się wydarzyło podczas sesji? Co zauważyłeś/aś w swoim ciele? Co zauważyłeś/aś w ciele klienta?**', 'podczas_sesji'),
        ('**Jak potoczyła się sesja względem początkowych ustaleń i intencji?**', 'przebieg'),
        ('**Jaka była reakcja klienta na tą sesję? (zacytuj klienta, jeśli to możliwe)**', 'reakcja'),
        ('**Czy były takie rzeczy które zasugerowałeś/aś klientowi by wziął z sesji i wprowadził w swoje życie, zauważył lub praktykował? Czy pojawiła się rekomendacja odnośnie zadbania o siebie? Czy był poruszany temat sesji kontynuującej i jeśli tak, to czego dotyczyła rozmowa?**', 'sugestie'),
        ('**Jaka była Twoja nauka z tej sesji?**', 'nauka'),
    ]

    for label, key in multiline_fields:
        value = data.get(key, '')
        if value:
            content = content.replace(f'{label}\n\n', f'{label}\n{value}\n\n')

    return content


def derive_output_name(pdf_path: str) -> str:
    """Derive output filename from the PDF filename."""
    stem = Path(pdf_path).stem
    return f"{stem}.md"


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    pdf_path = sys.argv[1]

    if not Path(pdf_path).exists():
        print(f"Error: PDF file not found: {pdf_path}")
        sys.exit(1)

    template_path = Path(__file__).parent / 'template' / 'TTM_template.md'
    if not template_path.exists():
        print(f"Error: Template not found: {template_path}")
        sys.exit(1)

    print(f"Reading PDF: {pdf_path}")
    data = extract_fields(pdf_path)

    print("\nExtracted fields:")
    for key, value in data.items():
        if value:
            display = value[:60] + '...' if len(value) > 60 else value
            display = display.replace('\n', ' ')
            print(f"  {key}: {display}")

    if not any(data.values()):
        print("\nNo field values found in PDF.")
        sys.exit(1)

    markdown = fill_template(data)

    output_name = derive_output_name(pdf_path)
    output_dir = Path(__file__).parent / 'markdown'
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / output_name

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(markdown)

    print(f"\nOutput written to: {output_path}")


if __name__ == '__main__':
    main()
