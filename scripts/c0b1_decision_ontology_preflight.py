"""Preflight gates for C0B.1 decision-variable ontology.

The script is read-only. It validates the C0B.1 ontology package against the
committed C0B.0 checkpoint and refuses any scope expansion into optimization,
economic outcomes, scenarios, or frozen climate/phenology artifacts.
"""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_BRANCH = "phase/c0b-decision-feasibility-v1"
EXPECTED_HEAD = "77526c9cb41b20062a5fa61a95167af5859295f2"
EXPECTED_PARENT = "144cb679186b8fdfe5b821aad635a7f805b7de28"
EXPECTED_COMMIT_MESSAGE = "Checkpoint C0B decision feasibility reconnaissance"

ONTOLOGY_PATH = ROOT / "config/decision_ontology/decision_variable_ontology_v1.json"
ARCHITECTURE_PATH = ROOT / "outputs/decision_feasibility/C0B1_ARCHITECTURE_COMPARISON.csv"
REPORT_PATH = ROOT / "outputs/decision_feasibility/C0B1_DECISION_ONTOLOGY_REPORT.md"
SCRIPT_PATH = ROOT / "scripts/c0b1_decision_ontology_preflight.py"
TEST_PATH = ROOT / "tests/test_c0b1_decision_ontology.py"
ARCHITECTURE_COMPARISON_SHA256 = "314b6a5ef9305b4768a3beb996475c9a86c0365756908db7aada789dbe9508bb"

AUTHORIZED_SCOPE = {
    "config/decision_ontology/decision_variable_ontology_v1.json",
    "outputs/decision_feasibility/C0B1_ARCHITECTURE_COMPARISON.csv",
    "outputs/decision_feasibility/C0B1_DECISION_ONTOLOGY_REPORT.md",
    "scripts/c0b1_decision_ontology_preflight.py",
    "tests/test_c0b1_decision_ontology.py",
}

C0B0_HASHES = {
    "outputs/decision_feasibility/C0B_EVIDENCE_REGISTRY.csv": "d634b2ab95824cf25117d49a2f0443444fc1aa0fac4d08ad584fcd2dc15918d1",
    "outputs/decision_feasibility/C0B_CONSTRAINT_CANDIDATES.csv": "473563a6fafbdd907e572214ffdf4514e85edba62905454932ac064836d68447",
    "outputs/decision_feasibility/C0B_DECISION_FEASIBILITY_REPORT.md": "1bedb367e9632b317fd138c222b2be4f05f0162877b3c1005e8b923aadf54f13",
    "scripts/c0b_decision_feasibility_preflight.py": "7c277bbd627d02a8dbe6931df655e7cd13b52158997f44f507b41021edd0f2f4",
    "tests/test_c0b_decision_feasibility_preflight.py": "b03bbc12b322d86a097e6d2c9721fed6b24f5fa878cf18f0ed0d88c2fa8868fd",
}

ARCHITECTURE_SCHEMA = [
    "ARCHITECTURE_ID",
    "ARCHITECTURE_NAME",
    "TRANSIENT_ONTOLOGY",
    "PERENNIAL_ONTOLOGY",
    "TEMPORAL_RESOLUTION",
    "LAND_COMPATIBILITY",
    "PHENOLOGY_COMPATIBILITY",
    "WATER_COMPATIBILITY",
    "PERENNIAL_STOCK_REQUIREMENT",
    "ADJUSTMENT_REQUIREMENT",
    "DATA_REQUIREMENT_LEVEL",
    "GOVERNANCE_COMPATIBILITY",
    "MAJOR_ADVANTAGE",
    "FATAL_WEAKNESS",
    "VERDICT",
    "RATIONALE",
]

EXPECTED_ARCHITECTURES = {"ARCH_A", "ARCH_B", "ARCH_C", "ARCH_D", "ARCH_E", "ARCH_F"}
ALLOWED_ARCHITECTURE_VERDICTS = {
    "PRIMARY_CANDIDATE",
    "CONDITIONAL_CANDIDATE",
    "FALLBACK_CANDIDATE",
    "REJECT",
    "UNRESOLVED",
}
ALLOWED_LAND_ROLES = {
    "HARD_CAP_COMPATIBLE_AFTER_OCCUPANCY_MAPPING",
    "HARD_CAP_COMPATIBLE_FOR_STOCK_ONLY",
    "SOFT_REFERENCE_ONLY",
    "NOT_USABLE",
    "UNRESOLVED",
}
ALLOWED_ENDOGENEITY_VERDICTS = {
    "SUPPORTED_IN_PRINCIPLE",
    "CONDITIONAL_ON_C0B3",
    "FALLBACK_ONLY",
    "REJECT",
}
REQUIRED_REPORT_HEADINGS = [
    "## 1. Executive verdict",
    "## 2. Why the ontology gate was necessary",
    "## 3. Physical land ontology",
    "## 4. Transient crop ontology",
    "## 5. Perennial/semipermanent crop ontology",
    "## 6. Architecture A adjudication",
    "## 7. Architecture B adjudication",
    "## 8. Architecture C adjudication",
    "## 9. Architecture D adjudication",
    "## 10. Architecture E adjudication",
    "## 11. Architecture F adjudication",
    "## 12. Transient temporal-resolution adjudication",
    "## 13. Perennial temporal-resolution adjudication",
    "## 14. Sequential/multiple cropping assessment",
    "## 15. Phenology compatibility",
    "## 16. Land-footprint compatibility",
    "## 17. Multiscale water compatibility",
    "## 18. Governance semantics",
    "## 19. Endogeneity-set adjudication",
    "## 20. Primary architecture",
    "## 21. Fallback architecture",
    "## 22. Remaining blockers",
    "## 23. Exact requirements for next gate",
    "## 24. Forbidden interpretations",
    "## 25. Final verdict",
]

