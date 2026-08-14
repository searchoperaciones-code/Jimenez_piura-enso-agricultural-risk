# B1.0 Transient Cohort Exposure Ledger Report

B1_0_VERDICT: B1_0 = PASS_FOR_INDEPENDENT_REVIEW

## Baseline
```json
{
  "branch": "phase/climate-exposure-build-v1",
  "branch_ok": true,
  "head": "656d5c8323b0f1bfd2538037a47d24cee2d3925e",
  "head_ok": true,
  "parent": "1d6cf2701d00c245f17f381119876548034ae60c",
  "parent_ok": true
}
```

## Input Hashes and Frozen Gates
```json
{
  "actual": {
    "config/climate_exposure/climate_exposure_spec_v1.json": "e2e1eabbf8530cb0dfe8538d12f12d73a6a8e77c0e773351b593a14cbe1e268a",
    "data/processed/climate/climate_anomalies.parquet": "11a1fc61cab062faf70e3f12d2a06f050a2ccf094273807192943ad130deb6df",
    "data/processed/phenology/phenology_windows_frozen.csv": "ea25d949be9834a9e35352d970bb1b2172cac7d49db7eabb101ddfde9cfb657d",
    "outputs/climate_exposure/B0_PREFLIGHT_REPORT.md": "47c2ff2db2df482b370cae74b1857700f12b14dda105846cd63bd62a7f0f02bf",
    "outputs/phenology/PHENOLOGY_MASTER_V1_FREEZE.md": "f9447e10918547011512d629b902dc71ec15b8d2ad74d28901f40f4afffa0ee9",
    "outputs/phenology/qa/climate_exposure_spec_gate_report.json": "872b508fa93e2f8a5799c6446a1cd46bbf5bf416d2b55cb181132410ef6fcd50",
    "scripts/climate_exposure_b0_preflight.py": "43d44bb71f81c804aa51694c553b10eeeae8d525b021928db3280f61261cb803",
    "tests/test_climate_exposure_b0_preflight.py": "fd9d7eb6a0b26e0b197294d8b08252a3327e8fab6e51a10b119ed0efb6b85b1f"
  },
  "expected": {
    "config/climate_exposure/climate_exposure_spec_v1.json": "e2e1eabbf8530cb0dfe8538d12f12d73a6a8e77c0e773351b593a14cbe1e268a",
    "data/processed/climate/climate_anomalies.parquet": "11a1fc61cab062faf70e3f12d2a06f050a2ccf094273807192943ad130deb6df",
    "data/processed/phenology/phenology_windows_frozen.csv": "ea25d949be9834a9e35352d970bb1b2172cac7d49db7eabb101ddfde9cfb657d",
    "outputs/climate_exposure/B0_PREFLIGHT_REPORT.md": "47c2ff2db2df482b370cae74b1857700f12b14dda105846cd63bd62a7f0f02bf",
    "outputs/phenology/PHENOLOGY_MASTER_V1_FREEZE.md": "f9447e10918547011512d629b902dc71ec15b8d2ad74d28901f40f4afffa0ee9",
    "outputs/phenology/qa/climate_exposure_spec_gate_report.json": "872b508fa93e2f8a5799c6446a1cd46bbf5bf416d2b55cb181132410ef6fcd50",
    "scripts/climate_exposure_b0_preflight.py": "43d44bb71f81c804aa51694c553b10eeeae8d525b021928db3280f61261cb803",
    "tests/test_climate_exposure_b0_preflight.py": "fd9d7eb6a0b26e0b197294d8b08252a3327e8fab6e51a10b119ed0efb6b85b1f"
  },
  "status": "PASS"
}
```

