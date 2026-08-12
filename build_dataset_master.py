#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DATASET MASTER v1 — Piura agricultural panel
=============================================

Builds and audits a district × crop × year panel for Piura, Peru, from:
- GORE Piura monthly agricultural campaign CSV
- GORE Piura data dictionary (XLSX)
- GORE Piura metadata (DOCX; integrity only in this phase)
- MIDAGRI 2024 agricultural physical-area workbook
- Official ICEN monthly text file

Scientific scope of this script:
- Data integrity and QA
- Annual aggregation for 2016–2023
- YIELD_RAW = annual production / annual harvested area
- Production-weighted farm-gate price
- Balanced-panel construction for five target crops
- ICEN cleaning (not merged into the agricultural panel)
- Physical land-area join and coverage gates
- Missingness, dictionary inconsistencies, and outlier flags

Explicitly out of scope:
- Econometric estimation
- Climate raster processing
- Scenario generation
- Copulas/bootstrap
- Mean-CVaR optimization

Python: 3.10+
Dependencies: pandas, numpy, openpyxl
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

import numpy as np
import pandas as pd


# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

DATASET_VERSION = "DATASET_MASTER_v1"
MAIN_START_YEAR = 2016
MAIN_END_YEAR = 2023
EXPECTED_RAW_ROWS = 124_514
EXPECTED_TARGET_RAW_ROWS = 23_540
EXPECTED_MAIN_PANEL_N = 1_701
EXPECTED_BALANCED_N = 480
EXPECTED_BALANCED_DISTRICTS = 12
MIN_MAIN_PANEL_N = 300
MIN_BALANCED_PANEL_N = 300
MIN_LAND_MATCH_RATE = 0.99  # strict >99% target
MIN_CROP_YEARS = 3
OUTLIER_Z_THRESHOLD = 3.0

EXPECTED_HASHES = {
    "Formato_dataset_productos_dra__ (2).csv": (
        "7953e95f532b97f3db1ad42dfb517dc0b5f6e98a80b1f1b0954fc1b52419c489"
    ),
    "Formato_DiccionarioDatos_productos_dra_.xlsx": (
        "9df8aedf987a7a882d265ffc629d105f8058a5208738d5dcd1b213b30d347ce0"
    ),
    "Formato_Metadatos_productos_dra_.docx": (
        "a66ede624b8d2f502df65620c84233dd04a9ebcc29ae9969c38e2272ec812ea7"
    ),
    "superficie_agricola_nacional_2024.xlsx": None,
    "ICEN.txt": None,
}

AGRICULTURAL_FILE = "Formato_dataset_productos_dra__ (2).csv"
DICTIONARY_FILE = "Formato_DiccionarioDatos_productos_dra_.xlsx"
METADATA_FILE = "Formato_Metadatos_productos_dra_.docx"
LAND_FILE = "superficie_agricola_nacional_2024.xlsx"
ICEN_FILE = "ICEN.txt"

REQUIRED_AG_COLUMNS = [
    "FECHA_CORTE",
    "FECHA_MUESTRA",
    "DEPARTAMENTO",
    "PROVINCIA",
    "DISTRITO",
    "UBIGEO",
    "ANO",
    "MES",
    "COD_CULTIVO",
    "CULTIVO",
    "SIEMBRA",
    "COSECHA",
    "PRODUCCION",
    "VERDE_ACTUAL",
    "PRECIO_CHACRA",
]

NUMERIC_AG_COLUMNS = [
    "SIEMBRA",
    "COSECHA",
    "PRODUCCION",
    "VERDE_ACTUAL",
    "PRECIO_CHACRA",
]

# Target crops are selected by official source codes only — never fuzzy names.
TARGET_CROPS = {
    "14010020000": "ARROZ",
    "13010210000": "MANGO",
    "13010170102": "LIMON SUTIL",
    "15010040000": "PLATANOS Y BANANAS",
    "14010070000": "MAIZ AMARILLO DURO",
}


# -----------------------------------------------------------------------------
# Paths and logging helpers
# -----------------------------------------------------------------------------


def project_paths(root: Path) -> dict[str, Path]:
    paths = {
        "root": root,
        "raw": root / "data" / "raw",
        "processed": root / "data" / "processed",
        "qa": root / "outputs" / "qa",
        "figures": root / "outputs" / "figures",
    }
    for key in ("raw", "processed", "qa", "figures"):
        paths[key].mkdir(parents=True, exist_ok=True)
    return paths


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def print_step(message: str) -> None:
    print(f"\n[DATASET MASTER v1] {message}")


# -----------------------------------------------------------------------------
# Integrity and manifest
# -----------------------------------------------------------------------------


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_files_and_hashes(paths: dict[str, Path]) -> pd.DataFrame:
    """Verify mandatory raw files and hard-stop on expected-hash mismatch."""
    rows: list[dict[str, object]] = []
    processed_at = utc_now_iso()

    for filename, expected_hash in EXPECTED_HASHES.items():
        path = paths["raw"] / filename
        if not path.exists():
            raise FileNotFoundError(
                f"Archivo obligatorio ausente: {path}. "
                "Coloque los cinco archivos raw en data/raw/."
            )

        actual_hash = sha256_file(path)
        if expected_hash is not None and actual_hash.lower() != expected_hash.lower():
            raise RuntimeError(
                "Integridad del archivo comprometida: "
                f"{filename}. SHA-256 esperado={expected_hash}; actual={actual_hash}"
            )

        stat = path.stat()
        rows.append(
            {
                "dataset_version": DATASET_VERSION,
                "filename": filename,
                "path": str(path.relative_to(paths["root"])),
                "size_bytes": stat.st_size,
                "sha256_actual": actual_hash,
                "sha256_expected": expected_hash or "NOT_PROVIDED",
                "hash_status": (
                    "PASS" if expected_hash is not None else "RECORDED_NO_EXPECTED_HASH"
                ),
                "source_mtime_utc": datetime.fromtimestamp(
                    stat.st_mtime, timezone.utc
                ).replace(microsecond=0).isoformat(),
                "processed_at_utc": processed_at,
            }
        )

    manifest = pd.DataFrame(rows)
    manifest.to_csv(paths["qa"] / "data_manifest.csv", index=False, encoding="utf-8")
    return manifest


