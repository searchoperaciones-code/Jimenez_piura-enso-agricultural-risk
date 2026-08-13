from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
WINDOWS = ROOT / "data" / "processed" / "phenology" / "phenology_windows_frozen.csv"
CERTIFICATE = ROOT / "outputs" / "phenology" / "PHENOLOGY_MASTER_V1_FREEZE.md"
QA = ROOT / "outputs" / "phenology" / "qa"
REPORT = QA / "phenology_freeze_gate_report.json"
MANIFEST = QA / "phenology_freeze_manifest.csv"

SCHEMA = [
    "COD_CULTIVO",
    "CROP_STD",
    "ARCHITECTURE",
    "WINDOW_ID",
    "ANCHOR_VARIABLE",
    "ANCHOR_SEMANTICS",
    "WINDOW_RULE",
    "START_OFFSET_MONTH",
    "END_OFFSET_MONTH",
    "START_DAS",
    "END_DAS",
    "CALENDAR_MONTH_START",
    "CALENDAR_MONTH_END",
    "YEAR_RELATION",
    "YEAR_OFFSET",
    "COHORT_WEIGHTING",
    "FREEZE_STATUS",
    "FREEZE_VERSION",
    "NOTES",
]

EXPECTED_CODES = {"14010020000", "14010070000", "13010210000", "13010170102", "15010040000"}
FORBIDDEN_TEXT = {
    "YIELD_RAW",
    "PRECIO",
    "P_VALUE",
    "PVALUE",
    "P-VALUE",
    "MODEL_FIT",
    "RSQUARED",
    "R_SQUARED",
    "AIC",
    "BIC",
    "REGRESSION",
    "CORRELATION",
    "SIGNIFICANCE",
    "OPTIMIZATION",
}


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8"))