## Source and Output Invariants
```json
{
  "aggregated_tmin_gt_tmax": 0,
  "allowed_campaign_statuses": [
    "AMBIGUOUS_CROSS_CAMPAIGN",
    "UNAMBIGUOUS_AGRONOMIC_CAMPAIGN"
  ],
  "allowed_failure_reasons": [
    "CLIMATE_WINDOW_RIGHT_TRUNCATED",
    "NONE"
  ],
  "by_crop": {
    "14010020000": 4019,
    "14010070000": 4958
  },
  "campaign_status_by_crop": {
    "14010020000|AMBIGUOUS_CROSS_CAMPAIGN": 771,
    "14010020000|UNAMBIGUOUS_AGRONOMIC_CAMPAIGN": 3248,
    "14010070000|AMBIGUOUS_CROSS_CAMPAIGN": 1287,
    "14010070000|UNAMBIGUOUS_AGRONOMIC_CAMPAIGN": 3671
  },
  "climate_checks": {
    "coverage_max_yyyymm": 202412,
    "coverage_min_yyyymm": 199101,
    "duplicate_climate_keys": 0,
    "missing_by_variable": {
      "RAIN_ANOM_MM": 0,
      "RAIN_MM": 0,
      "RAIN_Z": 0,
      "TMAX_ANOM_C": 0,
      "TMAX_C": 0,
      "TMAX_Z": 0,
      "TMIN_ANOM_C": 0,
      "TMIN_C": 0,
      "TMIN_Z": 0
    },
    "negative_rain_mm": 0,
    "nonfinite_by_variable": {
      "RAIN_ANOM_MM": 0,
      "RAIN_MM": 0,
      "RAIN_Z": 0,
      "TMAX_ANOM_C": 0,
      "TMAX_C": 0,
      "TMAX_Z": 0,
      "TMIN_ANOM_C": 0,
      "TMIN_C": 0,
      "TMIN_Z": 0
    },
    "rows": 22440,
    "status": "PASS",
    "tmin_gt_tmax": 0
  },
  "complete": 8724,
  "complete_nonfinite_climate_cells": 0,
  "complete_null_climate_cells": 0,
  "duplicate_output_keys": 0,
  "failure_reason_counts": {
    "CLIMATE_WINDOW_RIGHT_TRUNCATED": 253,
    "NONE": 8724
  },
  "incomplete": 253,
  "incomplete_non_null_climate_cells": 0,
  "internal_gap": 0,
  "internal_gap_by_crop": {},
  "negative_rain_aggregates": 0,
  "right_edge_anchor_months": {
    "202409": 28,
    "202410": 75,
    "202411": 75,
    "202412": 75
  },
  "right_truncated": 253,
  "right_truncated_by_crop": {
    "14010020000": 115,
    "14010070000": 138
  },
  "rows": 8977,
  "siembra_by_crop": {
    "14010020000": {
      "missing": 0,
      "observed": 4019,
      "rows": 4019,
      "zero": 2747
    },
    "14010070000": {
      "missing": 0,
      "observed": 4958,
      "rows": 4958,
      "zero": 3145
    }
  },
  "source_checks": {
    "by_crop": {
      "14010020000": 4019,
      "14010070000": 4958
    },
    "duplicate_source_keys": 0,
    "invalid_cod_cultivo": 0,
    "invalid_ubigeo": 0,
    "mes_mismatch": 0,
    "missing_cod_cultivo": 0,
    "missing_ubigeo": 0,
    "month_out_of_range": 0,
    "negative_siembras": 0,
    "source_rows": 8977,
    "status": "PASS",
    "unexpected_crop_std": 0
  },
  "status": "PASS"
}
```

