# B2.0 Perennial Exposure Ledger Report

B2_0_VERDICT: B2_0 = PASS_FOR_INDEPENDENT_REVIEW

## Baseline
```json
{
  "branch": "phase/climate-exposure-build-v1",
  "branch_ok": true,
  "head": "c50a649724b9167cd1fbcc096df4eb62e76f2cfe",
  "head_ok": true,
  "parent": "656d5c8323b0f1bfd2538037a47d24cee2d3925e",
  "parent_ok": true
}
```

## Frozen Hash Gates
```json
{
  "actual": {
    "config/climate_exposure/climate_exposure_spec_v1.json": "e2e1eabbf8530cb0dfe8538d12f12d73a6a8e77c0e773351b593a14cbe1e268a",
    "data/processed/climate/climate_anomalies.parquet": "11a1fc61cab062faf70e3f12d2a06f050a2ccf094273807192943ad130deb6df",
    "data/processed/phenology/phenology_windows_frozen.csv": "ea25d949be9834a9e35352d970bb1b2172cac7d49db7eabb101ddfde9cfb657d",
    "data/processed/phenology/transient_cohort_exposures.parquet": "e4ce7922f00a516643a5de832cc38377e20b3755ac46152cfb79900441564b39",
    "outputs/climate_exposure/B0_PREFLIGHT_REPORT.md": "47c2ff2db2df482b370cae74b1857700f12b14dda105846cd63bd62a7f0f02bf",
    "outputs/climate_exposure/B1_TRANSIENT_COHORT_LEDGER_REPORT.md": "256b41893b3b86a364899b1376f1a2fbb7c39f81efba41d9e507c78bceec12a2",
    "outputs/phenology/PHENOLOGY_MASTER_V1_FREEZE.md": "f9447e10918547011512d629b902dc71ec15b8d2ad74d28901f40f4afffa0ee9",
    "outputs/phenology/qa/climate_exposure_spec_gate_report.json": "872b508fa93e2f8a5799c6446a1cd46bbf5bf416d2b55cb181132410ef6fcd50",
    "scripts/build_transient_cohort_exposures.py": "1b8c23dcc76b13bbfba3559e56c4ea85d361d0907124028d7ae981674956186b",
    "scripts/climate_exposure_b0_preflight.py": "43d44bb71f81c804aa51694c553b10eeeae8d525b021928db3280f61261cb803",
    "tests/test_climate_exposure_b0_preflight.py": "fd9d7eb6a0b26e0b197294d8b08252a3327e8fab6e51a10b119ed0efb6b85b1f",
    "tests/test_transient_cohort_exposures.py": "b1ed9eb31961eac6918ee04e4d94d6c941e437f2cec067ba3948dca9c86226e5"
  },
  "expected": {
    "config/climate_exposure/climate_exposure_spec_v1.json": "e2e1eabbf8530cb0dfe8538d12f12d73a6a8e77c0e773351b593a14cbe1e268a",
    "data/processed/climate/climate_anomalies.parquet": "11a1fc61cab062faf70e3f12d2a06f050a2ccf094273807192943ad130deb6df",
    "data/processed/phenology/phenology_windows_frozen.csv": "ea25d949be9834a9e35352d970bb1b2172cac7d49db7eabb101ddfde9cfb657d",
    "data/processed/phenology/transient_cohort_exposures.parquet": "e4ce7922f00a516643a5de832cc38377e20b3755ac46152cfb79900441564b39",
    "outputs/climate_exposure/B0_PREFLIGHT_REPORT.md": "47c2ff2db2df482b370cae74b1857700f12b14dda105846cd63bd62a7f0f02bf",
    "outputs/climate_exposure/B1_TRANSIENT_COHORT_LEDGER_REPORT.md": "256b41893b3b86a364899b1376f1a2fbb7c39f81efba41d9e507c78bceec12a2",
    "outputs/phenology/PHENOLOGY_MASTER_V1_FREEZE.md": "f9447e10918547011512d629b902dc71ec15b8d2ad74d28901f40f4afffa0ee9",
    "outputs/phenology/qa/climate_exposure_spec_gate_report.json": "872b508fa93e2f8a5799c6446a1cd46bbf5bf416d2b55cb181132410ef6fcd50",
    "scripts/build_transient_cohort_exposures.py": "1b8c23dcc76b13bbfba3559e56c4ea85d361d0907124028d7ae981674956186b",
    "scripts/climate_exposure_b0_preflight.py": "43d44bb71f81c804aa51694c553b10eeeae8d525b021928db3280f61261cb803",
    "tests/test_climate_exposure_b0_preflight.py": "fd9d7eb6a0b26e0b197294d8b08252a3327e8fab6e51a10b119ed0efb6b85b1f",
    "tests/test_transient_cohort_exposures.py": "b1ed9eb31961eac6918ee04e4d94d6c941e437f2cec067ba3948dca9c86226e5"
  },
  "status": "PASS"
}
```

