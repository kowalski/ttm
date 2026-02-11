#!/usr/bin/env python3
"""
Create a new TTM markdown report from the template.

Usage:
    python new_ttm_report.py

Prompts for client name and session date, then creates
markdown/TTM_{date}_{name}.md with those fields pre-filled.
"""

import sys
from datetime import date
from pathlib import Path


def tty_input(prompt: str) -> str:
    """Read input from /dev/tty so it works even when stdin is redirected."""
    try:
        with open("/dev/tty") as tty:
            sys.stdout.write(prompt)
            sys.stdout.flush()
            return tty.readline().rstrip("\n")
    except OSError:
        return input(prompt)


def prompt_name() -> str:
    name = tty_input("Imię klienta: ").strip()
    if not name:
        print("Error: name cannot be empty.")
        sys.exit(1)
    return name


def prompt_date() -> date:
    today = date.today()
    default = today.strftime("%Y-%m-%d")
    raw = tty_input(f"Data sesji [{default}]: ").strip()
    if not raw:
        return today
    try:
        return date.fromisoformat(raw)
    except ValueError:
        print(f"Error: invalid date format '{raw}'. Use YYYY-MM-DD.")
        sys.exit(1)


def main():
    template_path = Path(__file__).parent / "template" / "TTM_template.md"
    if not template_path.exists():
        print(f"Error: Template not found: {template_path}")
        sys.exit(1)

    name = prompt_name()
    session_date = prompt_date()

    content = template_path.read_text(encoding="utf-8")

    # Fill name
    content = content.replace("**Imię:**\n\n", f"**Imię:**\n{name}\n\n")

    # Fill date
    content = content.replace("- Dzień:", f"- Dzień: {session_date.day}")
    content = content.replace("- Miesiąc:", f"- Miesiąc: {session_date.month}")
    content = content.replace("- Rok:", f"- Rok: {session_date.year}")

    # Write output
    output_dir = Path(__file__).parent / "markdown"
    output_dir.mkdir(exist_ok=True)
    date_str = session_date.strftime("%Y-%m-%d")
    output_path = output_dir / f"TTM_{date_str}_{name}.md"

    if output_path.exists():
        print(f"Error: file already exists: {output_path}")
        sys.exit(1)

    output_path.write_text(content, encoding="utf-8")
    print(f"Created: {output_path}")


if __name__ == "__main__":
    main()