# -----------------------------------------------------------------------------
# Generic normalization helpers
# -----------------------------------------------------------------------------


def normalize_identifier(series: pd.Series, width: Optional[int] = None) -> pd.Series:
    out = (
        series.astype("string")
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
    )
    if width is not None:
        out = out.str.zfill(width)
    return out


def sum_preserve_all_missing(series: pd.Series) -> float:
    """Sum observed values; all-NaN remains NaN; genuine zeros remain zero."""
    return series.sum(min_count=1)


def last_non_null_by_order(group: pd.DataFrame, value_col: str) -> float:
    non_null = group.loc[group[value_col].notna(), value_col]
    if non_null.empty:
        return np.nan
    return float(non_null.iloc[-1])


# -----------------------------------------------------------------------------
# Agricultural raw data
# -----------------------------------------------------------------------------


def load_agricultural_csv(paths: dict[str, Path]) -> tuple[pd.DataFrame, dict[str, object]]:
    path = paths["raw"] / AGRICULTURAL_FILE

    dtype_map = {
        "FECHA_CORTE": "string",
        "FECHA_MUESTRA": "string",
        "DEPARTAMENTO": "string",
        "PROVINCIA": "string",
        "DISTRITO": "string",
        "UBIGEO": "string",
        "MES": "string",
        "COD_CULTIVO": "string",
        "CULTIVO": "string",
    }

    df = pd.read_csv(
        path,
        encoding="utf-8",
        sep=",",
        dtype=dtype_map,
        low_memory=False,
        keep_default_na=True,
    )

    missing_cols = sorted(set(REQUIRED_AG_COLUMNS) - set(df.columns))
    if missing_cols:
        raise ValueError(f"Faltan columnas obligatorias en CSV agrícola: {missing_cols}")

    # Restrict to expected columns in source order; unexpected columns remain auditable separately.
    extra_cols = [c for c in df.columns if c not in REQUIRED_AG_COLUMNS]

    df["UBIGEO"] = normalize_identifier(df["UBIGEO"], width=6)
    df["COD_CULTIVO"] = normalize_identifier(df["COD_CULTIVO"], width=None)
    df["MES"] = normalize_identifier(df["MES"], width=6)

    df["ANO"] = pd.to_numeric(df["ANO"], errors="coerce").astype("Int64")
    for col in NUMERIC_AG_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Parse AAAAMM. Invalid values are a hard structural error.
    df["DATE_MONTH"] = pd.to_datetime(df["MES"], format="%Y%m", errors="coerce")
    invalid_month = df["DATE_MONTH"].isna()
    if invalid_month.any():
        invalid = df.loc[invalid_month, ["UBIGEO", "COD_CULTIVO", "ANO", "MES"]]
        invalid.to_csv(paths["qa"] / "invalid_month_values.csv", index=False)
        raise ValueError(
            f"Se detectaron {int(invalid_month.sum())} valores MES inválidos. "
            "Revise outputs/qa/invalid_month_values.csv"
        )

    # ANO mismatch is documented as warning, not silently corrected.
    ano_mismatch = df["ANO"].notna() & (df["ANO"].astype("Int64") != df["DATE_MONTH"].dt.year)
    mismatch_df = df.loc[
        ano_mismatch,
        ["UBIGEO", "COD_CULTIVO", "CULTIVO", "ANO", "MES", "DATE_MONTH"],
    ].copy()
    mismatch_df.to_csv(paths["qa"] / "ano_mes_mismatch.csv", index=False)

    # Duplicate monthly key is reported. For this scientific dataset, duplicates would make
    # annual aggregation ambiguous, so it is a hard stop.
    key = ["UBIGEO", "COD_CULTIVO", "MES"]
    dup_mask = df.duplicated(key, keep=False)
    if dup_mask.any():
        df.loc[dup_mask].sort_values(key).to_csv(
            paths["qa"] / "duplicate_monthly_keys.csv", index=False
        )
        raise ValueError(
            f"Se detectaron {int(dup_mask.sum())} filas con clave mensual duplicada "
            f"{key}. Revise outputs/qa/duplicate_monthly_keys.csv"
        )

    # Negative numeric values are impossible/suspicious. They are not silently fixed.
    negative_records: list[pd.DataFrame] = []
    for col in NUMERIC_AG_COLUMNS:
        mask = df[col].notna() & (df[col] < 0)
        if mask.any():
            tmp = df.loc[
                mask,
                ["UBIGEO", "COD_CULTIVO", "CULTIVO", "ANO", "MES", col],
            ].copy()
            tmp["VARIABLE"] = col
            tmp = tmp.rename(columns={col: "VALUE"})
            negative_records.append(tmp)
    negatives = (
        pd.concat(negative_records, ignore_index=True)
        if negative_records
        else pd.DataFrame(
            columns=["UBIGEO", "COD_CULTIVO", "CULTIVO", "ANO", "MES", "VALUE", "VARIABLE"]
        )
    )
    negatives.to_csv(paths["qa"] / "negative_values.csv", index=False)

    audit = {
        "raw_rows": int(len(df)),
        "raw_columns": int(df.shape[1]),
        "unique_crops": int(df["COD_CULTIVO"].nunique(dropna=True)),
        "unique_districts": int(df["UBIGEO"].nunique(dropna=True)),
        "first_month": df["DATE_MONTH"].min().strftime("%Y-%m"),
        "last_month": df["DATE_MONTH"].max().strftime("%Y-%m"),
        "unique_months": int(df["DATE_MONTH"].nunique()),
        "ano_mes_mismatches": int(ano_mismatch.sum()),
        "negative_value_rows": int(len(negatives)),
        "extra_columns": extra_cols,
        "benchmark_raw_rows_expected": EXPECTED_RAW_ROWS,
        "benchmark_raw_rows_match": bool(len(df) == EXPECTED_RAW_ROWS),
    }

    with (paths["qa"] / "raw_agricultural_audit.json").open("w", encoding="utf-8") as f:
        json.dump(audit, f, ensure_ascii=False, indent=2)

    return df, audit