def write_manifest(status: str) -> None:
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "artifact": rel(WINDOWS),
            "sha256": sha256_file(WINDOWS) if WINDOWS.exists() else "",
            "role": "CANONICAL_PHENOLOGY_WINDOWS",
            "status": status,
        },
        {
            "artifact": rel(CERTIFICATE),
            "sha256": sha256_file(CERTIFICATE) if CERTIFICATE.exists() else "",
            "role": "PHENOLOGY_MASTER_V1_FREEZE_CERTIFICATE",
            "status": status,
        },
    ]
    with MANIFEST.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["artifact", "sha256", "role", "status"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def read_rows() -> tuple[list[str] | None, list[dict[str, str]]]:
    if not WINDOWS.exists():
        return None, []
    with WINDOWS.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return reader.fieldnames, list(reader)


def as_int(value: str) -> int | None:
    if value == "":
        return None
    return int(value)


def row_by_window(rows: list[dict[str, str]], window_id: str) -> dict[str, str] | None:
    matches = [row for row in rows if row["WINDOW_ID"] == window_id]
    return matches[0] if len(matches) == 1 else None


def check(condition: bool, name: str, checks: list[dict[str, Any]], detail: Any = None) -> None:
    checks.append({"check": name, "status": "PASS" if condition else "FAIL", "detail": detail})


def check_row_values(row: dict[str, str] | None, expected: dict[str, str], checks: list[dict[str, Any]], prefix: str) -> None:
    check(row is not None, f"{prefix}_ROW_EXISTS", checks)
    if row is None:
        return
    for column, expected_value in expected.items():
        check(row[column] == expected_value, f"{prefix}_{column}", checks, {"actual": row[column], "expected": expected_value})


def evaluate() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    fieldnames, rows = read_rows()

    check(WINDOWS.exists(), "WINDOWS_FILE_EXISTS", checks, rel(WINDOWS))
    check(CERTIFICATE.exists(), "FREEZE_CERTIFICATE_EXISTS", checks, rel(CERTIFICATE))
    check(fieldnames == SCHEMA, "EXACT_SCHEMA", checks, {"actual": fieldnames, "expected": SCHEMA})
    check(len(rows) == 7, "EXACT_ROW_COUNT", checks, len(rows))

    if fieldnames == SCHEMA:
        codes = {row["COD_CULTIVO"] for row in rows}
        window_ids = [row["WINDOW_ID"] for row in rows]
        text = " ".join(SCHEMA + [value for row in rows for value in row.values()]).upper()

        check(len(codes) == 5, "EXACT_UNIQUE_CROP_COUNT", checks, sorted(codes))
        check(codes == EXPECTED_CODES, "EXACT_CROP_CODES", checks, sorted(codes))
        check(len(window_ids) == len(set(window_ids)), "NO_DUPLICATE_WINDOW_ID", checks, window_ids)
        check(all(row["FREEZE_STATUS"] == "PASS_FROZEN" for row in rows), "FREEZE_STATUS_PASS_FROZEN", checks)
        check(all(row["FREEZE_VERSION"] == "v1" for row in rows), "FREEZE_VERSION_V1", checks)
        check("YIELD_RAW" not in text and "PRECIO" not in text, "NO_YIELD_OR_PRICE_TEXT", checks)
        check(not any(token in text for token in FORBIDDEN_TEXT - {"YIELD_RAW", "PRECIO"}), "NO_MODEL_FIT_OR_PVALUE_SELECTION_TEXT", checks)

        check_row_values(
            row_by_window(rows, "RICE_FLOWERING_95_110_DAS"),
            {
                "COD_CULTIVO": "14010020000",
                "ARCHITECTURE": "SOWING_COHORT_WEIGHTED",
                "ANCHOR_VARIABLE": "SIEMBRA",
                "ANCHOR_SEMANTICS": "TRANSPLANT_ESTABLISHMENT_PROXY",
                "START_DAS": "95",
                "END_DAS": "110",
                "START_OFFSET_MONTH": "3",
                "END_OFFSET_MONTH": "4",
                "WINDOW_RULE": "DAS_95_110",
                "COHORT_WEIGHTING": "SIEMBRA_SHARE",
            },
            checks,
            "RICE",
        )
        check_row_values(
            row_by_window(rows, "MAD_MPLUS1_MPLUS3"),
            {
                "COD_CULTIVO": "14010070000",
                "ARCHITECTURE": "SOWING_COHORT_WEIGHTED",
                "ANCHOR_VARIABLE": "SIEMBRA",
                "START_OFFSET_MONTH": "1",
                "END_OFFSET_MONTH": "3",
                "WINDOW_RULE": "MONTH_OFFSET",
                "COHORT_WEIGHTING": "SIEMBRA_SHARE",
            },
            checks,
            "MAD",
        )

        mango_rows = [row for row in rows if row["COD_CULTIVO"] == "13010210000"]
        check(len(mango_rows) == 1, "MANGO_SINGLE_WINDOW", checks, len(mango_rows))
        if mango_rows:
            mango = mango_rows[0]
            check(mango["ARCHITECTURE"] == "SEASONAL_PERENNIAL", "MANGO_ARCHITECTURE", checks)
            check(as_int(mango["CALENDAR_MONTH_START"]) == 5 and as_int(mango["CALENDAR_MONTH_END"]) == 6, "MANGO_MAY_JUNE", checks)
            check(as_int(mango["YEAR_OFFSET"]) == 0, "MANGO_CURRENT_YEAR", checks)
            check(mango["YEAR_RELATION"] != "PREVIOUS_YEAR", "MANGO_NO_PREVIOUS_YEAR_WINDOW", checks)

        lemon_rows = [row for row in rows if row["COD_CULTIVO"] == "13010170102"]
        check(len(lemon_rows) == 2, "LEMON_EXACTLY_TWO_WINDOWS", checks, len(lemon_rows))
        check(all(row["ARCHITECTURE"] == "RECURRENT_PERENNIAL_BROAD" for row in lemon_rows), "LEMON_ARCHITECTURE", checks)
        check(all(as_int(row["CALENDAR_MONTH_START"]) == 1 and as_int(row["CALENDAR_MONTH_END"]) == 12 for row in lemon_rows), "LEMON_FULL_YEAR", checks)
        check({as_int(row["YEAR_OFFSET"]) for row in lemon_rows} == {0, -1}, "LEMON_YEAR_OFFSETS", checks)

        banana_rows = [row for row in rows if row["COD_CULTIVO"] == "15010040000"]
        check(len(banana_rows) == 2, "BANANA_EXACTLY_TWO_WINDOWS", checks, len(banana_rows))
        check(all(row["ARCHITECTURE"] == "MULTISTAGE_CONTINUOUS" for row in banana_rows), "BANANA_ARCHITECTURE", checks)
        check(all(as_int(row["CALENDAR_MONTH_START"]) == 1 and as_int(row["CALENDAR_MONTH_END"]) == 12 for row in banana_rows), "BANANA_FULL_YEAR", checks)
        check({as_int(row["YEAR_OFFSET"]) for row in banana_rows} == {0, -1}, "BANANA_YEAR_OFFSETS", checks)

    status = "PASS" if checks and all(item["status"] == "PASS" for item in checks) else "FAIL"
    return {
        "artifact": rel(WINDOWS),
        "checks": checks,
        "failed_checks": [item for item in checks if item["status"] != "PASS"],
        "row_count": len(rows),
        "stage": "PHENOLOGY_MASTER_v1_EVIDENCE_ARCHITECTURE_FREEZE",
        "status": status,
        "unique_crop_count": len({row["COD_CULTIVO"] for row in rows}) if rows and fieldnames == SCHEMA else 0,
    }


def main() -> int:
    report = evaluate()
    write_json(REPORT, report)
    write_manifest(report["status"])
    print(json.dumps({"stage": report["stage"], "status": report["status"]}, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