FORBIDDEN_NEW_PATH_PARTS = {
    "config/optimization",
    "data/processed/decision",
    "outputs/optimization",
    "outputs/scenario",
    "scripts/optimize",
    "tests/test_optimizer",
}
FROZEN_PATH_PREFIXES = (
    "data/processed/phenology/",
    "outputs/phenology/",
    "config/phenology/",
    "config/climate_exposure/",
    "outputs/climate_exposure/",
)
FORBIDDEN_PARAMETER_KEYS = {
    "delta_a",
    "delta_p",
    "objective",
    "objective_function",
    "cvar",
    "cvar_alpha",
    "risk_aversion",
    "price",
    "profit",
    "gvp",
    "return",
    "water_coefficient",
    "yield",
    "p_value",
    "regression_coefficient",
}

PRIMARY_T3_RESOLUTION = "T3_CAMPAIGN_TOTAL_DECISION_WITH_FUTURE_PRESPECIFIED_EXOGENOUS_WITHIN_CAMPAIGN_SHARES"
LEGACY_T3_RESOLUTION = "T3_CAMPAIGN_TOTAL_DECISION_WITH_FROZEN_WITHIN_CAMPAIGN_SHARES"
EXPECTED_STAGE_B_KNOWN_FAILURES = [
    "tests/test_climate_exposure_b0_preflight.py::test_02_base_commit_and_tag",
    "tests/test_climate_exposure_b0_preflight.py::test_03_no_forbidden_exposure_output_exists",
    "tests/test_climate_exposure_b0_preflight.py::test_16_no_stage_b_parquet_output_has_been_built",
    "tests/test_perennial_exposures.py::test_12_forbidden_artifacts_absent",
    "tests/test_transient_cohort_exposures.py::test_16_forbidden_artifacts_absent",
]
EXPECTED_C0B0_POST_CHECKPOINT_FAILURES = [
    "tests/test_c0b_decision_feasibility_preflight.py::test_02_exact_frozen_base",
    "tests/test_c0b_decision_feasibility_preflight.py::test_03_exact_five_file_scope",
    "tests/test_c0b_decision_feasibility_preflight.py::test_21_preflight_script_passes",
]
EXPECTED_T3_FORBIDDEN_SHARE_SELECTION_INPUTS = {
    "OUTCOME_VARIABLES",
    "CLIMATE_RESPONSE_ESTIMATES",
    "WEATHER_YIELD_RESPONSE_ESTIMATES",
    "ECONOMETRIC_SIGNIFICANCE",
    "ENSO_SCENARIO_OUTCOMES",
    "ECONOMIC_OPTIMIZATION_RESULTS",
    "YIELD_IMPROVEMENT",
    "ROBUSTNESS_IMPROVEMENT",
    "CVAR_IMPROVEMENT",
    "PROFIT_IMPROVEMENT",
    "GVP_IMPROVEMENT",
    "MODEL_FIT_IMPROVEMENT",
}
C0A_PATHS = {
    "outputs/outcome/C0A_EVIDENCE_REGISTRY.csv",
    "outputs/outcome/C0A_OUTCOME_EVIDENCE_REPORT.md",
    "scripts/c0a_outcome_evidence_preflight.py",
    "tests/test_c0a_outcome_evidence_preflight.py",
}


def _run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return result.stdout.strip()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _load_ontology() -> dict[str, Any]:
    return json.loads(ONTOLOGY_PATH.read_text(encoding="utf-8"))


def _flatten_keys(value: Any) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        for key, nested in value.items():
            keys.add(str(key).lower())
            keys.update(_flatten_keys(nested))
    elif isinstance(value, list):
        for item in value:
            keys.update(_flatten_keys(item))
    return keys