# -----------------------------------------------------------------------------
# Source dictionary QA
# -----------------------------------------------------------------------------


def load_dictionary(paths: dict[str, Path]) -> pd.DataFrame:
    path = paths["raw"] / DICTIONARY_FILE
    xls = pd.ExcelFile(path, engine="openpyxl")
    if "DiccionarioDatos" not in xls.sheet_names:
        raise ValueError(
            f"No existe la hoja 'DiccionarioDatos' en {DICTIONARY_FILE}. "
            f"Hojas encontradas: {xls.sheet_names}"
        )
    dictionary = pd.read_excel(
        path,
        sheet_name="DiccionarioDatos",
        header=3,
        engine="openpyxl",
    )
    dictionary.columns = [str(c).strip() for c in dictionary.columns]
    dictionary["Variable"] = dictionary["Variable"].astype("string").str.strip()
    return dictionary


def build_dictionary_inconsistencies(
    dictionary: pd.DataFrame,
    agricultural: pd.DataFrame,
    paths: dict[str, Path],
) -> pd.DataFrame:
    """Document known/document-detected dictionary issues; do not 'correct' source files."""
    lookup = dictionary.set_index("Variable", drop=False)
    issues: list[dict[str, object]] = []

    def dictionary_value(variable: str, col: str) -> object:
        if variable not in lookup.index or col not in lookup.columns:
            return np.nan
        value = lookup.loc[variable, col]
        if isinstance(value, pd.Series):
            value = value.iloc[0]
        return value

    # COD_CULTIVO: official dictionary says Numeric / size 8; observed source codes are 11-char identifiers.
    observed_lengths = agricultural["COD_CULTIVO"].dropna().str.len()
    observed_max_len = int(observed_lengths.max()) if not observed_lengths.empty else None
    declared_size = dictionary_value("COD_CULTIVO", "Tamaño")
    declared_type = dictionary_value("COD_CULTIVO", "Tipo de dato")
    if observed_max_len is not None and (
        str(declared_type).strip().lower().startswith("num")
        or (pd.notna(declared_size) and int(float(declared_size)) != observed_max_len)
    ):
        issues.append(
            {
                "VARIABLE": "COD_CULTIVO",
                "DICTIONARY_TYPE": declared_type,
                "DICTIONARY_SIZE": declared_size,
                "OBSERVED_PROPERTY": f"identifier stored as text; max length={observed_max_len}",
                "ISSUE": "Dictionary type/length is inconsistent with the observed identifier structure.",
                "SEVERITY": "HIGH",
                "PIPELINE_ACTION": "Preserve COD_CULTIVO as string; never coerce to integer.",
            }
        )

    # CULTIVO: dictionary says Numeric but actual values are textual crop names.
    declared_type = dictionary_value("CULTIVO", "Tipo de dato")
    non_numeric_names = pd.to_numeric(agricultural["CULTIVO"], errors="coerce").isna() & agricultural[
        "CULTIVO"
    ].notna()
    if str(declared_type).strip().lower().startswith("num") and non_numeric_names.any():
        issues.append(
            {
                "VARIABLE": "CULTIVO",
                "DICTIONARY_TYPE": declared_type,
                "DICTIONARY_SIZE": dictionary_value("CULTIVO", "Tamaño"),
                "OBSERVED_PROPERTY": "textual crop names observed",
                "ISSUE": "Dictionary declares CULTIVO as numeric although the source field contains text.",
                "SEVERITY": "HIGH",
                "PIPELINE_ACTION": "Preserve CULTIVO as string.",
            }
        )

    # Production unit: definition describes volume but does not explicitly state kg/tonnes.
    prod_desc = str(dictionary_value("PRODUCCION", "Descripción"))
    if not any(token in prod_desc.lower() for token in ["tonel", "kg", "kilogram", "t/", "tm"]):
        issues.append(
            {
                "VARIABLE": "PRODUCCION",
                "DICTIONARY_TYPE": dictionary_value("PRODUCCION", "Tipo de dato"),
                "DICTIONARY_SIZE": dictionary_value("PRODUCCION", "Tamaño"),
                "OBSERVED_PROPERTY": "numeric production volume",
                "ISSUE": "Official dictionary does not explicitly state the physical unit of PRODUCCION.",
                "SEVERITY": "MEDIUM",
                "PIPELINE_ACTION": "Compute YIELD_RAW ratio but keep its unit as UNRESOLVED; do not compute unit-dependent GVP conversion.",
            }
        )

    inconsistencies = pd.DataFrame(
        issues,
        columns=[
            "VARIABLE",
            "DICTIONARY_TYPE",
            "DICTIONARY_SIZE",
            "OBSERVED_PROPERTY",
            "ISSUE",
            "SEVERITY",
            "PIPELINE_ACTION",
        ],
    )
    inconsistencies.to_csv(
        paths["qa"] / "source_dictionary_inconsistencies.csv",
        index=False,
        encoding="utf-8",
    )
    return inconsistencies


# -----------------------------------------------------------------------------
# MIDAGRI physical land
# -----------------------------------------------------------------------------


