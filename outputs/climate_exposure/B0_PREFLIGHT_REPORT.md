# CLIMATE EXPOSURE MASTER v1 B0 Preflight Report

FINAL_B0_VERDICT: B0_2 = PASS_FOR_DIRECTOR_FREEZE_REVIEW

## B0.1 Empirical Findings
- EMPIRICAL_STATUS: PASS_FOR_DIRECTOR_REVIEW
- The following sections preserve B0.1 empirical diagnostics without changing scientific freeze decisions.

## Baseline
- BRANCH: phase/climate-exposure-build-v1
- HEAD SHA: 1d6cf2701d00c245f17f381119876548034ae60c
- BASE TAG TARGET: 1d6cf2701d00c245f17f381119876548034ae60c

## Upstream Hash Gate
- STATUS: PASS
- climate_exposure_spec_v1.json: e2e1eabbf8530cb0dfe8538d12f12d73a6a8e77c0e773351b593a14cbe1e268a (expected e2e1eabbf8530cb0dfe8538d12f12d73a6a8e77c0e773351b593a14cbe1e268a)
- phenology_windows_frozen.csv: ea25d949be9834a9e35352d970bb1b2172cac7d49db7eabb101ddfde9cfb657d (expected ea25d949be9834a9e35352d970bb1b2172cac7d49db7eabb101ddfde9cfb657d)
- PHENOLOGY_MASTER_V1_FREEZE.md: f9447e10918547011512d629b902dc71ec15b8d2ad74d28901f40f4afffa0ee9 (expected f9447e10918547011512d629b902dc71ec15b8d2ad74d28901f40f4afffa0ee9)
- climate_anomalies.parquet: 11a1fc61cab062faf70e3f12d2a06f050a2ccf094273807192943ad130deb6df (expected 11a1fc61cab062faf70e3f12d2a06f050a2ccf094273807192943ad130deb6df)