## Output Invariants
```json
{
  "by_crop": {
    "13010170102": 622,
    "13010210000": 255,
    "15010040000": 780
  },
  "by_crop_window": {
    "13010170102|LEMON_FULL_YEAR_T": 311,
    "13010170102|LEMON_FULL_YEAR_T_MINUS_1": 311,
    "13010210000|MANGO_MAY_JUN_CURRENT_YEAR": 255,
    "15010040000|BANANA_FULL_YEAR_T": 390,
    "15010040000|BANANA_FULL_YEAR_T_MINUS_1": 390
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
  "duplicate_output_keys": 0,
  "failure_reason_counts": {
    "NONE": 1657
  },
  "internal_gap": 0,
  "invalid": 0,
  "negative_rain_rows": 0,
  "nonfinite_climate_cells": 0,
  "null_climate_cells": 0,
  "outside_range": 0,
  "panel_checks": {
    "by_crop": {
      "13010170102": 311,
      "13010210000": 255,
      "15010040000": 390
    },
    "duplicate_panel_keys": 0,
    "invalid_cod_cultivo": 0,
    "invalid_ubigeo": 0,
    "missing_cod_cultivo": 0,
    "missing_ubigeo": 0,
    "panel_perennial_keys": 956,
    "status": "PASS",
    "unexpected_crop_std": 0
  },
  "reference_period_contract_failures": 0,
  "rows": 1657,
  "status": "PASS",
  "time_basis_values": [
    "CALENDAR_YEAR"
  ],
  "tmin_gt_tmax_rows": 0,
  "valid": 1657
}
```

## Arrow Schema
```text
UBIGEO: string not null
COD_CULTIVO: string not null
CROP_STD: string not null
TIME_BASIS: string not null
REFERENCE_PERIOD_ID: string not null
REFERENCE_CALENDAR_YEAR: int16 not null
WINDOW_ID: string not null
RAIN_MM: double not null
TMAX_C: double not null
TMIN_C: double not null
RAIN_ANOM_MM: double not null
TMAX_ANOM_C: double not null
TMIN_ANOM_C: double not null
RAIN_Z: double not null
TMAX_Z: double not null
TMIN_Z: double not null
EXPOSURE_VALID: bool not null
FAILURE_REASON: string not null
```

## Writer Configuration
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
      "case": "earliest_mango",
      "expected_months": "201605|201606",
      "key": "200101|13010210000|2016|MANGO_MAY_JUN_CURRENT_YEAR",
      "status": "PASS"
    },
    {
      "case": "latest_mango",
      "expected_months": "202205|202206",
      "key": "200806|13010210000|2022|MANGO_MAY_JUN_CURRENT_YEAR",
      "status": "PASS"
    },
    {
      "case": "earliest_lemon_t",
      "expected_months": "201601|201602|201603|201604|201605|201606|201607|201608|201609|201610|201611|201612",
      "key": "200101|13010170102|2016|LEMON_FULL_YEAR_T",
      "status": "PASS"
    },
    {
      "case": "earliest_lemon_t_minus_1",
      "expected_months": "201501|201502|201503|201504|201505|201506|201507|201508|201509|201510|201511|201512",
      "key": "200101|13010170102|2016|LEMON_FULL_YEAR_T_MINUS_1",
      "status": "PASS"
    },
    {
      "case": "latest_lemon_t_minus_1",
      "expected_months": "202201|202202|202203|202204|202205|202206|202207|202208|202209|202210|202211|202212",
      "key": "200806|13010170102|2023|LEMON_FULL_YEAR_T_MINUS_1",
      "status": "PASS"
    },
    {
      "case": "earliest_banana_t",
      "expected_months": "201601|201602|201603|201604|201605|201606|201607|201608|201609|201610|201611|201612",
      "key": "200101|15010040000|2016|BANANA_FULL_YEAR_T",
      "status": "PASS"
    },
    {
      "case": "earliest_banana_t_minus_1",
      "expected_months": "201501|201502|201503|201504|201505|201506|201507|201508|201509|201510|201511|201512",
      "key": "200101|15010040000|2016|BANANA_FULL_YEAR_T_MINUS_1",
      "status": "PASS"
    },
    {
      "case": "t_minus_1_prior_year_crossing",
      "expected_months": "201501|201502|201503|201504|201505|201506|201507|201508|201509|201510|201511|201512",
      "key": "200101|13010170102|2016|LEMON_FULL_YEAR_T_MINUS_1",
      "status": "PASS"
    }
  ],
  "status": "PASS"
}
```

## Two-Run Reproducibility
```json
{
  "run1_sha256": "3fde5c7fc7a00f4c6600a18f60935bad213408ffa2ba3bac5828603e46984714",
  "run2_sha256": "3fde5c7fc7a00f4c6600a18f60935bad213408ffa2ba3bac5828603e46984714",
  "status": "PASS"
}
```

## Canonical Parquet SHA256
3fde5c7fc7a00f4c6600a18f60935bad213408ffa2ba3bac5828603e46984714

## Outcome Firewall
```json
{
  "climate_columns": [
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
  "other_inputs_read": false,
  "panel_usecols": [
    "UBIGEO",
    "COD_CULTIVO",
    "CROP_STD",
    "ANO"
  ],
  "status": "PASS"
}
```

## Forbidden Artifact Check
```json
{
  "existing": [],
  "status": "PASS"
}
```