def load_land_physical(paths: dict[str, Path]) -> pd.DataFrame:
    path = paths["raw"] / LAND_FILE
    xls = pd.ExcelFile(path, engine="openpyxl")
    sheet = "Tabla_Superficie_Agricola"
    if sheet not in xls.sheet_names:
        raise ValueError(
            f"No existe la hoja '{sheet}' en {LAND_FILE}. Hojas: {xls.sheet_names}"
        )

    land = pd.read_excel(path, sheet_name=sheet, engine="openpyxl")
    required = {"UBIGEO", "AREA_HA"}
    missing = required - set(land.columns)
    if missing:
        raise ValueError(f"Faltan columnas MIDAGRI obligatorias: {sorted(missing)}")

    if "DEPARTAMENTO" in land.columns:
        dep = land["DEPARTAMENTO"].astype("string").str.strip().str.upper()
        land = land.loc[dep.eq("PIURA")].copy()

    land["UBIGEO"] = normalize_identifier(land["UBIGEO"], width=6)
    land["AREA_HA"] = pd.to_numeric(land["AREA_HA"], errors="coerce")

    invalid_area = land["AREA_HA"].isna() | (land["AREA_HA"] <= 0)
    if invalid_area.any():
        land.loc[invalid_area].to_csv(paths["qa"] / "invalid_land_area.csv", index=False)
        raise ValueError(
            "Se detectaron AREA_HA nulas/no positivas en el archivo MIDAGRI para Piura. "
            "Revise outputs/qa/invalid_land_area.csv"
        )

    dup = land["UBIGEO"].duplicated(keep=False)
    if dup.any():
        land.loc[dup].sort_values("UBIGEO").to_csv(
            paths["qa"] / "duplicate_land_ubigeo.csv", index=False
        )
        raise ValueError(
            "El archivo de superficie agrícola contiene UBIGEO duplicados. "
            "No se agregan automáticamente; revise outputs/qa/duplicate_land_ubigeo.csv"
        )

    keep_cols = [c for c in ["UBIGEO", "DISTRITO", "AREA_HA", "FUENTE"] if c in land.columns]
    land_out = land[keep_cols].copy().sort_values("UBIGEO")
    land_out.to_csv(paths["processed"] / "land_physical.csv", index=False, encoding="utf-8")
    return land_out


# -----------------------------------------------------------------------------
# ICEN
# -----------------------------------------------------------------------------


def load_and_clean_icen(paths: dict[str, Path]) -> tuple[pd.DataFrame, dict[str, object]]:
    path = paths["raw"] / ICEN_FILE
    icen = pd.read_csv(
        path,
        comment="%",
        sep=r"\s+",
        header=None,
        names=["year", "month", "ICEN"],
        encoding="utf-8",
    )

    icen["year"] = pd.to_numeric(icen["year"], errors="coerce").astype("Int64")
    icen["month"] = pd.to_numeric(icen["month"], errors="coerce").astype("Int64")
    icen["ICEN"] = pd.to_numeric(icen["ICEN"], errors="coerce")

    invalid = (
        icen["year"].isna()
        | icen["month"].isna()
        | ~icen["month"].between(1, 12)
        | icen["ICEN"].isna()
    )
    if invalid.any():
        icen.loc[invalid].to_csv(paths["qa"] / "invalid_icen_rows.csv", index=False)
        raise ValueError(
            f"ICEN contiene {int(invalid.sum())} filas inválidas. "
            "Revise outputs/qa/invalid_icen_rows.csv"
        )

    icen["DATE"] = pd.to_datetime(
        dict(year=icen["year"].astype(int), month=icen["month"].astype(int), day=1)
    )
    if icen["DATE"].duplicated().any():
        icen.loc[icen["DATE"].duplicated(keep=False)].to_csv(
            paths["qa"] / "duplicate_icen_months.csv", index=False
        )
        raise ValueError("ICEN contiene meses duplicados.")

    icen = icen.sort_values("DATE").reset_index(drop=True)

    required_start = pd.Timestamp(f"{MAIN_START_YEAR}-01-01")
    required_end = pd.Timestamp(f"{MAIN_END_YEAR}-12-01")
    covers_main = icen["DATE"].min() <= required_start and icen["DATE"].max() >= required_end

    # Verify every month within 2016–2023 exists.
    expected_dates = pd.date_range(required_start, required_end, freq="MS")
    available = set(icen.loc[icen["DATE"].between(required_start, required_end), "DATE"])
    missing_main_months = [d for d in expected_dates if d not in available]
    if missing_main_months:
        pd.DataFrame({"MISSING_DATE": missing_main_months}).to_csv(
            paths["qa"] / "missing_icen_main_period.csv", index=False
        )
        covers_main = False

    icen_out = icen[["year", "month", "DATE", "ICEN"]].copy()
    icen_out["DATE"] = icen_out["DATE"].dt.strftime("%Y-%m-%d")
    icen_out.to_csv(paths["processed"] / "icen_clean.csv", index=False, encoding="utf-8")

    audit = {
        "first_date": icen["DATE"].min().strftime("%Y-%m"),
        "last_date": icen["DATE"].max().strftime("%Y-%m"),
        "rows": int(len(icen)),
        "covers_2016_2023": bool(covers_main),
        "missing_months_2016_2023": len(missing_main_months),
    }
    with (paths["qa"] / "icen_audit.json").open("w", encoding="utf-8") as f:
        json.dump(audit, f, ensure_ascii=False, indent=2)

    return icen, audit


# -----------------------------------------------------------------------------
# Annual agricultural panel
# -----------------------------------------------------------------------------