## Input Schema Summary
```json
{
  "climate_anomalies": {
    "columns": [
      "UBIGEO",
      "DATE",
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
    "loaded_dtypes": {
      "DATE": "datetime64[us]",
      "MONTH": "int64",
      "RAIN_ANOM_MM": "float64",
      "RAIN_MM": "float64",
      "RAIN_Z": "float64",
      "TMAX_ANOM_C": "float64",
      "TMAX_C": "float64",
      "TMAX_Z": "float64",
      "TMIN_ANOM_C": "float64",
      "TMIN_C": "float64",
      "TMIN_Z": "float64",
      "UBIGEO": "string",
      "YEAR": "int64"
    }
  },
  "panel_master": {
    "header": [
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
      "MONTHS_PRESENT"
    ],
    "loaded_columns": [
      "UBIGEO",
      "COD_CULTIVO",
      "CROP_STD",
      "ANO"
    ],
    "loaded_dtypes": {
      "ANO": "int64",
      "COD_CULTIVO": "string",
      "CROP_STD": "string",
      "UBIGEO": "string"
    },
    "note": "CSV has no physical dtype; outcome-value columns were not loaded."
  },
  "phenology_windows_frozen": {
    "columns": [
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
      "NOTES"
    ],
    "loaded_dtypes": {
      "ANCHOR_SEMANTICS": "string",
      "ANCHOR_VARIABLE": "string",
      "ARCHITECTURE": "string",
      "CALENDAR_MONTH_END": "string",
      "CALENDAR_MONTH_START": "string",
      "COD_CULTIVO": "string",
      "COHORT_WEIGHTING": "string",
      "CROP_STD": "string",
      "END_DAS": "string",
      "END_OFFSET_MONTH": "string",
      "FREEZE_STATUS": "string",
      "FREEZE_VERSION": "string",
      "NOTES": "string",
      "START_DAS": "string",
      "START_OFFSET_MONTH": "string",
      "WINDOW_ID": "string",
      "WINDOW_RULE": "string",
      "YEAR_OFFSET": "string",
      "YEAR_RELATION": "string"
    }
  },
  "temporal_structure_monthly": {
    "header": [
      "UBIGEO",
      "COD_CULTIVO",
      "CROP_STD",
      "CULTIVO_SOURCE",
      "ANO",
      "MES",
      "MONTH",
      "TEMPORAL_ROLE",
      "SOURCE_12_MONTHS_PRESENT",
      "SIEMBRA",
      "COSECHA",
      "PRODUCCION",
      "SOWN_ANNUAL_DENOMINATOR",
      "SOWN_MISSING_MONTH_COUNT",
      "SOWN_POSITIVE_MONTH_COUNT",
      "SOWN_DENOMINATOR_STATUS",
      "SOWN_SOURCE_12_MONTHS_PRESENT",
      "SOWN_SHARE",
      "HARVEST_ANNUAL_DENOMINATOR",
      "HARVEST_MISSING_MONTH_COUNT",
      "HARVEST_POSITIVE_MONTH_COUNT",
      "HARVEST_DENOMINATOR_STATUS",
      "HARVEST_SOURCE_12_MONTHS_PRESENT",
      "HARVEST_SHARE",
      "PRODUCTION_ANNUAL_DENOMINATOR",
      "PRODUCTION_MISSING_MONTH_COUNT",
      "PRODUCTION_POSITIVE_MONTH_COUNT",
      "PRODUCTION_DENOMINATOR_STATUS",
      "PRODUCTION_SOURCE_12_MONTHS_PRESENT",
      "PRODUCTION_SHARE"
    ],
    "loaded_columns": [
      "UBIGEO",
      "COD_CULTIVO",
      "CROP_STD",
      "ANO",
      "MES",
      "MONTH",
      "TEMPORAL_ROLE",
      "SOURCE_12_MONTHS_PRESENT",
      "SIEMBRA",
      "SOWN_MISSING_MONTH_COUNT",
      "SOWN_POSITIVE_MONTH_COUNT",
      "SOWN_DENOMINATOR_STATUS",
      "SOWN_SOURCE_12_MONTHS_PRESENT"
    ],
    "loaded_dtypes": {
      "ANO": "int64",
      "COD_CULTIVO": "string",
      "CROP_STD": "string",
      "MES": "int64",
      "MONTH": "int64",
      "SIEMBRA": "float64",
      "SOURCE_12_MONTHS_PRESENT": "bool",
      "SOWN_DENOMINATOR_STATUS": "string",
      "SOWN_MISSING_MONTH_COUNT": "int64",
      "SOWN_POSITIVE_MONTH_COUNT": "int64",
      "SOWN_SOURCE_12_MONTHS_PRESENT": "bool",
      "TEMPORAL_ROLE": "string",
      "UBIGEO": "string"
    },
    "note": "Only SIEMBRA and sowing/source metadata were loaded."
  }
}
```

## Identifier Canonicalization
```json
{
  "climate": {
    "UBIGEO": {
      "colliding_canonical_values": 0,
      "invalid_format": 0,
      "max_length": 6,
      "min_length": 6,
      "missing": 0,
      "rows": 22440
    }
  },
  "panel": {
    "COD_CULTIVO": {
      "colliding_canonical_values": 0,
      "invalid_format": 0,
      "max_length": 11,
      "min_length": 11,
      "missing": 0,
      "rows": 1701
    },
    "UBIGEO": {
      "colliding_canonical_values": 0,
      "invalid_format": 0,
      "max_length": 6,
      "min_length": 6,
      "missing": 0,
      "rows": 1701
    }
  },
  "set_consistency": {
    "panel_crop_codes": [
      "13010170102",
      "13010210000",
      "14010020000",
      "14010070000",
      "15010040000"
    ],
    "panel_ubigeo_minus_climate": [],
    "temporal_crop_codes": [
      "13010170102",
      "13010210000",
      "14010020000",
      "14010070000",
      "15010040000"
    ],
    "temporal_ubigeo_minus_climate": []
  },
  "temporal": {
    "COD_CULTIVO": {
      "colliding_canonical_values": 0,
      "invalid_format": 0,
      "max_length": 11,
      "min_length": 11,
      "missing": 0,
      "rows": 23540
    },
    "UBIGEO": {
      "colliding_canonical_values": 0,
      "invalid_format": 0,
      "max_length": 6,
      "min_length": 6,
      "missing": 0,
      "rows": 23540
    }
  }
}
```

