"""
Unified sleep data converter
============================
Converts sleep data from 4 different formats into a single unified CSV.
Automatically detects format based on filename keyword in DATA_DIR.

To add a new person:
    1. Add a parser in converters/<name>.py with a parse() function
    2. Add an entry to FORMAT_MAP below
"""

import csv
import logging
import sys
from pathlib import Path

from utils import FIELDNAMES
from converters import bilgin, mifitness, pieter, rayan

# ── CONFIG ────────────────────────────────────────────────────────────────────

DATA_DIR   = Path('data')
OUTPUT_DIR = Path('output')

# Maps filename keyword (lowercase) → (format, user_id override or None)
FORMAT_MAP = {
    'bilgin':                     ('bilgin',    None),
    'junior':                     ('mifitness', None),
    'pieter':                     ('pieter',    'pieter'),
    'sleep_data_extracted_newer': ('pieter',    'pieter'),
    'rayan':                      ('ods',       None),
}

# ── LOGGING ───────────────────────────────────────────────────────────────────

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# ── HELPERS ───────────────────────────────────────────────────────────────────

def detect_format(file: Path) -> tuple[str, str | None] | None:
    for keyword, (fmt, uid_override) in FORMAT_MAP.items():
        if keyword.lower() in file.name.lower():
            return fmt, uid_override
    return None


def detect_user_id(file: Path) -> str:
    return file.stem.split('_')[0].lower()


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    for file in sorted(DATA_DIR.iterdir()):
        result = detect_format(file)
        if result is None:
            logging.warning("Skipping '%s' — no format match in FORMAT_MAP", file.name)
            continue

        fmt, uid_override = result
        user_id = uid_override or detect_user_id(file)
        logging.info("Parsing '%s' as format '%s' for user '%s'", file.name, fmt, user_id)

        try:
            if fmt == 'bilgin':
                rows = list(bilgin.parse(file))
            elif fmt == 'mifitness':
                rows = list(mifitness.parse(file))
            elif fmt == 'pieter':
                rows = list(pieter.parse(file, user_id))
            elif fmt == 'ods':
                rows = list(rayan.parse(file, user_id))
            else:
                logging.error("Unknown format '%s'", fmt)
                continue
        except Exception as e:
            logging.error("Failed to parse '%s': %s", file.name, e)
            continue

        if not rows:
            logging.warning("No rows found in '%s'", file.name)
            continue

        output = OUTPUT_DIR / f'sleep_{user_id}.csv'
        with open(output, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()
            writer.writerows(rows)

        logging.info("Saved %d rows to %s", len(rows), output)


if __name__ == '__main__':
    main()