def build_annual_candidate(
    agricultural: pd.DataFrame,
    paths: dict[str, Path],
) -> tuple[pd.DataFrame, int]:
    target_codes = set(TARGET_CROPS)
    target_raw = agricultural.loc[agricultural["COD_CULTIVO"].isin(target_codes)].copy()
    target_raw_rows = int(len(target_raw))

    # Main yield period only.
    main = target_raw.loc[target_raw["ANO"].between(MAIN_START_YEAR, MAIN_END_YEAR)].copy()
    main = main.sort_values(["UBIGEO", "COD_CULTIVO", "ANO", "DATE_MONTH"])

    # Annual sums preserving all-missing as NaN.
    grouped = main.groupby(["UBIGEO", "COD_CULTIVO", "ANO"], sort=True, dropna=False)

    annual_sums = grouped.agg(
        PRODUCCION=("PRODUCCION", sum_preserve_all_missing),
        COSECHA=("COSECHA", sum_preserve_all_missing),
        SIEMBRA=("SIEMBRA", sum_preserve_all_missing),
        MONTHS_PRESENT=("DATE_MONTH", "nunique"),
        CULTIVO_SOURCE=("CULTIVO", lambda s: s.dropna().iloc[0] if not s.dropna().empty else pd.NA),
    ).reset_index()

    # Final observed stock VERDE_ACTUAL: last non-null monthly value in the year.
    verde = (
        main.groupby(["UBIGEO", "COD_CULTIVO", "ANO"], sort=True, group_keys=False)
        .apply(lambda g: last_non_null_by_order(g.sort_values("DATE_MONTH"), "VERDE_ACTUAL"), include_groups=False)
        .rename("VERDE_ACTUAL")
        .reset_index()
    )

    # Production-weighted farm-gate price. Price 0 means no activity under the metadata;
    # only months with positive production and positive observed price contribute.
    price_valid = main.loc[
        main["PRODUCCION"].notna()
        & (main["PRODUCCION"] > 0)
        & main["PRECIO_CHACRA"].notna()
        & (main["PRECIO_CHACRA"] > 0)
    ].copy()
    price_valid["PQ"] = price_valid["PRODUCCION"] * price_valid["PRECIO_CHACRA"]
    price = (
        price_valid.groupby(["UBIGEO", "COD_CULTIVO", "ANO"], sort=True)
        .agg(PRICE_Q_SUM=("PRODUCCION", "sum"), PRICE_PQ_SUM=("PQ", "sum"))
        .reset_index()
    )
    price["PRECIO"] = np.where(
        price["PRICE_Q_SUM"] > 0,
        price["PRICE_PQ_SUM"] / price["PRICE_Q_SUM"],
        np.nan,
    )
    price = price[["UBIGEO", "COD_CULTIVO", "ANO", "PRECIO"]]

    annual = annual_sums.merge(
        verde,
        on=["UBIGEO", "COD_CULTIVO", "ANO"],
        how="left",
        validate="one_to_one",
    ).merge(
        price,
        on=["UBIGEO", "COD_CULTIVO", "ANO"],
        how="left",
        validate="one_to_one",
    )

    annual["CROP_STD"] = annual["COD_CULTIVO"].map(TARGET_CROPS).astype("string")
    annual["YIELD_RAW"] = np.where(
        (annual["PRODUCCION"] > 0) & (annual["COSECHA"] > 0),
        annual["PRODUCCION"] / annual["COSECHA"],
        np.nan,
    )
    annual["YIELD_UNIT"] = "UNRESOLVED"

    # Missingness before final inclusion is more informative than missingness after complete-case filters.
    missingness_rows = []
    vars_for_missing = [
        "PRODUCCION",
        "COSECHA",
        "SIEMBRA",
        "PRECIO",
        "VERDE_ACTUAL",
        "YIELD_RAW",
    ]
    for year, g in annual.groupby("ANO"):
        for var in vars_for_missing:
            missingness_rows.append(
                {
                    "ANO": int(year),
                    "VARIABLE": var,
                    "N": int(len(g)),
                    "N_MISSING": int(g[var].isna().sum()),
                    "PCT_MISSING": float(g[var].isna().mean() * 100.0),
                }
            )
    pd.DataFrame(missingness_rows).to_csv(
        paths["qa"] / "missingness_by_year.csv", index=False, encoding="utf-8"
    )

    return annual, target_raw_rows


def build_panel_master(
    annual: pd.DataFrame,
    land: pd.DataFrame,
    paths: dict[str, Path],
) -> tuple[pd.DataFrame, dict[str, object], pd.DataFrame]:
    # Land join before filtering to quantify coverage.
    land_min = land[["UBIGEO", "AREA_HA"]].copy()
    candidate = annual.merge(
        land_min,
        on="UBIGEO",
        how="left",
        validate="many_to_one",
        indicator=True,
    )

    unique_candidate_districts = set(candidate["UBIGEO"].dropna())
    matched_candidate_districts = set(candidate.loc[candidate["_merge"].eq("both"), "UBIGEO"].dropna())
    district_match_rate = (
        len(matched_candidate_districts) / len(unique_candidate_districts)
        if unique_candidate_districts
        else 0.0
    )

    all_land_area = float(land["AREA_HA"].sum())
    matched_land_area = float(
        land.loc[land["UBIGEO"].isin(matched_candidate_districts), "AREA_HA"].sum()
    )
    physical_area_coverage_rate = matched_land_area / all_land_area if all_land_area > 0 else 0.0

    # Main scientific inclusion criteria.
    eligible = candidate.loc[
        candidate["PRODUCCION"].notna()
        & (candidate["PRODUCCION"] > 0)
        & candidate["COSECHA"].notna()
        & (candidate["COSECHA"] > 0)
        & candidate["PRECIO"].notna()
        & (candidate["PRECIO"] > 0)
        & candidate["AREA_HA"].notna()
        & candidate["_merge"].eq("both")
    ].copy()

    # Crop-level minimum temporal support (not district-crop support) to preserve the audited N≈1701.
    crop_year_counts = (
        eligible.groupby("COD_CULTIVO")["ANO"]
        .nunique()
        .rename("N_YEARS")
        .reset_index()
    )
    valid_crop_codes = set(
        crop_year_counts.loc[crop_year_counts["N_YEARS"] >= MIN_CROP_YEARS, "COD_CULTIVO"]
    )
    panel = eligible.loc[eligible["COD_CULTIVO"].isin(valid_crop_codes)].copy()

    # Remove merge indicator only after QA metrics are derived.
    panel = panel.drop(columns=["_merge"])

    # Unique key is mandatory.
    key = ["UBIGEO", "COD_CULTIVO", "ANO"]
    if panel.duplicated(key).any():
        panel.loc[panel.duplicated(key, keep=False)].to_csv(
            paths["qa"] / "duplicate_annual_keys.csv", index=False
        )
        raise ValueError(f"panel_master no es único por {key}")

    # Rename annual-area fields to explicit names in final panel.
    panel = panel.rename(
        columns={
            "COSECHA": "HARVEST_AREA",
            "SIEMBRA": "SOWN_AREA",
        }
    )

    final_cols = [
        "UBIGEO",
        "COD_CULTIVO",
        "CROP_STD",
        "CULTIVO_SOURCE",
        "ANO",
        "PRODUCCION",
        "HARVEST_AREA",
        "SOWN_AREA",
        "PRECIO",
        "VERDE_ACTUAL",
        "YIELD_RAW",
        "YIELD_UNIT",
        "AREA_HA",
        "MONTHS_PRESENT",
    ]
    panel = panel[final_cols].sort_values(key).reset_index(drop=True)

    panel.to_csv(paths["processed"] / "panel_master.csv", index=False, encoding="utf-8")
    crop_year_counts.to_csv(paths["qa"] / "crop_year_counts.csv", index=False)

    coverage = {
        "unique_candidate_districts": len(unique_candidate_districts),
        "matched_candidate_districts": len(matched_candidate_districts),
        "district_match_rate": district_match_rate,
        "piura_total_physical_area_ha": all_land_area,
        "matched_physical_area_ha": matched_land_area,
        "physical_area_coverage_rate": physical_area_coverage_rate,
    }

    return panel, coverage, crop_year_counts