## Unique Keys
```json
{
  "climate_anomalies_key": {
    "columns": [
      "UBIGEO",
      "YEAR",
      "MONTH"
    ],
    "duplicate_rows": 0,
    "rows": 22440
  },
  "panel_master_key": {
    "columns": [
      "UBIGEO",
      "COD_CULTIVO",
      "ANO"
    ],
    "duplicate_rows": 0,
    "rows": 1701
  },
  "phenology_windows_key": {
    "columns": [
      "WINDOW_ID"
    ],
    "duplicate_rows": 0,
    "rows": 7
  },
  "temporal_structure_monthly_key": {
    "columns": [
      "UBIGEO",
      "COD_CULTIVO",
      "MES"
    ],
    "duplicate_rows": 0,
    "rows": 23540
  }
}
```

## Transient Candidate Universes
```json
{
  "A_all_transient_temporal_rows": {
    "by_crop": {
      "14010020000": 4019,
      "14010070000": 4958
    },
    "role": "CANONICAL_TRANSIENT_COHORT_LEDGER_UNIVERSE",
    "rows": 8977
  },
  "B_transient_rows_in_main_panel_key_years": {
    "by_crop": {
      "14010020000": 3334,
      "14010070000": 4083
    },
    "role": "DIAGNOSTIC_ONLY_NOT_CANONICAL_UNIVERSE",
    "rows": 7417
  },
  "C_strict_required_campaign_sowing_rows": {
    "by_crop_required": {
      "14010020000": 4760,
      "14010070000": 6075
    },
    "missing_rows": 2143,
    "observed_rows": 8692,
    "required_rows": 10835,
    "role": "STRICT_DIAGNOSTIC_ONLY_NOT_COHORT_LEDGER_UNIVERSE"
  },
  "D_contextual_edge_support_2015_2024": {
    "by_crop_year": {
      "14010020000|2015": 170,
      "14010020000|2024": 427,
      "14010070000|2015": 207,
      "14010070000|2024": 565
    },
    "role": "CONTEXT_EDGE_SUPPORT_RETAINED_IN_CANONICAL_SOURCE_UNIVERSE",
    "rows": 1369
  },
  "canonical_universe_name": "ALL_OBSERVED_TRANSIENT_TEMPORAL_SOURCE_ROWS",
  "canonical_universe_rows": 8977,
  "canonical_universe_status": "DIRECTOR_APPROVED_B0_2",
  "no_main_panel_restriction": true,
  "no_strict_slot_universe": true,
  "no_synthetic_month_densification": true
}
```

## Perennial Structural Count
```json
{
  "by_crop_window": {
    "13010170102|LEMON_FULL_YEAR_T": 311,
    "13010170102|LEMON_FULL_YEAR_T_MINUS_1": 311,
    "13010210000|MANGO_MAY_JUN_CURRENT_YEAR": 255,
    "15010040000|BANANA_FULL_YEAR_T": 390,
    "15010040000|BANANA_FULL_YEAR_T_MINUS_1": 390
  },
  "candidate_rows": 1657,
  "complete_rows": 1657,
  "expected_candidate_rows": 1657,
  "incomplete_rows": 0,
  "status": "PASS"
}
```

## Strict Diagnostic Reproduction
```json
{
  "by_crop": {
    "14010020000": {
      "total": 340,
      "valid": 31
    },
    "14010070000": {
      "total": 405,
      "valid": 7
    }
  },
  "by_crop_campaign": {
    "14010020000|2015/2016": {
      "total": 43,
      "valid": 0
    },
    "14010020000|2016/2017": {
      "total": 44,
      "valid": 3
    },
    "14010020000|2017/2018": {
      "total": 42,
      "valid": 2
    },
    "14010020000|2018/2019": {
      "total": 43,
      "valid": 8
    },
    "14010020000|2019/2020": {
      "total": 44,
      "valid": 4
    },
    "14010020000|2020/2021": {
      "total": 41,
      "valid": 7
    },
    "14010020000|2021/2022": {
      "total": 41,
      "valid": 4
    },
    "14010020000|2022/2023": {
      "total": 42,
      "valid": 3
    },
    "14010070000|2015/2016": {
      "total": 52,
      "valid": 0
    },
    "14010070000|2016/2017": {
      "total": 51,
      "valid": 0
    },
    "14010070000|2017/2018": {
      "total": 48,
      "valid": 3
    },
    "14010070000|2018/2019": {
      "total": 50,
      "valid": 2
    },
    "14010070000|2019/2020": {
      "total": 49,
      "valid": 1
    },
    "14010070000|2020/2021": {
      "total": 48,
      "valid": 0
    },
    "14010070000|2021/2022": {
      "total": 52,
      "valid": 0
    },
    "14010070000|2022/2023": {
      "total": 55,
      "valid": 1
    }
  },
  "combined": {
    "total": 745,
    "valid": 38
  },
  "expected": {
    "14010020000": {
      "total": 340,
      "valid": 31
    },
    "14010070000": {
      "total": 405,
      "valid": 7
    },
    "combined": {
      "total": 745,
      "valid": 38
    }
  },
  "status": "PASS"
}
```

