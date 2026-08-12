from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
BASE_SHA = "e4710b1429ed54c557e6c0a88212a24a6fdd7d47"
STAGE_A_VERSION = "PHENOLOGY_MASTER_v1_STAGE_A"

RAW_GORE = ROOT / "data" / "raw" / "Formato_dataset_productos_dra__ (2).csv"
SEED_PATH = ROOT / "config" / "phenology" / "PHENOLOGY_EVIDENCE_REGISTRY_SEED.csv"

TARGET_CROPS = {
    "14010020000": "ARROZ",
    "13010210000": "MANGO",
    "13010170102": "LIMON SUTIL",
    "15010040000": "PLATANOS Y BANANAS",
    "14010070000": "MAIZ AMARILLO DURO",
}
TRANSIENT_CROPS = {"14010020000", "14010070000"}
PERMANENT_CROPS = {"13010210000", "13010170102", "15010040000"}
AUTHORIZED_COLUMNS = ["UBIGEO", "ANO", "MES", "COD_CULTIVO", "CULTIVO", "SIEMBRA", "COSECHA", "PRODUCCION"]
MAIN_YEARS = list(range(2016, 2024))
DIAGNOSTIC_LAGS = list(range(1, 13))

INPUT_HASHES = {
    "data/raw/Formato_dataset_productos_dra__ (2).csv": "7953e95f532b97f3db1ad42dfb517dc0b5f6e98a80b1f1b0954fc1b52419c489",
    "data/raw/Formato_DiccionarioDatos_productos_dra_.xlsx": "9df8aedf987a7a882d265ffc629d105f8058a5208738d5dcd1b213b30d347ce0",
    "data/raw/Formato_Metadatos_productos_dra_.docx": "a66ede624b8d2f502df65620c84233dd04a9ebcc29ae9969c38e2272ec812ea7",
    "data/raw/superficie_agricola_nacional_2024.xlsx": "36f9f5d41489df4c4e19b8108c339088dd6ee2f240669d47683163077e1d9b7c",
    "data/raw/ICEN.txt": "53e82d90ad26335b081ddebf67f9293477cf6f80e3d7d9de17ddfe33fab8c03f",
    "data/processed/panel_master.csv": "ab9b4ce53c008a1bc3ceb7d3e4c5d617d2544ad48632b747079c33e8b95d1214",
    "data/processed/panel_balanceado.csv": "3b406d0bdec12414c58a14bd5f4e71ec708bc87910e9c06b182dfd2e043122a1",
    "data/processed/climate/climate_monthly_primary.parquet": "23c3232e69a6b4786e544d875575e6f3a98dc16f6048d3bd0a794e4420b04fd3",
    "config/phenology/PHENOLOGY_EVIDENCE_REGISTRY_SEED.csv": "12e5653ce99e97eff85bd5246a61cb9b105f1fab51ab72c33c59d8c1fab0f885",
}
PROTECTED_PATHS = [
    "data/processed/panel_master.csv",
    "data/processed/panel_balanceado.csv",
    "data/processed/climate",
    "outputs/qa",
    "outputs/figures/climate_qa",
    "outputs/repository",
]
ALLOWED_ROLE_TOKENS = {
    "WINDOW_ANCHOR_CANDIDATE",
    "DURATION_ANCHOR_CANDIDATE",
    "PHENOPHASE_DEFINITION",
    "DURATION_HETEROGENEITY",
    "MECHANISM_ONLY",
    "MECHANISM",
    "LOCAL_MECHANISM",
    "LOCAL_SEASONAL_CONTEXT",
    "CONTEXT",
    "EXCLUDED",
}
ALLOWED_AUTHORITIES = {
    "PERU_OFFICIAL_TECHNICAL",
    "INTERNATIONAL_OFFICIAL_GUIDELINE",
    "PEER_REVIEWED_PRIMARY",
    "PEER_REVIEWED_REVIEW",
}
CORE_RELATIVE_OUTPUTS = [
    "processed/phenology_evidence_registry.csv",
    "processed/temporal_structure_monthly.csv",
    "processed/temporal_structure_summary.csv",
    "qa/transient_lag_compatibility.csv",
    "qa/year_crossing_audit.csv",
    "qa/left_truncation_2016.csv",
    "qa/stage_a_schema.json",
]


def stage_dirs(output_root: Path | None = None) -> dict[str, Path]:
    if output_root is None:
        return {
            "processed": ROOT / "data" / "processed" / "phenology",
            "outputs": ROOT / "outputs" / "phenology",
            "qa": ROOT / "outputs" / "phenology" / "qa",
        }
    return {
        "processed": output_root / "processed",
        "outputs": output_root / "outputs",
        "qa": output_root / "qa",
    }


def ensure_dirs(dirs: dict[str, Path]) -> None:
    for path in dirs.values():
        path.mkdir(parents=True, exist_ok=True)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, lineterminator="\n")


def run_git(args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=check)


def git_lines(args: list[str]) -> list[str]:
    result = run_git(args)
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def branch_name() -> str:
    return run_git(["rev-parse", "--abbrev-ref", "HEAD"]).stdout.strip()


def head_sha() -> str:
    return run_git(["rev-parse", "HEAD"]).stdout.strip()