# -----------------------------------------------------------------------------
# Balanced panel
# -----------------------------------------------------------------------------


def build_balanced_panel(panel: pd.DataFrame, paths: dict[str, Path]) -> tuple[pd.DataFrame, list[str]]:
    expected_years = set(range(MAIN_START_YEAR, MAIN_END_YEAR + 1))
    target_codes = list(TARGET_CROPS.keys())

    complete_districts: list[str] = []
    for ubigeo, g in panel.groupby("UBIGEO"):
        ok = True
        for code in target_codes:
            years = set(g.loc[g["COD_CULTIVO"].eq(code), "ANO"].astype(int).tolist())
            if years != expected_years:
                ok = False
                break
        if ok:
            complete_districts.append(str(ubigeo))

    balanced = panel.loc[panel["UBIGEO"].isin(complete_districts)].copy()
    balanced = balanced.sort_values(["UBIGEO", "COD_CULTIVO", "ANO"]).reset_index(drop=True)

    expected_rows = len(complete_districts) * len(target_codes) * len(expected_years)
    if len(balanced) != expected_rows:
        raise ValueError(
            "El panel balanceado no tiene el número de filas esperado por su estructura: "
            f"actual={len(balanced)}, estructural={expected_rows}"
        )

    balanced.to_csv(paths["processed"] / "panel_balanceado.csv", index=False, encoding="utf-8")
    pd.DataFrame({"UBIGEO": complete_districts}).to_csv(
        paths["qa"] / "balanced_districts.csv", index=False
    )
    return balanced, complete_districts


# -----------------------------------------------------------------------------
# Coverage and outlier QA
# -----------------------------------------------------------------------------


def build_crop_coverage(panel: pd.DataFrame, paths: dict[str, Path]) -> pd.DataFrame:
    rows = []
    for code, name in TARGET_CROPS.items():
        g = panel.loc[panel["COD_CULTIVO"].eq(code)]
        rows.append(
            {
                "COD_CULTIVO": code,
                "CROP_STD": name,
                "N_OBS": int(len(g)),
                "N_DISTRICTS": int(g["UBIGEO"].nunique()),
                "N_YEARS": int(g["ANO"].nunique()),
                "FIRST_YEAR": int(g["ANO"].min()) if not g.empty else np.nan,
                "LAST_YEAR": int(g["ANO"].max()) if not g.empty else np.nan,
            }
        )
    coverage = pd.DataFrame(rows)
    coverage.to_csv(paths["qa"] / "coverage_by_crop.csv", index=False, encoding="utf-8")
    return coverage


def flag_outliers(panel: pd.DataFrame, paths: dict[str, Path]) -> pd.DataFrame:
    """Flag |z| > 3 within crop; never delete rows."""
    variables = [
        "YIELD_RAW",
        "PRODUCCION",
        "HARVEST_AREA",
        "SOWN_AREA",
        "PRECIO",
        "VERDE_ACTUAL",
    ]
    flags: list[dict[str, object]] = []

    for code, crop_group in panel.groupby("COD_CULTIVO"):
        crop_name = TARGET_CROPS.get(str(code), str(code))
        for variable in variables:
            values = pd.to_numeric(crop_group[variable], errors="coerce")
            valid = values.dropna()
            if len(valid) < 3:
                continue
            mean = float(valid.mean())
            std = float(valid.std(ddof=1))
            if not math.isfinite(std) or std <= 0:
                continue
            z = (values - mean) / std
            mask = z.abs() > OUTLIER_Z_THRESHOLD
            if mask.any():
                for idx in crop_group.index[mask.fillna(False)]:
                    flags.append(
                        {
                            "UBIGEO": panel.at[idx, "UBIGEO"],
                            "COD_CULTIVO": panel.at[idx, "COD_CULTIVO"],
                            "CROP_STD": crop_name,
                            "ANO": int(panel.at[idx, "ANO"]),
                            "VARIABLE": variable,
                            "VALUE": panel.at[idx, variable],
                            "Z_SCORE": float(z.loc[idx]),
                            "THRESHOLD_ABS_Z": OUTLIER_Z_THRESHOLD,
                            "ACTION": "RETAIN_FOR_REVIEW",
                        }
                    )

    outliers = pd.DataFrame(
        flags,
        columns=[
            "UBIGEO",
            "COD_CULTIVO",
            "CROP_STD",
            "ANO",
            "VARIABLE",
            "VALUE",
            "Z_SCORE",
            "THRESHOLD_ABS_Z",
            "ACTION",
        ],
    )
    outliers.to_csv(paths["qa"] / "outliers_flag.csv", index=False, encoding="utf-8")
    return outliers