## Missing vs Zero SIEMBRA
```json
{
  "13010170102|LIMON SUTIL": {
    "monthly_rows": 4779,
    "sowing_missing": 0,
    "sowing_negative": 0,
    "sowing_observed": 4779,
    "sowing_positive": 57,
    "sowing_zero": 4722
  },
  "13010210000|MANGO": {
    "monthly_rows": 4152,
    "sowing_missing": 0,
    "sowing_negative": 0,
    "sowing_observed": 4152,
    "sowing_positive": 53,
    "sowing_zero": 4099
  },
  "14010020000|ARROZ": {
    "monthly_rows": 4019,
    "sowing_missing": 0,
    "sowing_negative": 0,
    "sowing_observed": 4019,
    "sowing_positive": 1272,
    "sowing_zero": 2747
  },
  "14010070000|MAIZ AMARILLO DURO": {
    "monthly_rows": 4958,
    "sowing_missing": 0,
    "sowing_negative": 0,
    "sowing_observed": 4958,
    "sowing_positive": 1813,
    "sowing_zero": 3145
  },
  "15010040000|PLATANOS Y BANANAS": {
    "monthly_rows": 5632,
    "sowing_missing": 0,
    "sowing_negative": 0,
    "sowing_observed": 5632,
    "sowing_positive": 68,
    "sowing_zero": 5564
  }
}
```

## Boundary Findings
```json
{
  "climate_end_yyyymm": 202412,
  "left_truncation_by_crop": {
    "14010020000": 215,
    "14010070000": 312
  },
  "left_truncation_panel_keys": 95,
  "left_truncation_required_sowing_months": 527,
  "right_edge_affected_rows": 253,
  "right_edge_by_crop_anchor_yyyymm": {
    "14010020000|202409": 28,
    "14010020000|202410": 29,
    "14010020000|202411": 28,
    "14010020000|202412": 30,
    "14010070000|202410": 46,
    "14010070000|202411": 47,
    "14010070000|202412": 45
  },
  "right_edge_candidate_months": [
    202409,
    202410,
    202411,
    202412
  ],
  "source_start_yyyymm": 201508,
  "structural_left_truncation_campaign": "2015/2016"
}
```

## Climate Coverage and Completeness
```json
{
  "candidate_completeness": {
    "perennial_candidate_rows_assessed": 1657,
    "perennial_complete_rows": 1657,
    "perennial_incomplete_rows": 0,
    "transient_candidate_rows_assessed": 8977,
    "transient_complete_rows": 8724,
    "transient_incomplete_rows": 253
  },
  "coverage": {
    "all_nine_frozen_variables_available": true,
    "date_max": "2024-12-01",
    "date_min": "1991-01-01",
    "district_count": 55,
    "duplicate_district_month_keys": 0,
    "missing_by_authorized_variable": {
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
    "nonfinite_by_authorized_variable": {
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
    "row_count": 22440,
    "tmin_gt_tmax": 0,
    "yyyymm_max": 202412,
    "yyyymm_min": 199101
  }
}
```

## Outcome Firewall
```json
{
  "forbidden_outputs": {
    "existing": [],
    "status": "PASS"
  },
  "forbidden_value_tokens_not_loaded": [
    "YIELD_RAW",
    "PRODUCCION",
    "COSECHA",
    "PRECIO",
    "PRECIO_CHACRA",
    "ICEN"
  ],
  "icen_status": "NOT_READ_NOT_MERGED_NOT_CLASSIFIED",
  "panel_loaded_columns": [
    "UBIGEO",
    "COD_CULTIVO",
    "CROP_STD",
    "ANO"
  ],
  "status": "PASS",
  "temporal_loaded_columns": [
    "UBIGEO",
    "COD_CULTIVO",
    "CROP_STD",
    "ANO",
    "MES",
    "MONTH",
    "TEMPORAL_ROLE",
    "SOURCE_12_MONTHS_PRESENT",
    "SIEMBRA",
    "SOWN_MISSING_MONTH_COUNT",
    "SOWN_POSITIVE_MONTH_COUNT",
    "SOWN_DENOMINATOR_STATUS",
    "SOWN_SOURCE_12_MONTHS_PRESENT"
  ]
}
```