def base_is_ancestor() -> bool:
    return run_git(["merge-base", "--is-ancestor", BASE_SHA, "HEAD"], check=False).returncode == 0


def protected_diff() -> list[str]:
    return git_lines(["diff", "--name-only", BASE_SHA, "--", *PROTECTED_PATHS])


def protected_status() -> list[str]:
    return git_lines(["status", "--short", "--", *PROTECTED_PATHS])


def verify_upstream_integrity(dirs: dict[str, Path]) -> dict[str, Any]:
    checks = []
    for rel_path, expected in INPUT_HASHES.items():
        path = ROOT / rel_path
        exists = path.exists()
        actual = sha256_file(path) if exists else None
        checks.append(
            {
                "path": rel_path,
                "expected_sha256": expected,
                "actual_sha256": actual,
                "match": exists and actual == expected,
                "file_size": path.stat().st_size if exists else None,
                "exists": exists,
            }
        )
    diff = protected_diff()
    status = protected_status()
    report = {
        "stage": STAGE_A_VERSION,
        "base_sha": BASE_SHA,
        "head_sha": head_sha(),
        "branch": branch_name(),
        "base_is_ancestor": base_is_ancestor(),
        "input_hashes": checks,
        "protection_status": {
            "protected_paths": PROTECTED_PATHS,
            "diff_vs_base": diff,
            "working_tree_status": status,
            "protected_paths_modified": bool(diff or status),
        },
        "status": "PASS" if all(item["match"] for item in checks) and base_is_ancestor() and not diff and not status else "FAIL",
    }
    write_json(dirs["qa"] / "upstream_integrity_report.json", report)
    if report["status"] != "PASS":
        raise RuntimeError("UPSTREAM_FREEZE_INTEGRITY_FAIL")
    return report


def build_evidence_registry(dirs: dict[str, Path]) -> tuple[pd.DataFrame, dict[str, Any]]:
    if not SEED_PATH.exists():
        raise RuntimeError("PHENOLOGY_EVIDENCE_SEED_MISSING")
    seed_hash = sha256_file(SEED_PATH)
    seed = pd.read_csv(SEED_PATH, dtype="string", keep_default_na=False)
    required = [
        "evidence_id",
        "crop_code",
        "citation",
        "institution_or_journal",
        "doi_or_url",
        "source_authority",
        "transferability",
        "decision_role",
    ]
    missing_columns = [col for col in required if col not in seed.columns]
    nonblank = {col: bool(seed[col].astype(str).str.strip().ne("").all()) for col in required if col in seed.columns}
    unique_ids = "evidence_id" in seed.columns and seed["evidence_id"].astype(str).str.strip().is_unique
    role_tokens: set[str] = set()
    for roles in seed.get("decision_role", pd.Series(dtype="string")).astype(str):
        role_tokens.update(token.strip() for token in roles.split(";") if token.strip())
    unknown_roles = sorted(role_tokens - ALLOWED_ROLE_TOKENS)
    authorities = set(seed.get("source_authority", pd.Series(dtype="string")).astype(str).str.strip())
    unknown_authorities = sorted(authorities - ALLOWED_AUTHORITIES)
    crop_codes = set(seed.get("crop_code", pd.Series(dtype="string")).astype(str).str.strip())
    target_coverage = sorted(set(TARGET_CROPS) & crop_codes)
    invalid_crop_codes = sorted(crop_codes - set(TARGET_CROPS) - {"ALL"})

    registry = seed.sort_values("evidence_id", kind="mergesort").reset_index(drop=True)
    registry["stage_a_registry_status"] = "INGESTED_NOT_WINDOW_FREEZE"
    registry["evidence_freeze_status"] = "PENDING_DIRECTOR_FULLTEXT_REVIEW"
    registry["stage_a_candidate_promotion"] = "NO"
    write_csv(registry, dirs["processed"] / "phenology_evidence_registry.csv")

    page_locator_preserved = True
    if "page_table_figure_section" in seed.columns:
        before = seed.sort_values("evidence_id", kind="mergesort")["page_table_figure_section"].astype(str).tolist()
        after = registry["page_table_figure_section"].astype(str).tolist()
        page_locator_preserved = before == after
    fulltext_preserved = True
    if "fulltext_verified" in seed.columns:
        before = seed.sort_values("evidence_id", kind="mergesort")["fulltext_verified"].astype(str).tolist()
        after = registry["fulltext_verified"].astype(str).tolist()
        fulltext_preserved = before == after
    candidate_roles_preserved = registry["decision_role"].astype(str).str.contains("_CANDIDATE", regex=False).any()

    vocabulary_review_required = bool(unknown_roles or unknown_authorities or invalid_crop_codes)
    gate_pass = (
        seed_hash == INPUT_HASHES["config/phenology/PHENOLOGY_EVIDENCE_REGISTRY_SEED.csv"]
        and not missing_columns
        and all(nonblank.values())
        and unique_ids
        and len(target_coverage) == 5
        and not vocabulary_review_required
        and page_locator_preserved
        and fulltext_preserved
        and candidate_roles_preserved
    )
    report = {
        "stage": STAGE_A_VERSION,
        "seed_path": str(SEED_PATH.relative_to(ROOT)),
        "seed_sha256": seed_hash,
        "seed_hash_match": seed_hash == INPUT_HASHES["config/phenology/PHENOLOGY_EVIDENCE_REGISTRY_SEED.csv"],
        "rows": int(len(registry)),
        "evidence_id_unique_nonblank": bool(unique_ids and nonblank.get("evidence_id", False)),
        "required_metadata_nonblank": nonblank,
        "missing_required_columns": missing_columns,
        "target_crop_codes_represented": target_coverage,
        "target_crop_count": len(target_coverage),
        "context_all_rows": int((registry["crop_code"].astype(str).str.strip() == "ALL").sum()) if "crop_code" in registry.columns else 0,
        "unknown_role_tokens": unknown_roles,
        "unknown_source_authorities": unknown_authorities,
        "invalid_crop_codes": invalid_crop_codes,
        "vocabulary_review_required": vocabulary_review_required,
        "candidate_roles_preserved_not_promoted": bool(candidate_roles_preserved),
        "page_table_figure_section_preserved": page_locator_preserved,
        "fulltext_verified_preserved": fulltext_preserved,
        "live_url_accessibility_gate": "NOT_USED_STAGE_A",
        "status": "PASS" if gate_pass else "FAIL",
    }
    if vocabulary_review_required:
        report["hold_reason"] = "VOCABULARY_REVIEW_REQUIRED"
    write_json(dirs["qa"] / "evidence_gate_report.json", report)
    if not gate_pass:
        raise RuntimeError("EVIDENCE_REGISTRY_GATE_FAIL")
    return registry, report