def _numeric_share_fields(value: Any, path: str = "") -> list[str]:
    offenders: list[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            nested_path = f"{path}.{key}" if path else str(key)
            offenders.extend(_numeric_share_fields(nested, nested_path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            offenders.extend(_numeric_share_fields(item, f"{path}[{index}]"))
    elif "share" in path.lower() and isinstance(value, (int, float)) and not isinstance(value, bool):
        offenders.append(path)
    return offenders


def _numeric_fields_matching(value: Any, patterns: tuple[str, ...], path: str = "") -> list[str]:
    offenders: list[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            nested_path = f"{path}.{key}" if path else str(key)
            offenders.extend(_numeric_fields_matching(nested, patterns, nested_path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            offenders.extend(_numeric_fields_matching(item, patterns, f"{path}[{index}]"))
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        lowered = path.lower()
        if any(pattern in lowered for pattern in patterns):
            offenders.append(path)
    return offenders


def repository_identity() -> dict[str, str]:
    return {
        "branch": _run_git(["branch", "--show-current"]),
        "head": _run_git(["rev-parse", "HEAD"]),
        "parent": _run_git(["rev-parse", "HEAD^"]),
        "message": _run_git(["log", "-1", "--pretty=%B"]),
    }


def checkpoint_parentage() -> dict[str, object]:
    identity = repository_identity()
    failures = [
        key
        for key, expected in {
            "branch": EXPECTED_BRANCH,
            "head": EXPECTED_HEAD,
            "parent": EXPECTED_PARENT,
            "message": EXPECTED_COMMIT_MESSAGE,
        }.items()
        if identity[key] != expected
    ]
    return {"status": "PASS" if not failures else "FAIL", "identity": identity, "failures": failures}


def persistent_scope() -> dict[str, object]:
    output = _run_git(["status", "--short", "--untracked-files=all"])
    observed: set[str] = set()
    modified_c0b0: list[str] = []
    for line in output.splitlines():
        if not line:
            continue
        status = line[:2]
        path = line[3:].replace("\\", "/")
        if path in C0B0_HASHES and status.strip():
            modified_c0b0.append(path)
        if path in AUTHORIZED_SCOPE:
            observed.add(path)
        else:
            return {"status": "FAIL", "observed": sorted(observed), "unexpected": path, "raw": output}
    status = "PASS" if observed == AUTHORIZED_SCOPE and not modified_c0b0 else "FAIL"
    return {"status": status, "observed": sorted(observed), "modified_c0b0": modified_c0b0, "raw": output}


def c0b0_immutability() -> dict[str, object]:
    observed = {}
    failures = []
    for relpath, expected_hash in C0B0_HASHES.items():
        digest = _sha256(ROOT / relpath)
        observed[relpath] = digest
        if digest != expected_hash:
            failures.append(relpath)
    return {"status": "PASS" if not failures else "FAIL", "hashes": observed, "failures": failures}


def architecture_csv_gate() -> dict[str, object]:
    rows = _read_csv(ARCHITECTURE_PATH)
    schema = list(rows[0].keys()) if rows else []
    ids = {row["ARCHITECTURE_ID"] for row in rows}
    verdicts = [row["VERDICT"] for row in rows]
    failures = []
    if schema != ARCHITECTURE_SCHEMA:
        failures.append("SCHEMA")
    if ids != EXPECTED_ARCHITECTURES:
        failures.append("ARCHITECTURE_IDS")
    if any(verdict not in ALLOWED_ARCHITECTURE_VERDICTS for verdict in verdicts):
        failures.append("VERDICT_VOCAB")
    if verdicts.count("PRIMARY_CANDIDATE") != 1:
        failures.append("PRIMARY_COUNT")
    if verdicts.count("FALLBACK_CANDIDATE") > 2:
        failures.append("FALLBACK_COUNT")
    arch_a = next((row for row in rows if row["ARCHITECTURE_ID"] == "ARCH_A"), {})
    arch_e = next((row for row in rows if row["ARCHITECTURE_ID"] == "ARCH_E"), {})
    arch_f = next((row for row in rows if row["ARCHITECTURE_ID"] == "ARCH_F"), {})
    if arch_a.get("VERDICT") == "PRIMARY_CANDIDATE":
        failures.append("ARCH_A_PRIMARY")
    if arch_e.get("VERDICT") != "PRIMARY_CANDIDATE":
        failures.append("ARCH_E_NOT_PRIMARY")
    if arch_f.get("VERDICT") != "FALLBACK_CANDIDATE":
        failures.append("ARCH_F_NOT_FALLBACK")
    if _sha256(ARCHITECTURE_PATH) != ARCHITECTURE_COMPARISON_SHA256:
        failures.append("ARCHITECTURE_HASH")
    return {"status": "PASS" if not failures else "FAIL", "failures": failures, "rows": rows}


def ontology_gate() -> dict[str, object]:
    ontology = _load_ontology()
    failures = []
    required_keys = {
        "ontology_version",
        "planning_interpretation",
        "target_crops",
        "primary_architecture",
        "fallback_architectures",
        "rejected_architectures",
        "architecture_verdicts",
        "planning_horizon_interpretation",
        "transient_crops",
        "perennial_or_semipermanent_crops",
        "transient_decision_resolutions",
        "primary_transient_decision_resolution",
        "fallback_transient_decision_resolution",
        "primary_transient_resolution",
        "fallback_transient_resolution",
        "primary_transient_resolution_status",
        "t3_numeric_shares_defined",
        "t3_share_parameterization_status",
        "t3_share_provenance_rule_status",
        "t3_forbidden_share_selection_inputs",
        "planting_timing_adaptation_status",
        "primary_architecture_operational_authorization",
        "perennial_resolutions",
        "primary_perennial_resolution",
        "p2_status",
        "p3_fallback_status",
        "perennial_stock_state_definitions",
        "perennial_installed_stock_status",
        "perennial_productive_stock_distinction_status",
        "new_establishment_immediate_productivity_assumption",
        "immediate_productivity_assumption",
        "establishment_to_productivity_lag_status",
        "perennial_removal_replacement_timing_status",
        "numeric_maturity_parameters_created",
        "productive_age_distribution_status",
        "yield_age_relationship_status",
        "arch_e_to_arch_f_fallback_if_c0b3_fails",
        "c0b3_perennial_productivity_adjudication",
        "physical_land_interpretation",
        "AREA_HA_future_role",
        "climate_response_window_role",
        "climate_response_window_definition",
        "physical_land_occupancy_window_definition",
        "climate_response_window_is_physical_occupancy_window",
        "physical_land_occupancy_mapping_status",
        "physical_land_occupancy_evidence_status",
        "occupancy_mapping_may_reuse_climate_windows_without_independent_support",
        "occupancy_numeric_parameters_created",
        "occupancy_coefficient_status",
        "land_hard_constraint_currently_authorized",
        "land_ontology",
        "sequential_cropping_assumption",
        "stock_flow_distinction",
        "phenology_compatibility",
        "multiscale_water_compatibility",
        "governance_interpretation",
        "parcel_level_interpretation",
        "endogeneity_sets",
        "primary_endogeneity_set",
        "fallback_endogeneity_set",
        "endogeneity_set_primary",
        "endogeneity_set_fallback",
        "decision_spatial_scale",
        "constraint_multiscale_allowed",
        "future_evidence_requirements",
        "required_future_evidence",
        "numeric_parameter_policy",
        "forbidden_interpretations",
        "climate_stage_b_preservation",
        "fatal_gaps",
        "critical_gaps",
        "known_lifecycle_failure_ledger",
        "raw_full_suite_status",
        "adjudicated_validation_status",
        "phase_aware_validator_future_need",
        "next_gate_recommendation",
        "C0B1_status",
    }
    if not required_keys <= set(ontology):
        failures.append("REQUIRED_KEYS")
    if ontology.get("primary_architecture") != "ARCH_E_MIXED_STOCK_FLOW_PLUS_MARGINAL_ADJUSTMENT":
        failures.append("PRIMARY_ARCHITECTURE")
    if ontology.get("fallback_architectures") != ["ARCH_F_TRANSIENT_ENDOGENOUS_PERENNIAL_EXOGENOUS"]:
        failures.append("FALLBACK_ARCHITECTURES")
    if ontology.get("primary_transient_resolution") != PRIMARY_T3_RESOLUTION:
        failures.append("PRIMARY_T3_RESOLUTION")
    if LEGACY_T3_RESOLUTION in json.dumps(ontology, sort_keys=True):
        failures.append("LEGACY_T3_LABEL_PRESENT")
    land = ontology.get("land_ontology", {})
    if set(ontology.get("rejected_architectures", [])) != {
        "ARCH_A_HOMOGENEOUS_STATIC_AREA",
        "ARCH_B_CAMPAIGN_FLOW_FOR_ALL",
        "ARCH_C_PHYSICAL_STOCK_FOR_ALL",
    }:
        failures.append("REJECTED_ARCHITECTURES")
    if ontology.get("primary_transient_resolution") != ontology.get("primary_transient_decision_resolution"):
        failures.append("PRIMARY_TRANSIENT_ALIAS")
    if ontology.get("fallback_transient_resolution") != ontology.get("fallback_transient_decision_resolution"):
        failures.append("FALLBACK_TRANSIENT_ALIAS")
    if ontology.get("AREA_HA_future_role") != land.get("AREA_HA_future_role"):
        failures.append("AREA_HA_ALIAS")
    if ontology.get("endogeneity_set_primary") != ontology.get("primary_endogeneity_set"):
        failures.append("PRIMARY_ENDOGENEITY_ALIAS")
    if ontology.get("endogeneity_set_fallback") != ontology.get("fallback_endogeneity_set"):
        failures.append("FALLBACK_ENDOGENEITY_ALIAS")
    if ontology.get("constraint_multiscale_allowed") is not True:
        failures.append("CONSTRAINT_MULTISCALE_ALLOWED")
    if land.get("AREA_HA_future_role") not in ALLOWED_LAND_ROLES:
        failures.append("AREA_HA_ROLE_VOCAB")
    if land.get("direct_campaign_hectare_cap_authorized") is not False:
        failures.append("DIRECT_AREA_CAP_AUTHORIZED")
    if ontology.get("sequential_cropping_assumption") != "NOT_ASSUMED_ABSENT_AGGREGATE_DATA_CANNOT_PROVE_PARCEL_SEQUENCE":
        failures.append("SEQUENTIAL_CROPPING_ASSUMPTION")
    if ontology.get("stock_flow_distinction", {}).get("same_unit_label_not_same_decision_object") is not True:
        failures.append("STOCK_FLOW_DISTINCTION")
    if ontology.get("phenology_compatibility", {}).get("status") != "COMPATIBLE_WITH_FROZEN_STAGE_B_NO_REOPEN":
        failures.append("PHENOLOGY_COMPATIBILITY")
    if ontology.get("multiscale_water_compatibility", {}).get("district_hard_water_cap_authorized") is not False:
        failures.append("DISTRICT_WATER_CAP_AUTHORIZED")
    if ontology.get("multiscale_water_compatibility", {}).get("water_coefficient_authorized") is not False:
        failures.append("WATER_COEFFICIENT_AUTHORIZED")
    if "NORMATIVE_REGIONAL_DECISION_SUPPORT" not in ontology.get("governance_interpretation", ""):
        failures.append("GOVERNANCE_INTERPRETATION")
    if not ontology.get("parcel_level_interpretation", "").startswith("FORBIDDEN"):
        failures.append("PARCEL_INTERPRETATION")
    endogeneity = ontology.get("endogeneity_sets", {})
    for key, item in endogeneity.items():
        if item.get("verdict") not in ALLOWED_ENDOGENEITY_VERDICTS:
            failures.append(f"ENDOGENEITY_VERDICT_{key}")
    if ontology.get("primary_endogeneity_set") != "SET_2_RICE_MAIZE_FULLY_ENDOGENOUS_PERENNIALS_MARGINALLY_ENDOGENOUS":
        failures.append("PRIMARY_ENDOGENEITY_SET")
    if ontology.get("fallback_endogeneity_set") != "SET_3_RICE_MAIZE_ENDOGENOUS_PERENNIAL_STOCKS_EXOGENOUS":
        failures.append("FALLBACK_ENDOGENEITY_SET")
    if ontology.get("C0B1_status") != "PASS_ONTOLOGY_MASTER":
        failures.append("C0B1_STATUS")
    if ontology.get("phase_aware_validator_future_need") != "RECOMMENDED_BEFORE_FINAL_REPRODUCIBILITY_FREEZE":
        failures.append("PHASE_AWARE_VALIDATOR_FUTURE_NEED")
    return {"status": "PASS" if not failures else "FAIL", "failures": failures, "ontology": ontology}


def climate_occupancy_gate() -> dict[str, object]:
    ontology = _load_ontology()
    failures = []
    if ontology.get("climate_response_window_role") != "EMPIRICAL_CLIMATE_EXPOSURE_ONLY":
        failures.append("CLIMATE_RESPONSE_WINDOW_ROLE")
    if ontology.get("climate_response_window_is_physical_occupancy_window") is not False:
        failures.append("CLIMATE_WINDOW_IS_OCCUPANCY_WINDOW")
    if ontology.get("physical_land_occupancy_mapping_status") != "REQUIRED_BEFORE_LAND_HARD_CAP":
        failures.append("PHYSICAL_OCCUPANCY_MAPPING_STATUS")
    if ontology.get("physical_land_occupancy_evidence_status") != "NOT_YET_ADJUDICATED":
        failures.append("PHYSICAL_OCCUPANCY_EVIDENCE_STATUS")
    if ontology.get("occupancy_mapping_may_reuse_climate_windows_without_independent_support") is not False:
        failures.append("CLIMATE_WINDOW_REUSE_WITHOUT_SUPPORT")
    if ontology.get("occupancy_numeric_parameters_created") is not False:
        failures.append("OCCUPANCY_NUMERIC_PARAMETERS_CREATED")
    if ontology.get("occupancy_coefficient_status") != "NOT_CREATED_IN_C0B1":
        failures.append("OCCUPANCY_COEFFICIENT_STATUS")
    numeric_occupancy = _numeric_fields_matching(ontology, ("occupancy", "duration"))
    if numeric_occupancy:
        failures.append("NUMERIC_OCCUPANCY_FIELD")
    evidence = " ".join(ontology.get("future_evidence_requirements", {}).get("numeric_parameter_required_future_evidence", []))
    if "climate response window" not in evidence.lower() or "physical occupancy coefficient" not in evidence.lower():
        failures.append("CLIMATE_WINDOW_NOT_OCCUPANCY_EVIDENCE")
    report = REPORT_PATH.read_text(encoding="utf-8")
    required = [
        "CLIMATE_RESPONSE_WINDOW != PHYSICAL_LAND_OCCUPANCY_WINDOW",
        "Frozen Stage-A and Stage-B climate exposure windows do not define physical occupancy duration.",
        "No occupancy duration or occupancy coefficient is created in C0B1.",
    ]
    for phrase in required:
        if phrase not in report:
            failures.append(f"REPORT_PHRASE:{phrase}")
    return {"status": "PASS" if not failures else "FAIL", "failures": failures, "numeric_occupancy": numeric_occupancy}


def perennial_stock_gate() -> dict[str, object]:
    ontology = _load_ontology()
    failures = []
    definitions = ontology.get("perennial_stock_state_definitions", {})
    required_definitions = {
        "INSTALLED_PERENNIAL_STOCK",
        "PRODUCTIVE_OR_BEARING_PERENNIAL_STOCK",
        "NEW_ESTABLISHMENT_FLOW",
        "REMOVAL_OR_REPLACEMENT_FLOW",
    }
    if not required_definitions <= set(definitions):
        failures.append("PERENNIAL_STOCK_DEFINITIONS")
    if ontology.get("perennial_installed_stock_status") != "REQUIRES_C0B3_NUMERIC_EVIDENCE":
        failures.append("PERENNIAL_INSTALLED_STOCK_STATUS")
    if ontology.get("perennial_productive_stock_distinction_status") != "REQUIRES_C0B3_ADJUDICATION":
        failures.append("PERENNIAL_PRODUCTIVE_STOCK_DISTINCTION_STATUS")
    if ontology.get("new_establishment_immediate_productivity_assumption") != "NOT_AUTHORIZED":
        failures.append("NEW_ESTABLISHMENT_IMMEDIATE_PRODUCTIVITY")
    if ontology.get("immediate_productivity_assumption") != "NOT_AUTHORIZED_WITHOUT_C0B3_EVIDENCE":
        failures.append("IMMEDIATE_PRODUCTIVITY_ASSUMPTION")
    if ontology.get("establishment_to_productivity_lag_status") != "UNRESOLVED_REQUIRES_C0B3":
        failures.append("ESTABLISHMENT_TO_PRODUCTIVITY_LAG_STATUS")
    if ontology.get("perennial_removal_replacement_timing_status") != "UNRESOLVED_REQUIRES_C0B3":
        failures.append("PERENNIAL_REMOVAL_REPLACEMENT_TIMING_STATUS")
    if ontology.get("numeric_maturity_parameters_created") is not False:
        failures.append("NUMERIC_MATURITY_PARAMETERS_CREATED")
    if ontology.get("productive_age_distribution_status") != "NOT_CREATED_IN_C0B1":
        failures.append("PRODUCTIVE_AGE_DISTRIBUTION_STATUS")
    if ontology.get("yield_age_relationship_status") != "NOT_CREATED_IN_C0B1":
        failures.append("YIELD_AGE_RELATIONSHIP_STATUS")
    if ontology.get("arch_e_to_arch_f_fallback_if_c0b3_fails") != "AUTHORIZED_SCOPE_REDUCTION_PATH":
        failures.append("ARCH_E_TO_ARCH_F_FALLBACK")
    c0b3 = ontology.get("c0b3_perennial_productivity_adjudication", {})
    expected_topics = {
        "INSTALLED_STOCK_ONLY",
        "INSTALLED_VERSUS_PRODUCTIVE_OR_BEARING_STOCK_DISTINCTION",
        "ESTABLISHMENT_TO_PRODUCTIVITY_LAG",
        "REMOVAL_OR_REPLACEMENT_TIMING",
        "PRODUCTIVE_AGE_OR_LIFECYCLE_INFORMATION",
    }
    for crop in ("MANGO", "LEMON", "BANANA"):
        if not expected_topics <= set(c0b3.get(crop, [])):
            failures.append(f"C0B3_{crop}_TOPICS")
    if c0b3.get("c0b1d_prespecifies_answers") is not False:
        failures.append("C0B1D_PRESPECIFIES_C0B3_ANSWERS")
    numeric_maturity = _numeric_fields_matching(ontology, ("maturity", "lag", "productive_age", "yield_age"))
    if numeric_maturity:
        failures.append("NUMERIC_MATURITY_FIELD")
    report = REPORT_PATH.read_text(encoding="utf-8")
    required = [
        "### Installed versus productive perennial stock",
        "`NEW_ESTABLISHMENT_FLOW` does not automatically imply `IMMEDIATE_PRODUCTIVE_OR_BEARING_STOCK`.",
        "C0B3 must adjudicate separately for mango, lemon, and banana",
    ]
    for phrase in required:
        if phrase not in report:
            failures.append(f"REPORT_PHRASE:{phrase}")
    return {"status": "PASS" if not failures else "FAIL", "failures": failures, "numeric_maturity": numeric_maturity}


def t3_provenance_gate() -> dict[str, object]:
    ontology = _load_ontology()
    failures = []
    if ontology.get("primary_transient_resolution") != PRIMARY_T3_RESOLUTION:
        failures.append("PRIMARY_TRANSIENT_RESOLUTION")
    if ontology.get("primary_transient_decision_resolution") != PRIMARY_T3_RESOLUTION:
        failures.append("PRIMARY_TRANSIENT_DECISION_RESOLUTION")
    if ontology.get("primary_transient_resolution_status") != "CONDITIONAL_PRIMARY":
        failures.append("PRIMARY_TRANSIENT_RESOLUTION_STATUS")
    if ontology.get("t3_numeric_shares_defined") is not False:
        failures.append("T3_NUMERIC_SHARES_DEFINED")
    if ontology.get("t3_share_parameterization_status") != "NOT_YET_DEFINED":
        failures.append("T3_PARAMETERIZATION_STATUS")
    if ontology.get("t3_share_provenance_rule_status") != "REQUIRED_BEFORE_NUMERICAL_IMPLEMENTATION":
        failures.append("T3_PROVENANCE_RULE_STATUS")
    if ontology.get("planting_timing_adaptation_status") != "SENSITIVITY_CANDIDATE_OR_FUTURE_EXTENSION":
        failures.append("PLANTING_TIMING_ADAPTATION_STATUS")
    forbidden_inputs = set(ontology.get("t3_forbidden_share_selection_inputs", []))
    if not EXPECTED_T3_FORBIDDEN_SHARE_SELECTION_INPUTS <= forbidden_inputs:
        failures.append("T3_FORBIDDEN_SHARE_SELECTION_INPUTS")
    requirements = set(ontology.get("t3_future_share_rule_requirements", []))
    if "PRESPECIFIED_BEFORE_DOWNSTREAM_OUTCOME_ANALYSIS" not in requirements:
        failures.append("T3_PRESPECIFIED_RULE")
    if "DOCUMENTED_PROVENANCE_BEFORE_NUMERICAL_IMPLEMENTATION" not in requirements:
        failures.append("T3_DOCUMENTED_PROVENANCE")
    admissible = set(ontology.get("t3_admissible_future_share_evidence_classes_not_selected_in_c0b1", []))
    expected_admissible = {
        "SOURCE_OBSERVED_HISTORICAL_SIEMBRA_TIMING",
        "FROZEN_STAGE_B_COHORT_STRUCTURE",
        "OFFICIAL_AGRICULTURAL_CALENDAR_RULES",
    }
    if not expected_admissible <= admissible:
        failures.append("T3_ADMISSIBLE_CLASSES")
    numeric_share_fields = _numeric_share_fields(ontology)
    if numeric_share_fields:
        failures.append("T3_NUMERIC_SHARE_PAYLOAD")
    if "frozen within-campaign" in json.dumps(ontology, sort_keys=True).lower():
        failures.append("AMBIGUOUS_FROZEN_SHARE_PHRASE")
    return {
        "status": "PASS" if not failures else "FAIL",
        "failures": failures,
        "numeric_share_fields": numeric_share_fields,
    }


def operational_authorization_gate() -> dict[str, object]:
    ontology = _load_ontology()
    failures = []
    if ontology.get("primary_architecture_operational_authorization") != "BLOCKED_PENDING_C0B2_C0B3_AND_PARAMETER_GATES":
        failures.append("PRIMARY_ARCHITECTURE_OPERATIONAL_AUTHORIZATION")
    if ontology.get("land_hard_constraint_currently_authorized") is not False:
        failures.append("LAND_HARD_CONSTRAINT_CURRENTLY_AUTHORIZED")
    if ontology.get("land_ontology", {}).get("direct_campaign_hectare_cap_authorized") is not False:
        failures.append("DIRECT_CAMPAIGN_HECTARE_CAP_AUTHORIZED")
    if ontology.get("p2_status") != "CONDITIONAL_ON_C0B3":
        failures.append("P2_STATUS")
    if ontology.get("p3_fallback_status") != "EXPLICIT_FALLBACK_IF_C0B3_FAILS":
        failures.append("P3_FALLBACK_STATUS")
    return {"status": "PASS" if not failures else "FAIL", "failures": failures}


def lifecycle_failure_ledger_gate() -> dict[str, object]:
    ontology = _load_ontology()
    ledger = ontology.get("known_lifecycle_failure_ledger", {})
    failures = []
    stage_b = ledger.get("stage_b_known_state_failures", [])
    c0b0 = ledger.get("c0b0_expected_post_checkpoint_failures", [])
    stage_b_tests = [item.get("test") for item in stage_b]
    c0b0_tests = [item.get("test") for item in c0b0]
    if stage_b_tests != EXPECTED_STAGE_B_KNOWN_FAILURES:
        failures.append("STAGE_B_FAILURE_LIST")
    if c0b0_tests != EXPECTED_C0B0_POST_CHECKPOINT_FAILURES:
        failures.append("C0B0_FAILURE_LIST")
    if any(item.get("classification") != "KNOWN_STAGE_B_HISTORICAL_STATE_FAILURE" for item in stage_b):
        failures.append("STAGE_B_CLASSIFICATION")
    if any(item.get("classification") != "EXPECTED_POST_CHECKPOINT_STATE_FAILURE" for item in c0b0):
        failures.append("C0B0_CLASSIFICATION")
    if ledger.get("checkpoint_descendant") != EXPECTED_HEAD:
        failures.append("CHECKPOINT_DESCENDANT")
    if ledger.get("total_known_state_failures") != 8:
        failures.append("TOTAL_KNOWN_STATE_FAILURES")
    if ledger.get("stage_b_known_state_failure_count") != 5:
        failures.append("STAGE_B_FAILURE_COUNT")
    if ledger.get("c0b0_expected_post_checkpoint_failure_count") != 3:
        failures.append("C0B0_FAILURE_COUNT")
    if ledger.get("genuine_regression_count") != 0:
        failures.append("GENUINE_REGRESSION_COUNT")
    if ledger.get("unknown_failure_count") != 0:
        failures.append("UNKNOWN_FAILURE_COUNT")
    if ontology.get("raw_full_suite_status") != "FAIL_WITH_8_KNOWN_STATE_FAILURES":
        failures.append("RAW_FULL_SUITE_STATUS")
    if ontology.get("adjudicated_validation_status") != "PASS_WITH_ZERO_GENUINE_REGRESSIONS":
        failures.append("ADJUDICATED_VALIDATION_STATUS")
    policy = ledger.get("unknown_failure_policy", "")
    if "ANY_DIFFERENT_OR_NINTH_FAILURE_IS_UNEXPECTED_FAILURE" not in policy:
        failures.append("UNKNOWN_FAILURE_POLICY")
    conditions = set(ledger.get("tolerance_conditions", []))
    expected_conditions = {
        "C0B0_CHECKPOINT_FILES_BYTE_IDENTICAL",
        "CHECKPOINT_77526C9CB41B20062A5FA61A95167AF5859295F2_REMAINS_ANCESTOR",
        "NO_GENUINE_SCIENTIFIC_REGRESSION",
        "NO_UNKNOWN_FAILURES",
    }
    if not expected_conditions <= conditions:
        failures.append("TOLERANCE_CONDITIONS")
    return {"status": "PASS" if not failures else "FAIL", "failures": failures}


def numeric_parameter_gate() -> dict[str, object]:
    keys = _flatten_keys(_load_ontology())
    forbidden = sorted(key for key in keys if key in FORBIDDEN_PARAMETER_KEYS)
    return {"status": "PASS" if not forbidden else "FAIL", "forbidden_keys": forbidden}


def report_gate() -> dict[str, object]:
    text = REPORT_PATH.read_text(encoding="utf-8")
    failures = []
    for heading in REQUIRED_REPORT_HEADINGS:
        if heading not in text:
            failures.append(heading)
    if len([line for line in text.splitlines() if line.startswith("## ")]) != 25:
        failures.append("REPORT_HEADING_COUNT")
    required_phrases = [
        "Direct `SUM campaign hectares <= AREA_HA` is not authorized.",
        "Sequential or multiple cropping cannot be assumed absent.",
        "Parcel-level interpretation is forbidden.",
        "No numeric optimization parameters are authorized in C0B1.",
        "`C0B1_STATUS=PASS_ONTOLOGY_MASTER`",
        "The next gate is `C0B2_SPATIAL_HYDRAULIC_AND_AGENCY_CROSSWALK_GATE`.",
        "### T3 parameterization status",
        "### Lifecycle-state test adjudication",
        "### Climate-response windows versus physical land occupancy",
        "### Installed versus productive perennial stock",
        "C0B1 defines ontology.",
        "Raw full suite status is `FAIL_WITH_8_KNOWN_STATE_FAILURES`",
        "adjudicated validation status is `PASS_WITH_ZERO_GENUINE_REGRESSIONS`",
        "Any different or ninth full-suite failure is an `UNEXPECTED_FAILURE`",
    ]
    for phrase in required_phrases:
        if phrase not in text:
            failures.append(f"PHRASE:{phrase}")
    return {"status": "PASS" if not failures else "FAIL", "failures": failures}


def frozen_paths_gate() -> dict[str, object]:
    changed = _run_git(["diff", "--name-only"]).splitlines()
    staged = _run_git(["diff", "--cached", "--name-only"]).splitlines()
    all_changed = [path.replace("\\", "/") for path in changed + staged]
    frozen = [path for path in all_changed if path.startswith(FROZEN_PATH_PREFIXES)]
    return {"status": "PASS" if not frozen else "FAIL", "changed_frozen_paths": frozen}


def no_optimization_artifacts() -> dict[str, object]:
    tracked = _run_git(["ls-files"]).splitlines()
    status = _run_git(["status", "--short", "--untracked-files=all"]).splitlines()
    status_paths = [line[3:].replace("\\", "/") for line in status if line]
    paths = [path.replace("\\", "/") for path in tracked + status_paths]
    forbidden_paths = []
    for path in paths:
        lowered = path.lower()
        if path in AUTHORIZED_SCOPE:
            continue
        if any(part in lowered for part in FORBIDDEN_NEW_PATH_PARTS):
            forbidden_paths.append(path)
    return {"status": "PASS" if not forbidden_paths else "FAIL", "forbidden_paths": sorted(set(forbidden_paths))}


def no_c0a_contamination() -> dict[str, object]:
    existing = [path for path in C0A_PATHS if (ROOT / path).exists()]
    return {"status": "PASS" if not existing else "FAIL", "existing": existing}


def run_all_gates() -> dict[str, dict[str, object]]:
    return {
        "checkpoint_parentage": checkpoint_parentage(),
        "persistent_scope": persistent_scope(),
        "c0b0_immutability": c0b0_immutability(),
        "architecture_csv": architecture_csv_gate(),
        "ontology": ontology_gate(),
        "climate_occupancy": climate_occupancy_gate(),
        "perennial_stock": perennial_stock_gate(),
        "t3_provenance": t3_provenance_gate(),
        "operational_authorization": operational_authorization_gate(),
        "lifecycle_failure_ledger": lifecycle_failure_ledger_gate(),
        "numeric_parameters": numeric_parameter_gate(),
        "report": report_gate(),
        "frozen_paths": frozen_paths_gate(),
        "no_c0a_contamination": no_c0a_contamination(),
        "no_optimization_artifacts": no_optimization_artifacts(),
    }


def main() -> int:
    gates = run_all_gates()
    for name, result in gates.items():
        print(f"{name}={result['status']}")
        if result["status"] != "PASS":
            detail = {key: value for key, value in result.items() if key != "status"}
            print(json.dumps(detail, indent=2, sort_keys=True))
    status = "PASS" if all(result["status"] == "PASS" for result in gates.values()) else "FAIL"
    print(f"C0B1_PREFLIGHT={status}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
