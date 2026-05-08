#!/usr/bin/env python3
"""Validate the MCX disclosure schema and all example records.

Usage:
    python3 scripts/validate.py

Exit code 0 if everything validates; non-zero otherwise.

Format checks (uri, email, uuid, date, date-time) are enforced via
FormatChecker. For full coverage of all formats, install the optional
extras: ``pip install jsonschema[format]`` (this pulls in
rfc3339-validator, rfc3987, idna, webcolors, jsonpointer, etc.).
Without the extras, basic format checks still run; some advanced ones
become permissive.
"""

import json
import sys
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "schemas" / "mcx-disclosure-v0.1.schema.json"
EVENT_SCHEMA_PATH = ROOT / "schemas" / "events" / "mcx-event-v0.1.schema.json"
EXAMPLES_DIR = ROOT / "examples"


def load_json(path: Path):
    with path.open() as f:
        return json.load(f)


def main() -> int:
    failed = False

    # 1. Validate the schemas themselves are valid JSON Schema documents
    print("Validating schema documents...")
    for schema_path in [SCHEMA_PATH, EVENT_SCHEMA_PATH]:
        try:
            schema = load_json(schema_path)
            Draft202012Validator.check_schema(schema)
            print(f"  ok  {schema_path.relative_to(ROOT)}")
        except Exception as e:
            print(f"  FAIL  {schema_path.relative_to(ROOT)}: {e}")
            failed = True

    # 2. Validate all example records against the disclosure schema.
    #    FormatChecker enforces uri / email / uuid / date / date-time
    #    rather than treating them as advisory annotations.
    print("\nValidating example records (with format checking)...")
    schema = load_json(SCHEMA_PATH)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())

    for example_path in sorted(EXAMPLES_DIR.glob("*.json")):
        instance = load_json(example_path)
        errors = sorted(validator.iter_errors(instance), key=lambda e: list(e.path))
        rel = example_path.relative_to(ROOT)
        if errors:
            print(f"  FAIL  {rel}: {len(errors)} error(s)")
            for err in errors[:10]:
                path = ".".join(str(p) for p in err.path) or "(root)"
                print(f"        - {path}: {err.message}")
            failed = True
        else:
            print(f"  ok  {rel}")

    print()
    if failed:
        print("VALIDATION FAILED")
        return 1
    print("All checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
