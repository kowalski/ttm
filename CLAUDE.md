# TTM - Transformational Tantric Massage Reports

This directory contains tools for managing practitioner reports for Transformational Tantric Massage (TTM) sessions.

## Directory Structure

```
TTM/
├── CLAUDE.md              # This file
├── fill_ttm_pdf.py        # Script to fill PDF forms from markdown
├── extract_ttm_pdf.py     # Script to extract PDF form data into markdown
├── new_ttm_report.py      # Interactive script to create a new report
├── template/
│   ├── TTM.pdf            # Empty PDF form template
│   └── TTM_template.md    # Markdown template for creating new reports
├── markdown/              # Markdown source files for reports
│   └── TTM_<Date>_<Name>.md   # Individual report files
└── raporty/               # Generated PDF reports (output directory)
    └── TTM_<Date>_<Name>.pdf  # Filled PDF reports
```

## File Naming Convention

Files follow the pattern `TTM_{YYYY-MM-DD}_{Name}`, e.g. `TTM_2025-08-20_Karolina.md`.

## Workflow

1. Run `python3 new_ttm_report.py` (prompts for name and date, defaults to today)
2. Fill in the markdown file with session details
3. Run `python3 fill_ttm_pdf.py markdown/TTM_<Date>_<Name>.md`
4. PDF is generated in `raporty/TTM_<Date>_<Name>.pdf`

## Script Usage

```bash
# Create a new report interactively
python3 new_ttm_report.py

# Fill PDF from markdown (output goes to raporty/ by default)
python3 fill_ttm_pdf.py markdown/TTM_2026-02-05_Ula.md

# Specify custom output path
python3 fill_ttm_pdf.py markdown/TTM_2026-02-05_Ula.md custom_output.pdf

# Extract data from a filled PDF back into markdown
python3 extract_ttm_pdf.py raporty/TTM_2026-02-05_Ula.pdf

# List available PDF form fields
python3 fill_ttm_pdf.py --list-fields
```

## Form Fields

The PDF form contains fields for:
- **Page 1 (Informacje Kluczowe):** Name, email, client ID, session date, series status, duration, meeting count
- **Page 2 (Przed sesją / Pytania):** Pre-session preparation, client intentions, agreements/boundaries
- **Page 3 (Notatki i autorefleksja):** Session notes, progress vs intentions, client reaction, suggestions, learnings

## Dependencies

```bash
pip install pymupdf
```

## Notes

- The script uses PyMuPDF (fitz) for reliable PDF form filling with proper text rendering
- Polish characters are fully supported
- Empty fields in markdown are skipped (not filled in PDF)