# -----------------------------------------------------------------------------
# Reports and gates
# -----------------------------------------------------------------------------


def pass_fail(condition: bool) -> str:
    return "PASA" if condition else "FALLA"


def write_coverage_report(
    paths: dict[str, Path],
    manifest: pd.DataFrame,
    raw_audit: dict[str, object],
    target_raw_rows: int,
    panel: pd.DataFrame,
    balanced: pd.DataFrame,
    complete_districts: list[str],
    land_coverage: dict[str, object],
    crop_coverage: pd.DataFrame,
    icen_audit: dict[str, object],
    dictionary_issues: pd.DataFrame,
) -> dict[str, object]:
    main_n = int(len(panel))
    balanced_n = int(len(balanced))

    gate_main_n = main_n > MIN_MAIN_PANEL_N
    gate_balanced_n = balanced_n > MIN_BALANCED_PANEL_N
    gate_land_district = float(land_coverage["district_match_rate"]) > MIN_LAND_MATCH_RATE
    gate_land_area = float(land_coverage["physical_area_coverage_rate"]) > MIN_LAND_MATCH_RATE
    gate_icen = bool(icen_audit["covers_2016_2023"])
    gate_target_crops = set(panel["COD_CULTIVO"].unique()) == set(TARGET_CROPS)
    gate_hashes = bool((manifest["hash_status"].isin(["PASS", "RECORDED_NO_EXPECTED_HASH"])).all())

    overall = all(
        [
            gate_hashes,
            gate_main_n,
            gate_balanced_n,
            gate_land_district,
            gate_land_area,
            gate_icen,
            gate_target_crops,
        ]
    )

    gates = {
        "dataset_version": DATASET_VERSION,
        "generated_at_utc": utc_now_iso(),
        "raw_rows": int(raw_audit["raw_rows"]),
        "target_crop_raw_rows": target_raw_rows,
        "main_panel_n": main_n,
        "main_panel_n_gt_300": gate_main_n,
        "balanced_districts": len(complete_districts),
        "balanced_panel_n": balanced_n,
        "balanced_panel_n_gt_300": gate_balanced_n,
        "district_land_match_rate": float(land_coverage["district_match_rate"]),
        "physical_area_coverage_rate": float(land_coverage["physical_area_coverage_rate"]),
        "district_land_match_gt_99pct": gate_land_district,
        "physical_area_coverage_gt_99pct": gate_land_area,
        "icen_covers_2016_2023": gate_icen,
        "all_five_target_crops_present": gate_target_crops,
        "expected_hashes_pass": gate_hashes,
        "dictionary_issue_count": int(len(dictionary_issues)),
        "yield_unit": "UNRESOLVED",
        "overall_gate": "PASA" if overall else "FALLA",
        "benchmark_main_panel_n": EXPECTED_MAIN_PANEL_N,
        "benchmark_main_panel_match": main_n == EXPECTED_MAIN_PANEL_N,
        "benchmark_balanced_n": EXPECTED_BALANCED_N,
        "benchmark_balanced_match": balanced_n == EXPECTED_BALANCED_N,
        "benchmark_balanced_districts": EXPECTED_BALANCED_DISTRICTS,
        "benchmark_balanced_districts_match": len(complete_districts) == EXPECTED_BALANCED_DISTRICTS,
        "benchmark_target_raw_rows": EXPECTED_TARGET_RAW_ROWS,
        "benchmark_target_raw_rows_match": target_raw_rows == EXPECTED_TARGET_RAW_ROWS,
    }

    with (paths["qa"] / "gate_report.json").open("w", encoding="utf-8") as f:
        json.dump(gates, f, ensure_ascii=False, indent=2)

    lines: list[str] = []
    lines.append("DATASET MASTER v1 — COVERAGE & GATE REPORT")
    lines.append("=" * 55)
    lines.append(f"Generated UTC: {gates['generated_at_utc']}")
    lines.append("")
    lines.append("RAW DATA")
    lines.append(f"- Raw agricultural rows: {raw_audit['raw_rows']:,}")
    lines.append(f"- Raw unique crops: {raw_audit['unique_crops']}")
    lines.append(f"- Raw unique districts: {raw_audit['unique_districts']}")
    lines.append(f"- Raw monthly range: {raw_audit['first_month']} to {raw_audit['last_month']}")
    lines.append(f"- Unique months: {raw_audit['unique_months']}")
    lines.append(f"- ANO/MES mismatches: {raw_audit['ano_mes_mismatches']}")
    lines.append(f"- Negative-value QA rows: {raw_audit['negative_value_rows']}")
    lines.append("")
    lines.append("TARGET CROPS / PANEL")
    lines.append(f"- Five-target-crop raw rows: {target_raw_rows:,}")
    lines.append(f"- Main yield period: {MAIN_START_YEAR}–{MAIN_END_YEAR}")
    lines.append(f"- Main non-balanced panel N: {main_n:,} -> {pass_fail(gate_main_n)} (gate N>{MIN_MAIN_PANEL_N})")
    lines.append(f"- Balanced districts: {len(complete_districts)}")
    lines.append(f"- Balanced panel N: {balanced_n:,} -> {pass_fail(gate_balanced_n)} (gate N>{MIN_BALANCED_PANEL_N})")
    lines.append("")
    lines.append("CROP COVERAGE")
    for _, row in crop_coverage.iterrows():
        lines.append(
            f"- {row['CROP_STD']} [{row['COD_CULTIVO']}]: "
            f"N={int(row['N_OBS'])}, districts={int(row['N_DISTRICTS'])}, "
            f"years={int(row['N_YEARS'])}, range={int(row['FIRST_YEAR'])}-{int(row['LAST_YEAR'])}"
        )
    lines.append("")
    lines.append("LAND COVERAGE")
    lines.append(
        f"- Panel district match rate: {land_coverage['district_match_rate']:.4%} "
        f"-> {pass_fail(gate_land_district)} (>99%)"
    )
    lines.append(
        f"- Physical agricultural area represented: {land_coverage['physical_area_coverage_rate']:.4%} "
        f"-> {pass_fail(gate_land_area)} (>99%)"
    )
    lines.append(
        f"- Piura physical agricultural area in MIDAGRI file: "
        f"{land_coverage['piura_total_physical_area_ha']:,.2f} ha"
    )
    lines.append(
        f"- Area represented by panel districts: {land_coverage['matched_physical_area_ha']:,.2f} ha"
    )
    lines.append("")
    lines.append("ICEN")
    lines.append(f"- Range: {icen_audit['first_date']} to {icen_audit['last_date']}")
    lines.append(f"- Covers every month 2016–2023: {pass_fail(gate_icen)}")
    lines.append("")
    lines.append("SOURCE DICTIONARY")
    lines.append(f"- Documented inconsistencies/limitations: {len(dictionary_issues)}")
    lines.append("- YIELD_RAW unit: UNRESOLVED because PRODUCCION unit is not explicitly stated in the official dictionary.")
    lines.append("")
    lines.append("AUDIT BENCHMARKS (not hard-coded outputs)")
    lines.append(f"- Raw rows benchmark {EXPECTED_RAW_ROWS:,}: {'MATCH' if raw_audit['raw_rows'] == EXPECTED_RAW_ROWS else 'DIFFERS'}")
    lines.append(f"- Target raw rows benchmark {EXPECTED_TARGET_RAW_ROWS:,}: {'MATCH' if target_raw_rows == EXPECTED_TARGET_RAW_ROWS else 'DIFFERS'}")
    lines.append(f"- Main panel benchmark {EXPECTED_MAIN_PANEL_N:,}: {'MATCH' if main_n == EXPECTED_MAIN_PANEL_N else 'DIFFERS'}")
    lines.append(f"- Balanced panel benchmark {EXPECTED_BALANCED_N:,}: {'MATCH' if balanced_n == EXPECTED_BALANCED_N else 'DIFFERS'}")
    lines.append("")
    lines.append(f"FINAL DATASET GATE: {'PASA' if overall else 'FALLA'}")

    (paths["qa"] / "coverage_report.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return gates


# -----------------------------------------------------------------------------
# Main pipeline
# -----------------------------------------------------------------------------


def main() -> int:
    root = Path(__file__).resolve().parent
    paths = project_paths(root)

    print_step("0/8 — Verificando archivos e integridad SHA-256")
    manifest = verify_files_and_hashes(paths)

    print_step("1/8 — Cargando y auditando CSV agrícola")
    agricultural, raw_audit = load_agricultural_csv(paths)

    print_step("2/8 — Auditando diccionario oficial")
    dictionary = load_dictionary(paths)
    dictionary_issues = build_dictionary_inconsistencies(dictionary, agricultural, paths)

    print_step("3/8 — Cargando superficie agrícola física MIDAGRI")
    land = load_land_physical(paths)

    print_step("4/8 — Limpiando ICEN")
    _, icen_audit = load_and_clean_icen(paths)

    print_step("5/8 — Construyendo agregaciones anuales 2016–2023")
    annual, target_raw_rows = build_annual_candidate(agricultural, paths)

    print_step("6/8 — Aplicando reglas de inclusión y construyendo panel_master")
    panel, land_coverage, _ = build_panel_master(annual, land, paths)

    print_step("7/8 — Construyendo panel balanceado y QA")
    balanced, complete_districts = build_balanced_panel(panel, paths)
    crop_coverage = build_crop_coverage(panel, paths)
    _ = flag_outliers(panel, paths)

    print_step("8/8 — Evaluando gates y generando reporte final")
    gates = write_coverage_report(
        paths=paths,
        manifest=manifest,
        raw_audit=raw_audit,
        target_raw_rows=target_raw_rows,
        panel=panel,
        balanced=balanced,
        complete_districts=complete_districts,
        land_coverage=land_coverage,
        crop_coverage=crop_coverage,
        icen_audit=icen_audit,
        dictionary_issues=dictionary_issues,
    )

    print("\n" + "=" * 72)
    print("DATASET MASTER v1 — RESUMEN FINAL")
    print("=" * 72)
    print(f"Filas agrícolas raw:              {raw_audit['raw_rows']:,}")
    print(f"Filas raw de 5 cultivos:          {target_raw_rows:,}")
    print(f"Panel principal 2016–2023 (N):    {len(panel):,}")
    print(f"Distritos balanceados:            {len(complete_districts)}")
    print(f"Panel balanceado (N):             {len(balanced):,}")
    print(f"Cobertura UBIGEO-MIDAGRI:         {land_coverage['district_match_rate']:.2%}")
    print(f"Cobertura área física agrícola:   {land_coverage['physical_area_coverage_rate']:.2%}")
    print(f"ICEN cubre 2016–2023:             {pass_fail(bool(icen_audit['covers_2016_2023']))}")
    print("Unidad YIELD_RAW:                  UNRESOLVED")
    print(f"GATE FINAL:                        {gates['overall_gate']}")
    print("=" * 72)
    print("Salidas:")
    print(f"- {paths['processed'] / 'panel_master.csv'}")
    print(f"- {paths['processed'] / 'panel_balanceado.csv'}")
    print(f"- {paths['processed'] / 'icen_clean.csv'}")
    print(f"- {paths['processed'] / 'land_physical.csv'}")
    print(f"- {paths['qa'] / 'coverage_report.txt'}")
    print(f"- {paths['qa'] / 'gate_report.json'}")

    return 0 if gates["overall_gate"] == "PASA" else 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print("\n" + "!" * 72, file=sys.stderr)
        print("PIPELINE DETENIDO", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        print("!" * 72, file=sys.stderr)
        raise