## Frozen Contract Checks
```json
{
  "aggregation_exact": true,
  "climate_families_exact": true,
  "cohort_ledger_primary_stage_b": true,
  "econometrics_blocked": true,
  "five_crop_codes_exact": true,
  "seven_window_ids_exact": true,
  "strict_layer_non_primary": true
}
```

## DIRECTOR TECHNICAL ADJUDICATION — B0.2
```json
{
  "contract": {
    "arrow_dtype_contract": {
      "by_artifact": {
        "perennial_exposures_long": {
          "COD_CULTIVO": "string",
          "CROP_STD": "string",
          "EXPOSURE_VALID": "bool",
          "FAILURE_REASON": "string",
          "RAIN_ANOM_MM": "float64",
          "RAIN_MM": "float64",
          "RAIN_Z": "float64",
          "REFERENCE_CALENDAR_YEAR": "int16",
          "REFERENCE_PERIOD_ID": "string",
          "TIME_BASIS": "string",
          "TMAX_ANOM_C": "float64",
          "TMAX_C": "float64",
          "TMAX_Z": "float64",
          "TMIN_ANOM_C": "float64",
          "TMIN_C": "float64",
          "TMIN_Z": "float64",
          "UBIGEO": "string",
          "WINDOW_ID": "string"
        },
        "phenology_exposures_long": {
          "COD_CULTIVO": "string",
          "CROP_STD": "string",
          "EXPOSURE_VALID": "bool",
          "FAILURE_REASON": "string",
          "RAIN_ANOM_MM": "float64",
          "RAIN_MM": "float64",
          "RAIN_Z": "float64",
          "REFERENCE_CALENDAR_YEAR": "int16",
          "REFERENCE_END_YEAR": "int16",
          "REFERENCE_PERIOD_ID": "string",
          "REFERENCE_START_YEAR": "int16",
          "TIME_BASIS": "string",
          "TMAX_ANOM_C": "float64",
          "TMAX_C": "float64",
          "TMAX_Z": "float64",
          "TMIN_ANOM_C": "float64",
          "TMIN_C": "float64",
          "TMIN_Z": "float64",
          "UBIGEO": "string",
          "WINDOW_ID": "string"
        },
        "transient_campaign_exposures_strict": {
          "AMBIGUOUS_COHORT_COUNT": "int16",
          "CAMPAIGN_END_YEAR": "int16",
          "CAMPAIGN_ID": "string",
          "CAMPAIGN_SIEMBRA_DENOMINATOR": "float64",
          "CAMPAIGN_START_YEAR": "int16",
          "CAMPAIGN_WEIGHTED_EXPOSURE_VALID": "bool",
          "COD_CULTIVO": "string",
          "COHORT_WEIGHT_SUM": "float64",
          "CROP_STD": "string",
          "EXPECTED_WEIGHT": "float64",
          "FAILURE_REASON": "string",
          "MISSING_WEIGHT": "float64",
          "RAIN_ANOM_MM": "float64",
          "RAIN_MM": "float64",
          "RAIN_Z": "float64",
          "SUPPORTED_WEIGHT": "float64",
          "TMAX_ANOM_C": "float64",
          "TMAX_C": "float64",
          "TMAX_Z": "float64",
          "TMIN_ANOM_C": "float64",
          "TMIN_C": "float64",
          "TMIN_Z": "float64",
          "UBIGEO": "string",
          "UNAMBIGUOUS_COHORT_COUNT": "int16",
          "WINDOW_ID": "string"
        },
        "transient_cohort_exposures": {
          "ANCHOR_DATE_MAX": "date32",
          "ANCHOR_DATE_MIN": "date32",
          "ANCHOR_MONTH": "int8",
          "ANCHOR_YEAR": "int16",
          "ANCHOR_YYYYMM": "int32",
          "ARCHITECTURE": "string",
          "ASSIGNED_CAMPAIGN_ID": "string",
          "ATTRIBUTION_L_MAX_DAYS": "int16",
          "ATTRIBUTION_L_MIN_DAYS": "int16",
          "CAMPAIGN_ATTRIBUTION_STATUS": "string",
          "CAMPAIGN_MAX": "string",
          "CAMPAIGN_MIN": "string",
          "CLIMATE_WINDOW_COMPLETE": "bool",
          "CLIMATE_WINDOW_END_YYYYMM": "int32",
          "CLIMATE_WINDOW_START_YYYYMM": "int32",
          "COD_CULTIVO": "string",
          "COHORT_EXPOSURE_VALID": "bool",
          "CROP_STD": "string",
          "EXPECTED_CLIMATE_MONTHS": "string",
          "FAILURE_REASON": "string",
          "HARVEST_DATE_MAX": "date32",
          "HARVEST_DATE_MIN": "date32",
          "RAIN_ANOM_MM": "float64",
          "RAIN_MM": "float64",
          "RAIN_Z": "float64",
          "SIEMBRA": "float64",
          "SIEMBRA_OBSERVED": "bool",
          "SUPPORTED_CLIMATE_MONTHS": "string",
          "TMAX_ANOM_C": "float64",
          "TMAX_C": "float64",
          "TMAX_Z": "float64",
          "TMIN_ANOM_C": "float64",
          "TMIN_C": "float64",
          "TMIN_Z": "float64",
          "UBIGEO": "string",
          "WINDOW_ID": "string"
        }
      },
      "by_type": {
        "bool": [
          "SIEMBRA_OBSERVED",
          "CLIMATE_WINDOW_COMPLETE",
          "COHORT_EXPOSURE_VALID",
          "CAMPAIGN_WEIGHTED_EXPOSURE_VALID",
          "EXPOSURE_VALID"
        ],
        "date32": [
          "ANCHOR_DATE_MIN",
          "ANCHOR_DATE_MAX",
          "HARVEST_DATE_MIN",
          "HARVEST_DATE_MAX"
        ],
        "float64": [
          "SIEMBRA",
          "RAIN_MM",
          "TMAX_C",
          "TMIN_C",
          "RAIN_ANOM_MM",
          "TMAX_ANOM_C",
          "TMIN_ANOM_C",
          "RAIN_Z",
          "TMAX_Z",
          "TMIN_Z",
          "CAMPAIGN_SIEMBRA_DENOMINATOR",
          "COHORT_WEIGHT_SUM",
          "EXPECTED_WEIGHT",
          "SUPPORTED_WEIGHT",
          "MISSING_WEIGHT"
        ],
        "int16": [
          "ANCHOR_YEAR",
          "CAMPAIGN_START_YEAR",
          "CAMPAIGN_END_YEAR",
          "REFERENCE_START_YEAR",
          "REFERENCE_END_YEAR",
          "REFERENCE_CALENDAR_YEAR",
          "ATTRIBUTION_L_MIN_DAYS",
          "ATTRIBUTION_L_MAX_DAYS",
          "UNAMBIGUOUS_COHORT_COUNT",
          "AMBIGUOUS_COHORT_COUNT"
        ],
        "int32": [
          "ANCHOR_YYYYMM",
          "CLIMATE_WINDOW_START_YYYYMM",
          "CLIMATE_WINDOW_END_YYYYMM"
        ],
        "int8": [
          "ANCHOR_MONTH"
        ],
        "string": [
          "UBIGEO",
          "COD_CULTIVO",
          "CROP_STD",
          "WINDOW_ID",
          "ARCHITECTURE",
          "CAMPAIGN_MIN",
          "CAMPAIGN_MAX",
          "CAMPAIGN_ATTRIBUTION_STATUS",
          "ASSIGNED_CAMPAIGN_ID",
          "CAMPAIGN_ID",
          "TIME_BASIS",
          "REFERENCE_PERIOD_ID",
          "FAILURE_REASON",
          "EXPECTED_CLIMATE_MONTHS",
          "SUPPORTED_CLIMATE_MONTHS"
        ]
      },
      "status": "DIRECTOR_APPROVED_B0_2"
    },
    "director_adjudication_status": "DIRECTOR_APPROVED_B0_2",
    "failure_reason_contract": {
      "ambiguous_cross_campaign_is_failure": false,
      "do_not_invent_additional_codes_without_director_reopening": true,
      "perennial_order": [
        "CLIMATE_WINDOW_OUTSIDE_AVAILABLE_RANGE",
        "CLIMATE_WINDOW_INTERNAL_GAP"
      ],
      "separator": "|",
      "status": "DIRECTOR_APPROVED_B0_2",
      "strict_campaign_order": [
        "STRUCTURAL_LEFT_TRUNCATION",
        "REQUIRED_U_SIEMBRA_NOT_OBSERVED",
        "REQUIRED_A_SIEMBRA_NOT_OBSERVED",
        "AMBIGUOUS_COHORT_SIEMBRA_NONZERO",
        "NO_POSITIVE_UNAMBIGUOUS_SIEMBRA",
        "POSITIVE_WEIGHT_COHORT_CLIMATE_INCOMPLETE",
        "WEIGHT_SUM_TOLERANCE_FAIL"
      ],
      "success": "NONE",
      "transient_cohort_order": [
        "CLIMATE_WINDOW_RIGHT_TRUNCATED",
        "CLIMATE_WINDOW_INTERNAL_GAP"
      ]
    },
    "incomplete_window_aggregation": {
      "if_supported_months_differ_from_expected": {
        "CLIMATE_WINDOW_COMPLETE": false,
        "COHORT_EXPOSURE_VALID": false,
        "all_nine_aggregated_climate_values": null
      },
      "no_partial_mean": true,
      "no_partial_sum": true,
      "no_renormalization": true,
      "partial_climate_aggregation_allowed": false
    },
    "month_list_representation": {
      "canonical_format": "YYYYMM|YYYYMM|YYYYMM",
      "rules": [
        "chronological ascending",
        "exactly six digits per month",
        "no spaces",
        "no trailing separator",
        "empty set = \"\"",
        "never JSON",
        "never Python repr",
        "never null merely because set is empty"
      ],
      "type": "UTF-8 string"
    },
    "right_edge_internal_gap_contract": {
      "expected_month_gt_2024_12": "CLIMATE_WINDOW_RIGHT_TRUNCATED",
      "expected_month_inside_coverage_but_key_or_value_unavailable": "CLIMATE_WINDOW_INTERNAL_GAP",
      "internal_gap_future_final_gate": "HOLD_OR_FAIL"
    },
    "transient_universe_contract": {
      "canonical_universe": "ALL_OBSERVED_TRANSIENT_TEMPORAL_SOURCE_ROWS",
      "do_not_densify_synthetic_months": true,
      "do_not_restrict_to_main_panel": true,
      "do_not_use_strict_required_slots_as_universe": true,
      "edge_support_2015_2024": "CONTEXT_EDGE_SUPPORT",
      "row_count": 8977,
      "source_boundary": "2015-08..2024-12"
    },
    "unified_long_contract": {
      "UNIFIED_LONG_BUILD": "HOLD",
      "do_not_aggregate_transient_cohorts_to_fit_unified_schema": true,
      "do_not_build_during_climate_exposure_master_v1": true,
      "do_not_modify_frozen_unified_schema": true
    },
    "zero_sowing_contract": {
      "no_dropping": true,
      "sowing_zero_semantics": "OBSERVED_ZERO_NOT_MISSING",
      "with_complete_climate_window": {
        "CLIMATE_WINDOW_COMPLETE": true,
        "COHORT_EXPOSURE_VALID": true,
        "FAILURE_REASON": "NONE",
        "SIEMBRA_OBSERVED": true
      }
    }
  },
  "status": "INCORPORATED"
}
```

## Director Decision Required Items
- NONE_REMAINING_FOR_B0_2_FREEZE_REVIEW

## Unified Long Build Status
```json
{
  "lossless_transform_defined": false,
  "status": "UNIFIED_LONG_BUILD = HOLD",
  "transient_columns_lost_by_reduction": [
    "ANCHOR_YEAR",
    "ANCHOR_MONTH",
    "ANCHOR_YYYYMM",
    "SIEMBRA",
    "CAMPAIGN_MIN",
    "CAMPAIGN_MAX",
    "CAMPAIGN_ATTRIBUTION_STATUS"
  ]
}
```