def read_authorized_raw() -> pd.DataFrame:
    df = pd.read_csv(
        RAW_GORE,
        usecols=AUTHORIZED_COLUMNS,
        dtype={"UBIGEO": "string", "COD_CULTIVO": "string", "CULTIVO": "string"},
        keep_default_na=True,
    )
    df["UBIGEO"] = df["UBIGEO"].astype("string").str.zfill(6)
    df["COD_CULTIVO"] = df["COD_CULTIVO"].astype("string").str.strip()
    for col in ["ANO", "MES", "SIEMBRA", "COSECHA", "PRODUCCION"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["ANO"] = df["ANO"].astype("Int64")
    df["MES"] = df["MES"].astype("Int64")
    df["MONTH"] = (df["MES"] % 100).astype("Int64")
    df["MES_TEXT"] = df["MES"].astype("string")
    df["CROP_STD"] = df["COD_CULTIVO"].map(TARGET_CROPS).astype("string")
    return df


def temporal_role(year: int) -> str:
    if year == 2015:
        return "AUG_DEC_ANTECEDENT_SUPPORT_ONLY"
    if 2016 <= year <= 2023:
        return "MAIN_TEMPORAL_STRUCTURE"
    if year == 2024:
        return "CONTEXTUAL_ONLY_NOT_FOR_SELECTION"
    return "OUT_OF_STAGE_A_SCOPE"


def denominator_status(values: pd.Series, source_months: int) -> tuple[float | None, int, int, str, bool]:
    missing = int(values.isna().sum())
    positive = int((values > 0).sum(skipna=True))
    denom_value = values.sum(min_count=1)
    denom = None if pd.isna(denom_value) else float(denom_value)
    has_12 = source_months == 12
    if missing == source_months:
        status = "ALL_MISSING"
    elif missing > 0 or not has_12:
        status = "PARTIAL_MISSING"
    elif denom is not None and denom > 0:
        status = "POSITIVE"
    elif denom == 0:
        status = "ZERO"
    else:
        status = "ALL_MISSING"
    return denom, missing, positive, status, has_12


def normalize_vector(values: list[float | None]) -> tuple[np.ndarray | None, float | None, int, int, str]:
    arr = np.array([np.nan if value is None else value for value in values], dtype=float)
    missing = int(np.isnan(arr).sum())
    positive = int(np.nansum(arr > 0))
    denom_value = np.nansum(arr) if missing < len(arr) else np.nan
    if missing == len(arr):
        return None, None, missing, positive, "ALL_MISSING"
    if missing > 0:
        return None, float(denom_value), missing, positive, "PARTIAL_MISSING"
    if denom_value > 0:
        return arr / denom_value, float(denom_value), missing, positive, "POSITIVE"
    return None, float(denom_value), missing, positive, "ZERO"


def normalized_entropy(shares: list[float] | np.ndarray) -> float | None:
    p = np.asarray(shares, dtype=float)
    if p.shape[0] != 12 or np.isnan(p).any() or np.any(p < 0) or not np.isclose(p.sum(), 1.0):
        return None
    positive = p[p > 0]
    if positive.size == 0:
        return None
    return float(-(positive * np.log(positive)).sum() / np.log(12.0))


def circular_concentration(shares: list[float] | np.ndarray) -> tuple[float | None, float | None, float | None]:
    p = np.asarray(shares, dtype=float)
    if p.shape[0] != 12 or np.isnan(p).any() or np.any(p < 0) or not np.isclose(p.sum(), 1.0):
        return None, None, None
    theta = 2 * np.pi * np.arange(12) / 12.0
    z = np.sum(p * np.exp(1j * theta))
    radius = float(abs(z))
    if radius < 1e-12:
        return radius, None, None
    angle = float(np.angle(z) % (2 * np.pi))
    month = float((angle / (2 * np.pi)) * 12.0 + 1.0)
    if month > 12.0:
        month -= 12.0
    return radius, angle, month


def cyclic_k_arc(shares: list[float] | np.ndarray, threshold: float) -> dict[str, Any]:
    p = np.asarray(shares, dtype=float)
    if p.shape[0] != 12 or np.isnan(p).any() or np.any(p < 0) or not np.isclose(p.sum(), 1.0):
        return {"k": None, "start_month": None, "end_month": None, "captured_share": None}
    candidates = []
    for length in range(1, 13):
        for start_idx in range(12):
            idx = [(start_idx + offset) % 12 for offset in range(length)]
            captured = float(p[idx].sum())
            if captured + 1e-12 >= threshold:
                end_month = ((start_idx + length - 1) % 12) + 1
                candidates.append((length, -captured, start_idx + 1, end_month, captured))
        if candidates:
            candidates.sort()
            length, neg_capture, start_month, end_month, captured = candidates[0]
            return {
                "k": int(length),
                "start_month": int(start_month),
                "end_month": int(end_month),
                "captured_share": float(-neg_capture if not np.isclose(-neg_capture, captured) else captured),
            }
    return {"k": None, "start_month": None, "end_month": None, "captured_share": None}


def add_months(year: int, month: int, delta: int) -> tuple[int, int, int]:
    zero_based = year * 12 + (month - 1) + delta
    new_year = zero_based // 12
    new_month = zero_based % 12 + 1
    return int(new_year), int(new_month), int(new_year * 100 + new_month)


def js_divergence(p: np.ndarray, q: np.ndarray) -> float:
    m = 0.5 * (p + q)

    def kl(a: np.ndarray, b: np.ndarray) -> float:
        mask = a > 0
        return float(np.sum(a[mask] * np.log(a[mask] / b[mask])))

    return 0.5 * kl(p, m) + 0.5 * kl(q, m)


def temporal_structure_audit(raw: pd.DataFrame, dirs: dict[str, Path]) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    target = raw[raw["COD_CULTIVO"].isin(TARGET_CROPS)].copy()
    target = target.sort_values(["UBIGEO", "COD_CULTIVO", "ANO", "MONTH"], kind="mergesort")
    group_cols = ["UBIGEO", "COD_CULTIVO", "ANO"]
    rows = []
    summaries = []
    for keys, group in target.groupby(group_cols, sort=True, dropna=False):
        ubigeo, crop_code, year = keys
        year_int = int(year)
        source_months = int(group["MONTH"].nunique(dropna=True))
        ordered = group.sort_values("MONTH", kind="mergesort")
        records = ordered.to_dict("records")
        month_values_by_variable = {
            var: {
                int(record["MONTH"]): None if pd.isna(record[var]) else float(record[var])
                for record in records
            }
            for var in ["SIEMBRA", "COSECHA", "PRODUCCION"]
        }
        stats: dict[str, tuple[float | None, int | None, int | None, str, bool | None]] = {}
        for var in ["SIEMBRA", "COSECHA"]:
            stats[var] = denominator_status(group[var], source_months)
        if crop_code in PERMANENT_CROPS:
            stats["PRODUCCION"] = denominator_status(group["PRODUCCION"], source_months)
        else:
            stats["PRODUCCION"] = (None, None, None, "NOT_COMPUTED_TRANSIENT", None)

        for record in records:
            out = {
                "UBIGEO": str(ubigeo),
                "COD_CULTIVO": str(crop_code),
                "CROP_STD": TARGET_CROPS[str(crop_code)],
                "CULTIVO_SOURCE": record["CULTIVO"],
                "ANO": year_int,
                "MES": int(record["MES"]),
                "MONTH": int(record["MONTH"]),
                "TEMPORAL_ROLE": temporal_role(year_int),
                "SOURCE_12_MONTHS_PRESENT": source_months == 12,
                "SIEMBRA": record["SIEMBRA"],
                "COSECHA": record["COSECHA"],
                "PRODUCCION": record["PRODUCCION"] if crop_code in PERMANENT_CROPS else np.nan,
            }
            for var, prefix in [("SIEMBRA", "SOWN"), ("COSECHA", "HARVEST"), ("PRODUCCION", "PRODUCTION")]:
                denom, missing, positive, status, has_12 = stats[var]
                out[f"{prefix}_ANNUAL_DENOMINATOR"] = denom
                out[f"{prefix}_MISSING_MONTH_COUNT"] = missing
                out[f"{prefix}_POSITIVE_MONTH_COUNT"] = positive
                out[f"{prefix}_DENOMINATOR_STATUS"] = status
                out[f"{prefix}_SOURCE_12_MONTHS_PRESENT"] = has_12
                allowed_production = var != "PRODUCCION" or crop_code in PERMANENT_CROPS
                if status == "POSITIVE" and denom and allowed_production:
                    out[f"{prefix}_SHARE"] = float(record[var]) / denom if pd.notna(record[var]) else np.nan
                else:
                    out[f"{prefix}_SHARE"] = np.nan
            rows.append(out)

        for var, prefix in [("SIEMBRA", "SOWN"), ("COSECHA", "HARVEST"), ("PRODUCCION", "PRODUCTION")]:
            if var == "PRODUCCION" and crop_code not in PERMANENT_CROPS:
                continue
            share_col = []
            denom, _, _, status, _ = stats[var]
            values_by_month = month_values_by_variable[var]
            for month in range(1, 13):
                value = values_by_month.get(month)
                share_col.append(np.nan if status != "POSITIVE" or not denom or value is None else value / denom)
            valid = not np.isnan(np.asarray(share_col, dtype=float)).any()
            entropy = normalized_entropy(share_col) if valid else None
            radius, angle, mean_month = circular_concentration(share_col) if valid else (None, None, None)
            k50 = cyclic_k_arc(share_col, 0.50) if valid else {"k": None, "start_month": None, "end_month": None, "captured_share": None}
            k75 = cyclic_k_arc(share_col, 0.75) if valid else {"k": None, "start_month": None, "end_month": None, "captured_share": None}
            k90 = cyclic_k_arc(share_col, 0.90) if valid else {"k": None, "start_month": None, "end_month": None, "captured_share": None}
            summaries.append(
                {
                    "UBIGEO": str(ubigeo),
                    "COD_CULTIVO": str(crop_code),
                    "CROP_STD": TARGET_CROPS[str(crop_code)],
                    "ANO": year_int,
                    "TEMPORAL_ROLE": temporal_role(year_int),
                    "VARIABLE": var,
                    "SHARE_FIELD": f"{prefix}_SHARE",
                    "ANNUAL_DENOMINATOR": stats[var][0],
                    "DENOMINATOR_STATUS": stats[var][3],
                    "SOURCE_12_MONTHS_PRESENT": stats[var][4],
                    "MISSING_MONTH_COUNT": stats[var][1],
                    "POSITIVE_MONTH_COUNT": stats[var][2],
                    "NORMALIZED_ENTROPY": entropy,
                    "CIRCULAR_R": radius,
                    "CIRCULAR_MEAN_ANGLE_RAD": angle,
                    "CIRCULAR_MEAN_MONTH": mean_month,
                    "K50": k50["k"],
                    "K50_START_MONTH": k50["start_month"],
                    "K50_END_MONTH": k50["end_month"],
                    "K50_CAPTURED_SHARE": k50["captured_share"],
                    "K75": k75["k"],
                    "K75_START_MONTH": k75["start_month"],
                    "K75_END_MONTH": k75["end_month"],
                    "K75_CAPTURED_SHARE": k75["captured_share"],
                    "K90": k90["k"],
                    "K90_START_MONTH": k90["start_month"],
                    "K90_END_MONTH": k90["end_month"],
                    "K90_CAPTURED_SHARE": k90["captured_share"],
                    "DESCRIPTIVE_ONLY": True,
                    "SELECTION_STATUS": "NOT_SELECTED_STAGE_A",
                }
            )

    monthly = pd.DataFrame(rows)
    count_columns = [
        column
        for column in monthly.columns
        if column.endswith("_MISSING_MONTH_COUNT") or column.endswith("_POSITIVE_MONTH_COUNT")
    ]
    for column in count_columns:
        monthly[column] = monthly[column].astype("Int64")
    summary = pd.DataFrame(summaries)
    write_csv(monthly, dirs["processed"] / "temporal_structure_monthly.csv")
    write_csv(summary, dirs["processed"] / "temporal_structure_summary.csv")

    raw_month_min = int(raw["MES"].min())
    raw_month_max = int(raw["MES"].max())
    duplicate_keys = int(raw.duplicated(["UBIGEO", "MES", "COD_CULTIVO"]).sum())
    report = {
        "raw_rows": int(len(raw)),
        "target_crop_raw_rows": int(len(target)),
        "duplicate_source_keys": duplicate_keys,
        "observed_raw_month_min": raw_month_min,
        "observed_raw_month_max": raw_month_max,
        "authorized_columns_used": AUTHORIZED_COLUMNS,
        "blank_zero_semantics": {
            "numeric_missing_cells": {col: int(raw[col].isna().sum()) for col in ["SIEMBRA", "COSECHA", "PRODUCCION"]},
            "numeric_zero_cells": {col: int((raw[col] == 0).sum(skipna=True)) for col in ["SIEMBRA", "COSECHA", "PRODUCCION"]},
            "missing_filled_with_zero": False,
        },
        "temporal_roles": {
            "2016_2023": "MAIN_TEMPORAL_STRUCTURE",
            "2015_08_2015_12": "AUG_DEC_ANTECEDENT_SUPPORT_ONLY",
            "2024": "CONTEXTUAL_ONLY_NOT_FOR_SELECTION",
        },
        "status": "PASS"
        if len(raw) == 124514 and len(target) == 23540 and duplicate_keys == 0 and raw_month_min == 201508 and raw_month_max == 202412
        else "FAIL",
    }
    write_json(dirs["qa"] / "temporal_source_integrity_report.json", report)
    if report["status"] != "PASS":
        raise RuntimeError("TEMPORAL_SOURCE_INTEGRITY_FAIL")
    return monthly, summary, report


def lookup_series(raw: pd.DataFrame, crop_code: str, value_col: str) -> dict[tuple[str, int], float | None]:
    crop = raw[raw["COD_CULTIVO"] == crop_code]
    output: dict[tuple[str, int], float | None] = {}
    for _, row in crop.iterrows():
        key = (str(row["UBIGEO"]), int(row["MES"]))
        output[key] = None if pd.isna(row[value_col]) else float(row[value_col])
    return output


def transient_lag_compatibility(raw: pd.DataFrame, dirs: dict[str, Path]) -> pd.DataFrame:
    rows = []
    for crop_code in sorted(TRANSIENT_CROPS):
        crop = raw[(raw["COD_CULTIVO"] == crop_code) & (raw["ANO"].isin(MAIN_YEARS))].copy()
        sow_lookup = lookup_series(raw, crop_code, "SIEMBRA")
        for (ubigeo, year), group in crop.groupby(["UBIGEO", "ANO"], sort=True):
            harvest_values = []
            for month in range(1, 13):
                value_series = group.loc[group["MONTH"] == month, "COSECHA"]
                harvest_values.append(None if value_series.empty or pd.isna(value_series.iloc[0]) else float(value_series.iloc[0]))
            harvest_share, harvest_denom, harvest_missing, harvest_positive, harvest_status = normalize_vector(harvest_values)
            for lag in DIAGNOSTIC_LAGS:
                sow_values = []
                predecessor_dates = []
                predecessor_observed = 0
                for harvest_month in range(1, 13):
                    pred_year, pred_month, pred_mes = add_months(int(year), harvest_month, -lag)
                    predecessor_dates.append(pred_mes)
                    key = (str(ubigeo), pred_mes)
                    if key in sow_lookup:
                        predecessor_observed += 1
                    sow_values.append(sow_lookup.get(key))
                sow_share, sow_denom, sow_missing, sow_positive, sow_status = normalize_vector(sow_values)
                metrics_available = harvest_share is not None and sow_share is not None
                rows.append(
                    {
                        "UBIGEO": str(ubigeo),
                        "COD_CULTIVO": crop_code,
                        "CROP_STD": TARGET_CROPS[crop_code],
                        "OUTCOME_YEAR": int(year),
                        "DIAGNOSTIC_LAG_MONTHS": lag,
                        "HARVEST_DENOMINATOR": harvest_denom,
                        "HARVEST_SUPPORT_STATUS": harvest_status,
                        "HARVEST_MISSING_MONTHS": harvest_missing,
                        "HARVEST_POSITIVE_MONTHS": harvest_positive,
                        "SOWING_DENOMINATOR": sow_denom,
                        "SOWING_SUPPORT_STATUS": sow_status,
                        "SOWING_MISSING_MONTHS": sow_missing,
                        "SOWING_POSITIVE_MONTHS": sow_positive,
                        "PREDECESSOR_MONTHS_OBSERVED": predecessor_observed,
                        "PREDECESSOR_MONTHS_REQUIRED": 12,
                        "PREDECESSOR_SUPPORT_COMPLETE": predecessor_observed == 12,
                        "OVERLAP_COEFFICIENT": float(np.minimum(harvest_share, sow_share).sum()) if metrics_available else np.nan,
                        "JENSEN_SHANNON_DIVERGENCE": js_divergence(harvest_share, sow_share) if metrics_available else np.nan,
                        "DIAGNOSTIC_ONLY": True,
                        "SELECTION_STATUS": "NOT_SELECTED_STAGE_A",
                        "PREDECESSOR_MONTH_MIN": min(predecessor_dates),
                        "PREDECESSOR_MONTH_MAX": max(predecessor_dates),
                    }
                )
    result = pd.DataFrame(rows).sort_values(["COD_CULTIVO", "UBIGEO", "OUTCOME_YEAR", "DIAGNOSTIC_LAG_MONTHS"], kind="mergesort")
    write_csv(result, dirs["qa"] / "transient_lag_compatibility.csv")
    return result


def year_crossing_audit(raw: pd.DataFrame, dirs: dict[str, Path]) -> pd.DataFrame:
    rows = []
    for crop_code in sorted(TRANSIENT_CROPS):
        crop = raw[(raw["COD_CULTIVO"] == crop_code) & (raw["ANO"].isin(MAIN_YEARS))].copy()
        sow_lookup = lookup_series(raw, crop_code, "SIEMBRA")
        for (ubigeo, year), group in crop.groupby(["UBIGEO", "ANO"], sort=True):
            harvest_values = []
            for month in range(1, 13):
                value_series = group.loc[group["MONTH"] == month, "COSECHA"]
                harvest_values.append(None if value_series.empty or pd.isna(value_series.iloc[0]) else float(value_series.iloc[0]))
            harvest_share, harvest_denom, _, _, harvest_status = normalize_vector(harvest_values)
            for lag in DIAGNOSTIC_LAGS:
                predecessor_in_prior_year = []
                observed_prior_predecessors = 0
                required_prior_predecessors = 0
                prior_share = np.nan
                if harvest_share is not None:
                    prior_share_value = 0.0
                    for harvest_month in range(1, 13):
                        pred_year, _, pred_mes = add_months(int(year), harvest_month, -lag)
                        is_prior = pred_year == int(year) - 1
                        predecessor_in_prior_year.append(is_prior)
                        if is_prior:
                            required_prior_predecessors += 1
                            prior_share_value += float(harvest_share[harvest_month - 1])
                            if (str(ubigeo), pred_mes) in sow_lookup:
                                observed_prior_predecessors += 1
                    prior_share = prior_share_value
                rows.append(
                    {
                        "AUDIT_TYPE": "TRANSIENT_SUPPORT_COMPATIBILITY",
                        "UBIGEO": str(ubigeo),
                        "COD_CULTIVO": crop_code,
                        "CROP_STD": TARGET_CROPS[crop_code],
                        "ANO": int(year),
                        "TEMPORAL_ROLE": temporal_role(int(year)),
                        "DIAGNOSTIC_LAG_MONTHS": lag,
                        "HARVEST_DENOMINATOR": harvest_denom,
                        "HARVEST_SUPPORT_STATUS": harvest_status,
                        "PRIOR_YEAR_PREDECESSOR_HARVEST_SHARE": prior_share,
                        "PRIOR_YEAR_PREDECESSOR_MONTHS_REQUIRED": required_prior_predecessors,
                        "PRIOR_YEAR_PREDECESSOR_MONTHS_OBSERVED": observed_prior_predecessors,
                        "SUPPORT_STATUS": "OBSERVED" if required_prior_predecessors == observed_prior_predecessors else "PARTIAL_OR_UNOBSERVED",
                        "ATTRIBUTION_STATUS": "NOT_ATTRIBUTED_STAGE_A",
                        "DESCRIPTIVE_ONLY": True,
                    }
                )
    for crop_code in sorted(PERMANENT_CROPS):
        crop = raw[(raw["COD_CULTIVO"] == crop_code) & (raw["ANO"].isin(MAIN_YEARS))].copy()
        for (ubigeo, year), group in crop.groupby(["UBIGEO", "ANO"], sort=True):
            harvest_values = []
            production_values = []
            for month in range(1, 13):
                h = group.loc[group["MONTH"] == month, "COSECHA"]
                p = group.loc[group["MONTH"] == month, "PRODUCCION"]
                harvest_values.append(None if h.empty or pd.isna(h.iloc[0]) else float(h.iloc[0]))
                production_values.append(None if p.empty or pd.isna(p.iloc[0]) else float(p.iloc[0]))
            harvest_share, harvest_denom, _, _, harvest_status = normalize_vector(harvest_values)
            production_share, production_denom, _, _, production_status = normalize_vector(production_values)
            rows.append(
                {
                    "AUDIT_TYPE": "PERMANENT_EARLY_YEAR_ACTIVITY",
                    "UBIGEO": str(ubigeo),
                    "COD_CULTIVO": crop_code,
                    "CROP_STD": TARGET_CROPS[crop_code],
                    "ANO": int(year),
                    "TEMPORAL_ROLE": temporal_role(int(year)),
                    "DIAGNOSTIC_LAG_MONTHS": np.nan,
                    "HARVEST_DENOMINATOR": harvest_denom,
                    "HARVEST_SUPPORT_STATUS": harvest_status,
                    "JAN_MAR_HARVEST_SHARE": float(harvest_share[:3].sum()) if harvest_share is not None else np.nan,
                    "PRODUCTION_DENOMINATOR": production_denom,
                    "PRODUCTION_SUPPORT_STATUS": production_status,
                    "JAN_MAR_PRODUCTION_SHARE": float(production_share[:3].sum()) if production_share is not None else np.nan,
                    "ATTRIBUTION_STATUS": "NOT_IDENTIFIABLE_FROM_AGGREGATED_DATA",
                    "DESCRIPTIVE_ONLY": True,
                }
            )
    result = pd.DataFrame(rows).sort_values(["AUDIT_TYPE", "COD_CULTIVO", "UBIGEO", "ANO", "DIAGNOSTIC_LAG_MONTHS"], kind="mergesort")
    write_csv(result, dirs["qa"] / "year_crossing_audit.csv")
    return result


def left_truncation_2016_audit(raw: pd.DataFrame, dirs: dict[str, Path]) -> pd.DataFrame:
    rows = []
    source_start = 201508
    for crop_code in sorted(TRANSIENT_CROPS):
        crop = raw[(raw["COD_CULTIVO"] == crop_code) & (raw["ANO"] == 2016)].copy()
        for ubigeo, group in crop.groupby("UBIGEO", sort=True):
            harvest_values = []
            for month in range(1, 13):
                value_series = group.loc[group["MONTH"] == month, "COSECHA"]
                harvest_values.append(None if value_series.empty or pd.isna(value_series.iloc[0]) else float(value_series.iloc[0]))
            harvest_share, harvest_denom, _, _, harvest_status = normalize_vector(harvest_values)
            for lag in DIAGNOSTIC_LAGS:
                unsupported_share = np.nan
                unsupported_months = []
                if harvest_share is not None:
                    unsupported_share_value = 0.0
                    for harvest_month in range(1, 13):
                        _, _, pred_mes = add_months(2016, harvest_month, -lag)
                        if pred_mes < source_start:
                            unsupported_share_value += float(harvest_share[harvest_month - 1])
                            unsupported_months.append(pred_mes)
                    unsupported_share = unsupported_share_value
                rows.append(
                    {
                        "UBIGEO": str(ubigeo),
                        "COD_CULTIVO": crop_code,
                        "CROP_STD": TARGET_CROPS[crop_code],
                        "OUTCOME_YEAR": 2016,
                        "DIAGNOSTIC_LAG_MONTHS": lag,
                        "HARVEST_DENOMINATOR": harvest_denom,
                        "HARVEST_SUPPORT_STATUS": harvest_status,
                        "UNSUPPORTED_HARVEST_SHARE": unsupported_share,
                        "POTENTIAL_LEFT_TRUNCATION": bool(pd.notna(unsupported_share) and unsupported_share > 0),
                        "UNSUPPORTED_PREDECESSOR_MONTHS": ";".join(str(m) for m in unsupported_months),
                        "DECISION_STATUS": "PENDING_EVIDENCE_FREEZE",
                        "IMPUTATION_USED": False,
                    }
                )
    result = pd.DataFrame(rows).sort_values(["COD_CULTIVO", "UBIGEO", "DIAGNOSTIC_LAG_MONTHS"], kind="mergesort")
    write_csv(result, dirs["qa"] / "left_truncation_2016.csv")
    return result


def write_stage_schema(dirs: dict[str, Path]) -> dict[str, Any]:
    files = {
        "phenology_evidence_registry.csv": dirs["processed"] / "phenology_evidence_registry.csv",
        "temporal_structure_monthly.csv": dirs["processed"] / "temporal_structure_monthly.csv",
        "temporal_structure_summary.csv": dirs["processed"] / "temporal_structure_summary.csv",
        "transient_lag_compatibility.csv": dirs["qa"] / "transient_lag_compatibility.csv",
        "year_crossing_audit.csv": dirs["qa"] / "year_crossing_audit.csv",
        "left_truncation_2016.csv": dirs["qa"] / "left_truncation_2016.csv",
    }
    schema = {
        "stage": STAGE_A_VERSION,
        "outputs": {
            name: {
                "columns": pd.read_csv(path, nrows=0).columns.tolist(),
                "relative_path": str(path.relative_to(dirs["processed"].parent) if "processed" in path.parts else path.name),
            }
            for name, path in sorted(files.items())
        },
        "forbidden_stage_b_outputs": [
            "crop_exposure_architecture.csv",
            "phenology_windows_frozen.csv",
            "phenology_exposures_panel.parquet",
            "phenology_exposures_long.parquet",
        ],
    }
    write_json(dirs["qa"] / "stage_a_schema.json", schema)
    return schema


def core_hashes(root: Path) -> dict[str, str]:
    output = {}
    for rel in CORE_RELATIVE_OUTPUTS:
        path = root / rel
        output[rel] = sha256_file(path)
    return output


def run_core(output_root: Path | None = None) -> dict[str, Any]:
    dirs = stage_dirs(output_root)
    ensure_dirs(dirs)
    upstream = verify_upstream_integrity(dirs)
    registry, evidence = build_evidence_registry(dirs)
    raw = read_authorized_raw()
    monthly, summary, temporal_report = temporal_structure_audit(raw, dirs)
    lag = transient_lag_compatibility(raw, dirs)
    crossing = year_crossing_audit(raw, dirs)
    truncation = left_truncation_2016_audit(raw, dirs)
    schema = write_stage_schema(dirs)
    return {
        "upstream": upstream,
        "evidence": evidence,
        "temporal": temporal_report,
        "rows": {
            "evidence_registry": int(len(registry)),
            "temporal_monthly": int(len(monthly)),
            "temporal_summary": int(len(summary)),
            "transient_lag": int(len(lag)),
            "year_crossing": int(len(crossing)),
            "left_truncation": int(len(truncation)),
        },
        "schema": schema,
    }


def run_reproducibility(real_dirs: dict[str, Path]) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="phenology_stage_a_run1_") as run1_dir, tempfile.TemporaryDirectory(
        prefix="phenology_stage_a_run2_"
    ) as run2_dir:
        run1_root = Path(run1_dir)
        run2_root = Path(run2_dir)
        run_core(run1_root)
        run_core(run2_root)
        run1_hashes = core_hashes(run1_root)
        run2_hashes = core_hashes(run2_root)
    report = {
        "stage": STAGE_A_VERSION,
        "core_outputs": CORE_RELATIVE_OUTPUTS,
        "run1_hashes": run1_hashes,
        "run2_hashes": run2_hashes,
        "deterministic_core_outputs_identical": run1_hashes == run2_hashes,
        "status": "PASS" if run1_hashes == run2_hashes else "FAIL",
    }
    write_json(real_dirs["qa"] / "phenology_stage_a_reproducibility_report.json", report)
    if report["status"] != "PASS":
        raise RuntimeError("STAGE_A_REPRODUCIBILITY_FAIL")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Run PHENOLOGY MASTER v1 Stage A processing.")
    parser.add_argument("--skip-reproducibility", action="store_true")
    args = parser.parse_args()
    dirs = stage_dirs(None)
    result = run_core(None)
    if not args.skip_reproducibility:
        result["reproducibility"] = run_reproducibility(dirs)
    print(json.dumps({"stage": STAGE_A_VERSION, "status": "PROCESSING_COMPLETE", "rows": result["rows"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
