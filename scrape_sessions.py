#!/usr/bin/env python3
"""
Scrape Moodle course page for upcoming TTM session links.

Logs into Moodle, finds sections matching "Sesja <date>", extracts
"Dziennik sesji masażu" links, and generates per-session markdown summaries.

Usage:
    python scrape_sessions.py [--all] [--debug] [--headed]
"""

import argparse
import re
import sys
from datetime import date
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    print("Error: python-dotenv required. Install with: pip install python-dotenv")
    sys.exit(1)

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PwTimeout
except ImportError:
    print("Error: playwright required. Install with: pip install playwright && python -m playwright install chromium")
    sys.exit(1)

import os

# --- Configuration -----------------------------------------------------------

SCRIPT_DIR = Path(__file__).parent
AUTH_STATE_DIR = SCRIPT_DIR / "auth_state"
AUTH_STATE_FILE = AUTH_STATE_DIR / "state.json"
SESJE_DIR = SCRIPT_DIR / "sesje"
DEBUG_DIR = SCRIPT_DIR / "debug"

# Polish month names → month number (nominative, genitive, and common variants)
POLISH_MONTHS = {
    "styczeń": 1, "stycznia": 1, "styczen": 1,
    "luty": 2, "lutego": 2,
    "marzec": 3, "marca": 3,
    "kwiecień": 4, "kwietnia": 4, "kwiecien": 4,
    "maj": 5, "maja": 5,
    "czerwiec": 6, "czerwca": 6,
    "lipiec": 7, "lipca": 7,
    "sierpień": 8, "sierpnia": 8, "sierpien": 8,
    "wrzesień": 9, "września": 9, "wrzesien": 9,
    "październik": 10, "października": 10, "pazdziernik": 10, "pazdziernika": 10,
    "listopad": 11, "listopada": 11,
    "grudzień": 12, "grudnia": 12, "grudzien": 12,
}

# "Sesja 11 lutego 2026" or "Sesja 15.03.2026"
DATE_PATTERN_NAMED = re.compile(
    r"Sesja\s+(\d{1,2})\s+([a-ząćęłńóśźż]+)\s+(\d{4})", re.IGNORECASE
)
DATE_PATTERN_NUMERIC = re.compile(r"Sesja\s+(\d{1,2})[./](\d{1,2})[./](\d{4})")

# --- Helpers ------------------------------------------------------------------


def parse_env():
    """Load credentials from .env file.

    MOODLE_URL can be either a base URL (https://learn.example.com) or a full
    course URL (https://learn.example.com/course/view.php?id=2).  The function
    returns (base_url, course_url, user, password).
    """
    env_path = SCRIPT_DIR / ".env"
    if not env_path.exists():
        print(f"Error: .env file not found at {env_path}")
        print("Create it with MOODLE_URL, MOODLE_USER, and MOODLE_PASS.")
        sys.exit(1)

    load_dotenv(env_path)

    url = os.getenv("MOODLE_URL", "").rstrip("/")
    user = os.getenv("MOODLE_USER", "")
    password = os.getenv("MOODLE_PASS", "")

    if not all([url, user, password]):
        print("Error: MOODLE_URL, MOODLE_USER, and MOODLE_PASS must be set in .env")
        sys.exit(1)

    from urllib.parse import urlparse
    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    # If the URL contains a path beyond /, treat full URL as the course page
    if parsed.path and parsed.path != "/":
        course_url = url
    else:
        course_url = f"{base_url}/course/view.php?id=2"

    return base_url, course_url, user, password


def save_debug(page, debug_dir: Path):
    """Save screenshot and HTML for selector debugging."""
    debug_dir.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(debug_dir / "page.png"), full_page=True)
    html = page.content()
    (debug_dir / "page.html").write_text(html, encoding="utf-8")
    print(f"Debug files saved to {debug_dir}/")


def login(page, base_url: str, user: str, password: str) -> bool:
    """Log in to Moodle using standard selectors."""
    login_url = f"{base_url}/login/index.php"
    print(f"Navigating to {login_url}")
    page.goto(login_url, wait_until="networkidle")

    # Fill credentials (standard Moodle login form)
    page.fill("#username", user)
    page.fill("#password", password)
    page.click("#loginbtn")
    page.wait_for_load_state("networkidle")

    # Check if login succeeded — look for logout link or user menu
    if page.locator("a[href*='logout']").count() > 0:
        print("Login successful.")
        return True

    # Fallback: check we are no longer on the login page
    if "/login/" not in page.url:
        print("Login successful (redirected away from login page).")
        return True

    print("Login failed — still on login page.")
    return False


def save_auth_state(context):
    """Persist browser auth state for reuse."""
    AUTH_STATE_DIR.mkdir(parents=True, exist_ok=True)
    context.storage_state(path=str(AUTH_STATE_FILE))
    print(f"Auth state saved to {AUTH_STATE_FILE}")


def auth_state_valid(base_url: str, browser, headed: bool) -> bool:
    """Check whether saved auth state is still valid."""
    if not AUTH_STATE_FILE.exists():
        return False

    ctx = browser.new_context(storage_state=str(AUTH_STATE_FILE))
    page = ctx.new_page()
    try:
        page.goto(f"{base_url}/my/", wait_until="networkidle", timeout=15000)
        valid = "/login/" not in page.url
    except Exception:
        valid = False
    finally:
        page.close()
        ctx.close()

    return valid


