# TTM - Transformational Tantric Massage Reports

This directory contains tools for managing practitioner reports for Transformational Tantric Massage (TTM) sessions.

## Directory Structure

```
TTM/
├── CLAUDE.md              # This file
├── fill_ttm_pdf.py        # Script to fill PDF forms from markdown
├── template/
│   ├── TTM.pdf            # Empty PDF form template
│   └── TTM_template.md    # Markdown template for creating new reports
├── markdown/              # Markdown source files for reports
│   └── TTM_<Name>.md      # Individual report files
└── raporty/               # Generated PDF reports (output directory)
    └── TTM_<Name>.pdf     # Filled PDF reports
```

## Workflow

1. Copy `template/TTM_template.md` to `markdown/TTM_<ClientName>.md`
2. Fill in the markdown file with session details
3. Run `python3 fill_ttm_pdf.py markdown/TTM_<ClientName>.md`
4. PDF is generated in `raporty/TTM_<ClientName>.pdf`

## Script Usage

```bash
# Fill PDF from markdown (output goes to raporty/ by default)
python3 fill_ttm_pdf.py markdown/TTM_Ula.md

# Specify custom output path
python3 fill_ttm_pdf.py markdown/TTM_Ula.md custom_output.pdf

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
