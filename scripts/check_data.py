import sys
import os
import csv
import logging

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

DATA_PATH = os.getenv("DATA_PATH", "data/patients.csv")

REQUIRED_COLUMNS = {
    "patient_id",
    "age",
    "gender",
    "blood_pressure_systolic",
    "blood_pressure_diastolic",
    "cholesterol",
    "glucose",
    "risk_label",
}

COLUMN_TYPES = {
    "patient_id": str,
    "age": int,
    "gender": str,
    "blood_pressure_systolic": int,
    "blood_pressure_diastolic": int,
    "cholesterol": float,
    "glucose": float,
    "risk_label": int,
}

VALID_GENDERS = {"M", "F", "O"}
VALID_RISK_LABELS = {0, 1}
MIN_ROWS = 5
MAX_MISSING_PCT = 0.05


def load_csv(path):
    if not os.path.exists(path):
        log.error(f"Dataset not found at '{path}'")
        sys.exit(1)
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    log.info(f"Loaded {len(rows)} rows from '{path}'")
    return rows


def check_schema(rows):
    if not rows:
        log.error("Dataset is empty.")
        sys.exit(1)
    missing = REQUIRED_COLUMNS - set(rows[0].keys())
    if missing:
        log.error(f"Schema violation - missing columns: {missing}")
        sys.exit(1)
    log.info("Schema check PASSED")


def check_row_count(rows):
    if len(rows) < MIN_ROWS:
        log.error(f"Insufficient data: {len(rows)} rows (minimum: {MIN_ROWS})")
        sys.exit(1)
    log.info(f"Row count check PASSED ({len(rows)} rows)")


def check_types_and_values(rows):
    errors = []
    missing_count = {col: 0 for col in REQUIRED_COLUMNS}

    for i, row in enumerate(rows, start=2):
        for col in REQUIRED_COLUMNS:
            val = row.get(col, "").strip()

            if val == "" or val is None:
                missing_count[col] += 1
                continue

            try:
                coerced = COLUMN_TYPES[col](val)
            except (ValueError, TypeError):
                errors.append(f"Row {i}, col '{col}': cannot cast '{val}' to {COLUMN_TYPES[col].__name__}")
                continue

            if col == "gender" and str(coerced).upper() not in VALID_GENDERS:
                errors.append(f"Row {i}, col 'gender': invalid value '{coerced}'")
            if col == "risk_label" and int(coerced) not in VALID_RISK_LABELS:
                errors.append(f"Row {i}, col 'risk_label': invalid value '{coerced}'")
            if col == "age" and not (0 < int(coerced) < 130):
                errors.append(f"Row {i}, col 'age': out of range '{coerced}'")
            if col in ("blood_pressure_systolic", "blood_pressure_diastolic"):
                if not (0 < int(coerced) < 300):
                    errors.append(f"Row {i}, col '{col}': out of range '{coerced}'")

    total = len(rows)
    for col, count in missing_count.items():
        rate = count / total
        if rate > MAX_MISSING_PCT:
            errors.append(f"Column '{col}': missing rate {rate:.1%} exceeds threshold {MAX_MISSING_PCT:.0%}")

    if errors:
        log.error(f"Found {len(errors)} data quality error(s):")
        for e in errors:
            log.error(f"  {e}")
        sys.exit(1)

    log.info("Type and value check PASSED")


def generate_report(rows):
    total = len(rows)
    risk_counts = {}
    for row in rows:
        label = row.get("risk_label", "unknown")
        risk_counts[label] = risk_counts.get(label, 0) + 1
    log.info("Quality Report:")
    log.info(f"  Total records: {total}")
    for label, count in sorted(risk_counts.items()):
        log.info(f"  risk_label={label}: {count} ({count/total:.1%})")


def main():
    log.info("Safe-Health Data Integrity Audit")
    rows = load_csv(DATA_PATH)
    check_schema(rows)
    check_row_count(rows)
    check_types_and_values(rows)
    generate_report(rows)
    log.info("ALL CHECKS PASSED - data is cleared for pipeline")


if __name__ == "__main__":
    main()
