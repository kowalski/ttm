# TTM - Raporty z Sesji Transformacyjnego Masażu Tantrycznego

Narzędzie do generowania raportów PDF z sesji Transformacyjnego Masażu Tantrycznego na podstawie plików markdown.

## Wymagania

- Python 3
- PyMuPDF

```bash
pip install pymupdf
```

## Struktura projektu

```
TTM/
├── fill_ttm_pdf.py        # Skrypt generujący PDF z markdown
├── extract_ttm_pdf.py     # Skrypt wyciągający dane z PDF do markdown
├── new_ttm_report.py      # Skrypt tworzący nowy raport z szablonu
├── template/
│   ├── TTM.pdf            # Szablon formularza PDF
│   └── TTM_template.md    # Szablon markdown do nowych raportów
├── markdown/              # Pliki źródłowe raportów (.md)
└── raporty/               # Wygenerowane raporty PDF
```

## Użycie

### 1. Utwórz nowy raport

```bash
python3 new_ttm_report.py
```

Skrypt zapyta o imię klienta i datę sesji (domyślnie dzisiejsza). Utworzy plik `markdown/TTM_{data}_{imię}.md` z uzupełnionymi polami imienia i daty.

### 2. Wypełnij raport

Otwórz plik `markdown/TTM_Imie.md` w dowolnym edytorze tekstu i uzupełnij pola. Treść wpisuj w linii bezpośrednio pod każdym pogrubionym nagłówkiem, np.:

```markdown
**Imię:**
Jan Kowalski

**Email:**
jan@example.com

**Data sesji:**
- Dzień: 15
- Miesiąc: 3
- Rok: 2025
```

Pola pozostawione puste zostaną pominięte w PDF.

### 3. Wygeneruj PDF

```bash
python3 fill_ttm_pdf.py markdown/TTM_Imie.md
```

PDF zostanie zapisany w `raporty/TTM_Imie.pdf`.

Możesz też podać własną ścieżkę wyjściową:

```bash
python3 fill_ttm_pdf.py markdown/TTM_Imie.md ~/Desktop/raport.pdf
```

### 4. Podgląd pól formularza PDF

Aby wyświetlić listę wszystkich pól w szablonie PDF:

```bash
python3 fill_ttm_pdf.py --list-fields
```

### 5. Wyciągnij dane z PDF do markdown

Aby odtworzyć plik markdown z wypełnionego raportu PDF:

```bash
python3 extract_ttm_pdf.py raporty/TTM_2025-08-20_Karolina.pdf
```

Plik zostanie zapisany w `markdown/TTM_2025-08-20_Karolina.md`.