def parse_section_date(title: str) -> date | None:
    """Extract date from a section title like 'Sesja 11 lutego 2026' or 'Sesja 15.03.2026'."""
    # Try named month first: "Sesja 11 lutego 2026"
    m = DATE_PATTERN_NAMED.search(title)
    if m:
        day = int(m.group(1))
        month_name = m.group(2).lower()
        year = int(m.group(3))
        month = POLISH_MONTHS.get(month_name)
        if month is None:
            return None
        try:
            return date(year, month, day)
        except ValueError:
            return None

    # Fallback: numeric "Sesja 15.03.2026"
    m = DATE_PATTERN_NUMERIC.search(title)
    if m:
        day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            return date(year, month, day)
        except ValueError:
            return None

    return None


def scrape_sessions(page, course_url: str, include_all: bool, debug: bool):
    """Navigate to course page and extract session data."""
    print(f"Navigating to {course_url}")
    page.goto(course_url, wait_until="networkidle")

    if debug:
        save_debug(page, DEBUG_DIR / "course")

    today = date.today()
    sessions = []

    # --- Try Moodle 4.x selectors first, fall back to 3.x ----------------

    # Moodle 4.x: sections are <li data-sectionid> or <div data-region="section">
    sections = page.locator(
        "li[data-sectionid], "
        "div[data-region='section'], "
        "li.section"
    ).all()

    if not sections:
        print("Warning: no course sections found. Run with --debug to inspect HTML.")
        return []

    print(f"Found {len(sections)} course sections.")

    results = []

    for section in sections:
        # Try to get section title from various selectors
        title_el = (
            section.locator("h3.sectionname, h3.section-title, "
                            ".sectionname span, .section-title span, "
                            "h3 a, h4 a").first
        )
        if not title_el.count():
            continue

        # Use text_content() to avoid CSS text-transform artifacts
        title = (title_el.text_content() or "").strip()
        session_date = parse_section_date(title)

        if session_date is None:
            continue

        if not include_all and session_date < today:
            continue

        # Find "Dziennik sesji masażu" links within this section
        links = section.locator("a").all()
        journal_links = []
        for link in links:
            try:
                text = link.inner_text().strip()
            except Exception:
                continue
            if "Dziennik sesji" in text or "dziennik sesji" in text.lower():
                href = link.get_attribute("href") or ""
                if href:
                    # Clean up: remove "Opinia zwrotna" suffix added by Moodle
                    clean = re.sub(r'\s*Opinia zwrotna\s*$', '', text, flags=re.IGNORECASE).strip()
                    journal_links.append({"text": clean, "href": href})

        results.append({
            "title": title,
            "date": session_date,
            "links": journal_links,
        })

    results.sort(key=lambda r: r["date"])
    return results


def write_session_markdown(sessions: list[dict]):
    """Generate markdown files for each session."""
    if not sessions:
        print("No sessions to write.")
        return

    for session in sessions:
        d = session["date"]
        folder = SESJE_DIR / f"sesja_{d.isoformat()}"
        folder.mkdir(parents=True, exist_ok=True)

        md_path = folder / "summary.md"
        lines = [
            f"# {session['title']}",
            f"",
            f"**Data:** {d.strftime('%d.%m.%Y')}",
            f"",
        ]

        if session["links"]:
            lines.append("## Dzienniki sesji")
            lines.append("")
            for i, link in enumerate(session["links"], 1):
                lines.append(f"{i}. [{link['text']}]({link['href']})")
            lines.append("")
        else:
            lines.append("*Brak linków do dzienników sesji.*")
            lines.append("")

        md_path.write_text("\n".join(lines), encoding="utf-8")
        print(f"  {md_path}")


# --- Main --------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="Scrape Moodle for TTM session links.")
    parser.add_argument("--all", action="store_true", help="Include past sessions")
    parser.add_argument("--debug", action="store_true", help="Save screenshots and HTML for debugging")
    parser.add_argument("--headed", action="store_true", help="Show browser window")
    args = parser.parse_args()

    base_url, course_url, user, password = parse_env()

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=not args.headed)

        # Try reusing saved auth state
        reuse = auth_state_valid(base_url, browser, args.headed)

        if reuse:
            print("Reusing saved auth state.")
            context = browser.new_context(storage_state=str(AUTH_STATE_FILE))
        else:
            context = browser.new_context()
            page = context.new_page()

            if not login(page, base_url, user, password):
                if args.debug:
                    save_debug(page, DEBUG_DIR / "login_failed")
                browser.close()
                sys.exit(1)

            save_auth_state(context)
            page.close()

        page = context.new_page()
        sessions = scrape_sessions(page, course_url, include_all=args.all, debug=args.debug)

        print(f"\nFound {len(sessions)} session(s):")
        for s in sessions:
            link_count = len(s["links"])
            print(f"  {s['title']} — {link_count} link(s)")

        write_session_markdown(sessions)

        page.close()
        context.close()
        browser.close()

    print("\nDone.")


if __name__ == "__main__":
    main()