## Arrow Schema
```text
UBIGEO: string not null
COD_CULTIVO: string not null
CROP_STD: string not null
ANCHOR_YEAR: int16 not null
ANCHOR_MONTH: int8 not null
ANCHOR_YYYYMM: int32 not null
WINDOW_ID: string not null
ARCHITECTURE: string not null
SIEMBRA: double
SIEMBRA_OBSERVED: bool not null
CLIMATE_WINDOW_START_YYYYMM: int32 not null
CLIMATE_WINDOW_END_YYYYMM: int32 not null
EXPECTED_CLIMATE_MONTHS: string not null
SUPPORTED_CLIMATE_MONTHS: string not null
CLIMATE_WINDOW_COMPLETE: bool not null
RAIN_MM: double
TMAX_C: double
TMIN_C: double
RAIN_ANOM_MM: double
TMAX_ANOM_C: double
TMIN_ANOM_C: double
RAIN_Z: double
TMAX_Z: double
TMIN_Z: double
ANCHOR_DATE_MIN: date32[day] not null
ANCHOR_DATE_MAX: date32[day] not null
ATTRIBUTION_L_MIN_DAYS: int16 not null
ATTRIBUTION_L_MAX_DAYS: int16 not null
HARVEST_DATE_MIN: date32[day] not null
HARVEST_DATE_MAX: date32[day] not null
CAMPAIGN_MIN: string not null
CAMPAIGN_MAX: string not null
CAMPAIGN_ATTRIBUTION_STATUS: string not null
ASSIGNED_CAMPAIGN_ID: string
COHORT_EXPOSURE_VALID: bool not null
FAILURE_REASON: string not null
```

## Parquet Writer Contract
```json
{
  "compression": "zstd",
  "data_page_version": "2.0",
  "use_dictionary": false,
  "version": "2.6",
  "write_statistics": true
}
```

## Independent Numerical Recomputation
```json
{
  "cases": [
    {
      "case": "earliest_complete_rice",
      "expected_months": "201511|201512",
      "key": "200101|14010020000|201508|RICE_FLOWERING_95_110_DAS",
      "status": "PASS"
    },
    {
      "case": "latest_complete_rice_before_right_truncation",
      "expected_months": "202411|202412",
      "key": "200806|14010020000|202408|RICE_FLOWERING_95_110_DAS",
      "status": "PASS"
    },
    {
      "case": "earliest_complete_mad",
      "expected_months": "201509|201510|201511",
      "key": "200101|14010070000|201508|MAD_MPLUS1_MPLUS3",
      "status": "PASS"
    },
    {
      "case": "latest_complete_mad_before_right_truncation",
      "expected_months": "202410|202411|202412",
      "key": "200806|14010070000|202409|MAD_MPLUS1_MPLUS3",
      "status": "PASS"
    },
    {
      "case": "year_crossing_window",
      "expected_months": "202312|202401",
      "key": "200101|14010020000|202309|RICE_FLOWERING_95_110_DAS",
      "status": "PASS"
    },
    {
      "case": "zero_sowing_complete",
      "expected_months": "201602|201603",
      "key": "200101|14010020000|201511|RICE_FLOWERING_95_110_DAS",
      "status": "PASS"
    },
    {
      "case": "ambiguous_campaign_complete",
      "expected_months": "201606|201607",
      "key": "200101|14010020000|201603|RICE_FLOWERING_95_110_DAS",
      "status": "PASS"
    }
  ],
  "status": "PASS"
}
```

## Two-Run Reproducibility
```json
{
  "run1_sha256": "e4ce7922f00a516643a5de832cc38377e20b3755ac46152cfb79900441564b39",
  "run2_sha256": "e4ce7922f00a516643a5de832cc38377e20b3755ac46152cfb79900441564b39",
  "status": "PASS"
}
```

## Canonical Parquet SHA256
e4ce7922f00a516643a5de832cc38377e20b3755ac46152cfb79900441564b39

## Outcome Firewall
```json
{
  "climate_usecols": [
    "UBIGEO",
    "YEAR",
    "MONTH",
    "RAIN_MM",
    "TMAX_C",
    "TMIN_C",
    "RAIN_ANOM_MM",
    "TMAX_ANOM_C",
    "TMIN_ANOM_C",
    "RAIN_Z",
    "TMAX_Z",
    "TMIN_Z"
  ],
  "icen_read": false,
  "panel_balanceado_read": false,
  "panel_master_read": false,
  "status": "PASS",
  "temporal_usecols": [
    "UBIGEO",
    "COD_CULTIVO",
    "CROP_STD",
    "ANO",
    "MES",
    "MONTH",
    "SIEMBRA"
  ]
}
```

## Forbidden Artifact Check
```json
{
  "existing": [],
  "status": "PASS"
}
```
