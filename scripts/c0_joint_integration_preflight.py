"""Deterministic Joint C0 outcome and decision architecture integration gate."""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import io
import json
import subprocess
import sys
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_BRANCH = "phase/c0-joint-outcome-decision-integration-v1"
C0A_FREEZE = "5e2b32edba2e4b3eee471c669f427ef9a70fe4b6"
C0B6_FREEZE = "cf99e30f2f6cfe686f760b2dd608d933e3918bc0"
FINAL_STATUS = "PASS_WITH_TARGETED_PRE_ESTIMATION_GATES"

EVIDENCE_PATH = ROOT / "outputs/joint_c0/C0_JOINT_EVIDENCE_REGISTRY.csv"
COMPATIBILITY_PATH = ROOT / "outputs/joint_c0/C0_JOINT_COMPATIBILITY_MATRIX.csv"
AUTHORIZATION_PATH = ROOT / "outputs/joint_c0/C0_JOINT_AUTHORIZATION_MATRIX.csv"
REPORT_PATH = ROOT / "outputs/joint_c0/C0_JOINT_REPORT.md"
CONFIG_PATH = ROOT / "config/joint_c0/outcome_decision_integration_v1.json"
SCRIPT_PATH = ROOT / "scripts/c0_joint_integration_preflight.py"
TEST_PATH = ROOT / "tests/test_c0_joint_integration.py"

RAW_PATH = ROOT / "data/raw/Formato_dataset_productos_dra__ (2).csv"
PANEL_PATH = ROOT / "data/processed/panel_master.csv"
CLIMATE_SPEC_PATH = ROOT / "config/climate_exposure/climate_exposure_spec_v1.json"
C0B6_CONFIG_PATH = ROOT / "config/decision_ontology/reference_configuration_data_master_v1.json"
PERENNIAL_EXPOSURE_PATH = ROOT / "data/processed/phenology/perennial_exposures_long.parquet"

AUTHORIZED_SCOPE = {
    "outputs/joint_c0/C0_JOINT_EVIDENCE_REGISTRY.csv",
    "outputs/joint_c0/C0_JOINT_COMPATIBILITY_MATRIX.csv",
    "outputs/joint_c0/C0_JOINT_AUTHORIZATION_MATRIX.csv",
    "outputs/joint_c0/C0_JOINT_REPORT.md",
    "config/joint_c0/outcome_decision_integration_v1.json",
    "scripts/c0_joint_integration_preflight.py",
    "tests/test_c0_joint_integration.py",
}

C0A_FILES = {
    "outputs/outcome/C0A_EVIDENCE_REGISTRY.csv": "82a01d6762050c43ace0726be40227f9d5e21d714f7ba7cf40fca2ccd7fca7c1",
    "outputs/outcome/C0A_OUTCOME_EVIDENCE_REPORT.md": "2d1d261a74ba21145797de14d846d53e7383fed77789cc259931c295ee2d40dd",
    "scripts/c0a_outcome_evidence_preflight.py": "21ce349cf96aa9d70a393bf067f1a03c9386de1c8a334304a058a36ccdedd994",
    "tests/test_c0a_outcome_evidence_preflight.py": "c56522f299f140c14bebd26c02cdb64d4a7373ac06a9d116d8ac44b3f4092220",
}

C0B6_FILES = {
    "data/processed/decision/reference_configurations_transient_long.csv": "749dae0e8d5d84fee0a09e1661a91097ef1a2feea7f52bd70fbc8cf36fa36a16",
    "outputs/decision_feasibility/C0B6_SCOPE_ADJUDICATION.csv": "303a76b21bc32f33fb1a08e8103f3fb5f8050ec2d2c491fa06972ac2114c1cc3",
    "outputs/decision_feasibility/C0B6_ALTERNATIVE_DATA_AUDIT.csv": "0df2353ff65f917f2fe1c30332d9260e97ff3a10939dba8e58ecd6be3e41cb32",
    "outputs/decision_feasibility/C0B6_ALTERNATIVE_DATA_REPORT.md": "a42fca0ec258ab83e7021ed409e5ea92be6ed01a0817893df0162baaa6755b0b",
    "config/decision_ontology/reference_configuration_data_master_v1.json": "a63ba28bcfb2c6548055bbd385169b149405232b6f65927f4511e0a5198a9aef",
    "scripts/c0b6_alternative_data_master.py": "b29819dd9b6363dad3d9576a6f7114e2a7b76ff58bde8e0492aae785ddc5b4d3",
    "tests/test_c0b6_alternative_data_master.py": "34a09cceceae6cd78f4df8ddfc9c92806a85caf1805ea18565b12ddebca4332e",
}

FROZEN_UPSTREAM_HASHES = {
    "data/processed/panel_master.csv": "ab9b4ce53c008a1bc3ceb7d3e4c5d617d2544ad48632b747079c33e8b95d1214",
    "config/climate_exposure/climate_exposure_spec_v1.json": "e2e1eabbf8530cb0dfe8538d12f12d73a6a8e77c0e773351b593a14cbe1e268a",
    "data/processed/phenology/perennial_exposures_long.parquet": "3fde5c7fc7a00f4c6600a18f60935bad213408ffa2ba3bac5828603e46984714",
    "data/processed/phenology/transient_cohort_exposures.parquet": "e4ce7922f00a516643a5de832cc38377e20b3755ac46152cfb79900441564b39",
    "data/processed/phenology/transient_campaign_exposures_strict.parquet": "349413312568d0d423675bf58320ade41d2d9e700f138e7fbec55fc580bc1fb5",
    "data/processed/phenology/phenology_windows_frozen.csv": "ea25d949be9834a9e35352d970bb1b2172cac7d49db7eabb101ddfde9cfb657d",
}

DISTRICTS = (
    ("200101", "PIURA"), ("200105", "CATACAOS"), ("200108", "EL TALLAN"),
    ("200111", "LAS LOMAS"), ("200114", "TAMBO GRANDE"), ("200201", "AYABACA"),
    ("200205", "MONTERO"), ("200304", "HUARMACA"),
    ("200802", "BELLAVISTA DE LA UNION"), ("200803", "BERNAL"),
    ("200804", "CRISTO NOS VALGA"), ("200805", "VICE"),
    ("200806", "RINCONADA LLICUAR"),
)

CROPS = {
    "RICE": ("14010020000", "ARROZ"),
    "MAD": ("14010070000", "MAIZ AMARILLO DURO"),
    "MANGO": ("13010210000", "MANGO"),
    "LEMON": ("13010170102", "LIMON SUTIL"),
    "BANANA": ("15010040000", "PLATANOS Y BANANAS"),
}
TRANSIENT_CROPS = {CROPS["RICE"][0], CROPS["MAD"][0]}
PERENNIAL_CROPS = {CROPS[name][0] for name in ("MANGO", "LEMON", "BANANA")}
CAMPAIGNS = tuple(f"{year}/{year + 1}" for year in range(2016, 2023))

EXPECTED_SAMPLE_FACTS = {
    "RICE": {"districts_n": 46, "usable": 294, "complete_grid": 322, "c0b6_usable": 90},
    "MAD": {"districts_n": 55, "usable": 352, "complete_grid": 385, "c0b6_usable": 91},
    "MANGO": {"districts_n": 36, "usable": 255, "complete_grid": 288},
    "LEMON": {"districts_n": 44, "usable": 311, "complete_grid": 352},
    "BANANA": {"districts_n": 54, "usable": 390, "complete_grid": 432},
}

EVIDENCE_COLUMNS = [
    "EVIDENCE_ID", "DOMAIN", "SOURCE_REF", "SOURCE_SHA256", "EVIDENCE_FACT",
    "INTEGRATION_DECISION", "STATUS", "NOTES",
]
COMPATIBILITY_COLUMNS = [
    "CHECK_ID", "DOMAIN", "C0A_CONTRACT", "C0B6_OR_UPSTREAM_CONTRACT",
    "COMPATIBILITY_STATUS", "REQUIRED_GATE", "RATIONALE",
]
AUTHORIZATION_COLUMNS = [
    "COMPONENT", "CURRENT_STATUS", "AUTHORIZED_NEXT_PHASE", "REQUIRES_FUTURE_GATE",
    "FORBIDDEN", "RATIONALE",
]


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, text=True, encoding="utf-8",
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    )
    return result.stdout.strip()


def git_bytes(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def csv_bytes(columns: list[str], rows: list[dict[str, str]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def parse_decimal(value: str | None) -> Decimal | None:
    if value is None or not value.strip():
        return None
    return Decimal(value)


def read_c0a_registry() -> list[dict[str, str]]:
    payload = git_bytes("show", f"{C0A_FREEZE}:outputs/outcome/C0A_EVIDENCE_REGISTRY.csv")
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"), newline="")))


def c0a_decision(
    rows: list[dict[str, str]], variable: str, category: str, claim_contains: str = "",
) -> dict[str, str]:
    for row in rows:
        if (
            row["VARIABLE"] == variable
            and row["CLAIM_CATEGORY"] == category
            and claim_contains.lower() in row["CLAIM"].lower()
        ):
            return row
    raise KeyError((variable, category, claim_contains))


def c0a_conclusions() -> dict[str, Any]:
    rows = read_c0a_registry()
    report = git_bytes("show", f"{C0A_FREEZE}:outputs/outcome/C0A_OUTCOME_EVIDENCE_REPORT.md").decode("utf-8")
    return {
        "produccion": c0a_decision(rows, "PRODUCCION", "UNIT", "Final adjudication"),
        "yield": c0a_decision(rows, "YIELD_RAW", "UNIT"),
        "cosecha": c0a_decision(rows, "COSECHA", "UNIT"),
        "siembra": c0a_decision(rows, "SIEMBRA", "UNIT"),
        "precio": c0a_decision(rows, "PRECIO_CHACRA", "UNIT"),
        "verde_semantics": c0a_decision(rows, "VERDE_ACTUAL", "SEMANTICS"),
        "verde_flow": c0a_decision(rows, "VERDE_ACTUAL", "STOCK_FLOW"),
        "monetary": c0a_decision(rows, "CROSS_VARIABLE", "DIMENSIONALITY", "monetary translation"),
        "report_gvp_not_built": "GVP construction is blocked" in report,
        "report_causal_not_authorized": "Causal interpretation is not authorized" in report,
    }


def c0a_introduced_files() -> dict[str, str]:
    lines = git("diff-tree", "--root", "--no-commit-id", "--name-status", "-r", C0A_FREEZE).splitlines()
    return {line.split("\t", 1)[1]: line.split("\t", 1)[0] for line in lines if "\t" in line}


def transient_sample_contracts() -> dict[str, dict[str, Any]]:
    groups: dict[tuple[str, str, int], dict[str, Any]] = defaultdict(
        lambda: {"production": Decimal(0), "production_seen": False, "harvest": Decimal(0), "harvest_seen": False}
    )
    with RAW_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            crop = row["COD_CULTIVO"]
            if crop not in TRANSIENT_CROPS:
                continue
            year_month = int(row["MES"])
            year, month = divmod(year_month, 100)
            start_year = year if month >= 8 else year - 1
            if start_year < 2016 or start_year > 2022:
                continue
            group = groups[(crop, row["UBIGEO"], start_year)]
            production = parse_decimal(row["PRODUCCION"])
            harvest = parse_decimal(row["COSECHA"])
            if production is not None:
                group["production"] += production
                group["production_seen"] = True
            if harvest is not None:
                group["harvest"] += harvest
                group["harvest_seen"] = True

    c0b6_support = {ubigeo for ubigeo, _ in DISTRICTS}
    result: dict[str, dict[str, Any]] = {}
    for crop_name in ("RICE", "MAD"):
        crop_code = CROPS[crop_name][0]
        valid = {
            (ubigeo, start_year)
            for (crop, ubigeo, start_year), values in groups.items()
            if crop == crop_code
            and values["production_seen"]
            and values["harvest_seen"]
            and values["harvest"] > 0
        }
        districts = sorted({ubigeo for ubigeo, _ in valid})
        result[crop_name] = {
            "crop_code": crop_code,
            "crop_std": CROPS[crop_name][1],
            "outcome_observation_unit": "DISTRICT_CROP_AGRICULTURAL_CAMPAIGN_AUG_JUL",
            "climate_exposure_unit": "DISTRICT_CROP_AGRICULTURAL_CAMPAIGN_PHENOLOGY_WEIGHTED",
            "expected_linkage_key": "UBIGEO|COD_CULTIVO|CAMPAIGN_ID",
            "available_periods": list(CAMPAIGNS),
            "time_periods_n": 7,
            "districts_n": len(districts),
            "usable_outcome_observations": len(valid),
            "expected_observations_if_complete": len(districts) * 7,
            "c0b6_support_usable_observations": sum(ubigeo in c0b6_support for ubigeo, _ in valid),
            "c0b6_support_expected_if_complete": 91,
            "outcome_contract_status": "COHERENT_DEFINED_NOT_BUILT_REQUIRES_TRANSIENT_OUTCOME_MASTER",
        }
    return result


def perennial_sample_contracts() -> dict[str, dict[str, Any]]:
    panel: dict[str, set[tuple[str, int]]] = defaultdict(set)
    with PANEL_PATH.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            crop = row["COD_CULTIVO"]
            if crop in PERENNIAL_CROPS and row["YIELD_RAW"].strip():
                panel[crop].add((row["UBIGEO"], int(row["ANO"])))

    import pyarrow.parquet as pq

    exposure_table = pq.read_table(
        PERENNIAL_EXPOSURE_PATH,
        columns=["UBIGEO", "COD_CULTIVO", "REFERENCE_CALENDAR_YEAR", "WINDOW_ID", "EXPOSURE_VALID"],
    )
    exposure_keys: dict[str, set[tuple[str, int]]] = defaultdict(set)
    windows: dict[str, set[str]] = defaultdict(set)
    for row in exposure_table.to_pylist():
        if row["EXPOSURE_VALID"]:
            exposure_keys[row["COD_CULTIVO"]].add((row["UBIGEO"], row["REFERENCE_CALENDAR_YEAR"]))
            windows[row["COD_CULTIVO"]].add(row["WINDOW_ID"])

    result: dict[str, dict[str, Any]] = {}
    for crop_name in ("MANGO", "LEMON", "BANANA"):
        crop_code = CROPS[crop_name][0]
        keys = panel[crop_code]
        districts = sorted({ubigeo for ubigeo, _ in keys})
        years = sorted({year for _, year in keys})
        if exposure_keys[crop_code] != keys:
            raise ValueError(f"perennial outcome/exposure key mismatch: {crop_name}")
        result[crop_name] = {
            "crop_code": crop_code,
            "crop_std": CROPS[crop_name][1],
            "outcome_observation_unit": "DISTRICT_CROP_CALENDAR_YEAR",
            "climate_exposure_unit": "DISTRICT_CROP_CALENDAR_YEAR_WINDOW",
            "expected_linkage_key": "UBIGEO|COD_CULTIVO|REFERENCE_CALENDAR_YEAR",
            "available_periods": years,
            "time_periods_n": len(years),
            "districts_n": len(districts),
            "usable_outcome_observations": len(keys),
            "expected_observations_if_complete": len(districts) * len(years),
            "exposure_windows": sorted(windows[crop_code]),
            "outcome_contract_status": "AUTHORIZED_FOR_ECONOMETRIC_DESIGN",
        }
    return result


def sample_contracts() -> dict[str, dict[str, Any]]:
    return {**transient_sample_contracts(), **perennial_sample_contracts()}


def evidence_row(
    evidence_id: str, domain: str, source_ref: str, source_sha256: str,
    fact: str, decision: str, notes: str,
) -> dict[str, str]:
    return {
        "EVIDENCE_ID": evidence_id,
        "DOMAIN": domain,
        "SOURCE_REF": source_ref,
        "SOURCE_SHA256": source_sha256,
        "EVIDENCE_FACT": fact,
        "INTEGRATION_DECISION": decision,
        "STATUS": "PASS_ADJUDICATED",
        "NOTES": notes,
    }


def build_evidence_rows(samples: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    number = 1
    for path, digest in C0A_FILES.items():
        rows.append(evidence_row(
            f"JC0-E{number:03d}", "C0A_OBJECT_PROVENANCE", f"{C0A_FREEZE}:{path}", digest,
            "C0A file introduced by sibling freeze and read from Git object storage.",
            "IMMUTABLE_SIBLING_INPUT", "The file is not copied into Joint C0.",
        ))
        number += 1
    facts = [
        ("C0B6_PROVENANCE", C0B6_CONFIG_PATH.relative_to(ROOT).as_posix(), C0B6_FILES[C0B6_CONFIG_PATH.relative_to(ROOT).as_posix()], "C0B6 S1 architecture is frozen at the current base.", "IMMUTABLE_ANCESTOR_INPUT", "C0B6 is not reopened."),
        ("OUTCOME_UNIT", "C0A_EVIDENCE_REGISTRY", C0A_FILES["outputs/outcome/C0A_EVIDENCE_REGISTRY.csv"], "PRODUCCION is metric tonne by institutional convergence.", "PRODUCCION_UNIT=METRIC_TONNE", "Exact dictionary omitted the unit; C0A convergence is preserved."),
        ("OUTCOME_UNIT", "C0A_EVIDENCE_REGISTRY", C0A_FILES["outputs/outcome/C0A_EVIDENCE_REGISTRY.csv"], "YIELD_RAW is production over harvested area.", "YIELD_UNIT=TM_PER_HA", "No monthly-yield averaging is authorized."),
        ("PRICE_UNIT", "C0A_EVIDENCE_REGISTRY", C0A_FILES["outputs/outcome/C0A_EVIDENCE_REGISTRY.csv"], "PRECIO_CHACRA is farm-gate price in soles per kilogram.", "PRICE_UNIT=S_PER_KG", "Temporal mapping and real-price treatment remain undefined."),
        ("TRANSIENT_OUTCOME", CLIMATE_SPEC_PATH.relative_to(ROOT).as_posix(), FROZEN_UPSTREAM_HASHES[CLIMATE_SPEC_PATH.relative_to(ROOT).as_posix()], "Transient outcome is an Aug-Jul ratio of summed production to summed harvested area.", "DEFINED_NOT_BUILT_REQUIRES_OUTCOME_MASTER", "Mean or sum of monthly yields is forbidden."),
        ("PERENNIAL_OUTCOME", PANEL_PATH.relative_to(ROOT).as_posix(), FROZEN_UPSTREAM_HASHES[PANEL_PATH.relative_to(ROOT).as_posix()], "Perennial annual YIELD_RAW keys match all valid perennial exposure keys.", "AUTHORIZED_FOR_ECONOMETRIC_DESIGN", "VERDE_ACTUAL is not used as productive stock."),
        ("YIELD_AREA_MAPPING", C0B6_CONFIG_PATH.relative_to(ROOT).as_posix(), C0B6_FILES[C0B6_CONFIG_PATH.relative_to(ROOT).as_posix()], "A1/A2 areas are SIEMBRA hectares while yield is per harvested hectare.", "REQUIRES_SOWN_TO_HARVESTED_AREA_MAPPING_GATE", "Unit cancellation alone does not certify physical production semantics."),
        ("PRICE_MAPPING", "C0A_EVIDENCE_REGISTRY", C0A_FILES["outputs/outcome/C0A_EVIDENCE_REGISTRY.csv"], "Observed farm-gate prices are in soles/kg with no frozen temporal or real-price rule.", "REQUIRES_PRICE_MAPPING_GATE", "No annual mean, harvest price, deflator, or future price is invented."),
        ("RISK_SCOPE", C0B6_CONFIG_PATH.relative_to(ROOT).as_posix(), C0B6_FILES[C0B6_CONFIG_PATH.relative_to(ROOT).as_posix()], "C0B6 forbids five-crop A1/A2 aggregation and perennial CVaR cancellation.", "A1_A2_RISK_METRIC_SCOPE=TRANSIENT_BLOCK_ONLY", "No risk metric is calculated."),
        ("IDENTIFICATION", "JOINT_C0_ADJUDICATION", "NOT_APPLICABLE", "No stronger causal design is frozen.", "EMPIRICAL_ASSOCIATION_CLIMATE_RESPONSE_ONLY", "No causal or structural production-function claim."),
        ("SCENARIO_ORDER", "JOINT_C0_ADJUDICATION", "NOT_APPLICABLE", "Econometric design and support characterization precede scenarios.", "SCENARIO_MODEL_SEPARATION_REQUIRED", "No scenario tuning may select the model."),
    ]
    for domain, source, digest, fact, decision, notes in facts:
        rows.append(evidence_row(f"JC0-E{number:03d}", domain, source, digest, fact, decision, notes))
        number += 1
    for crop_name in ("RICE", "MAD", "MANGO", "LEMON", "BANANA"):
        sample = samples[crop_name]
        rows.append(evidence_row(
            f"JC0-E{number:03d}", "SAMPLE_SUPPORT", "FROZEN_RAW_PANEL_AND_EXPOSURE_ARTIFACTS",
            "MULTIPLE_FROZEN_HASHES", f"{crop_name}: {sample['usable_outcome_observations']} usable outcome observations across {sample['time_periods_n']} periods and {sample['districts_n']} districts.",
            sample["outcome_contract_status"],
            f"Complete rectangular grid would contain {sample['expected_observations_if_complete']} observations.",
        ))
        number += 1
    return rows


def compatibility_row(
    check_id: str, domain: str, c0a: str, upstream: str, status: str, gate: str, rationale: str,
) -> dict[str, str]:
    return {
        "CHECK_ID": check_id, "DOMAIN": domain, "C0A_CONTRACT": c0a,
        "C0B6_OR_UPSTREAM_CONTRACT": upstream, "COMPATIBILITY_STATUS": status,
        "REQUIRED_GATE": gate, "RATIONALE": rationale,
    }


def build_compatibility_rows() -> list[dict[str, str]]:
    return [
        compatibility_row("JC0-C001", "PRODUCCION_UNIT", "METRIC_TONNE", "PHYSICAL_QUANTITY_REQUIRED_LATER", "PASS", "NONE", "C0A supplies the missing physical mass unit."),
        compatibility_row("JC0-C002", "YIELD_UNIT", "TM_PER_HA_HARVESTED", "A1_A2_AREA_IS_SOWN_HA", "PASS_WITH_GATE", "SOWN_TO_HARVESTED_AREA_MAPPING", "Dimensional units align but area semantics differ."),
        compatibility_row("JC0-C003", "TRANSIENT_TIME", "MONTHLY_SOURCE", "AUG_JUL_CAMPAIGN_OUTCOME", "PASS_WITH_GATE", "TRANSIENT_OUTCOME_MASTER", "Campaign ratio is defined and not built."),
        compatibility_row("JC0-C004", "TRANSIENT_EXPOSURE", "NO_MODEL_SELECTED", "COHORT_PRIMARY_DATA_PRODUCT_STRICT_AUDIT_LAYER", "PASS_WITH_GATE", "PRIMARY_TRANSIENT_ECONOMETRIC_EXPOSURE_SELECTION", "Stage B did not select the econometric exposure."),
        compatibility_row("JC0-C005", "PERENNIAL_TIME", "ANNUAL_YIELD_RATIO", "CALENDAR_YEAR_EXPOSURES", "PASS", "ECONOMETRIC_DESIGN_FREEZE", "Outcome and exposure keys match exactly."),
        compatibility_row("JC0-C006", "PERENNIAL_STATE", "VERDE_ACTUAL_STOCK_SNAPSHOT", "PERENNIALS_EXOGENOUS_OUTSIDE_A1_A2", "PASS", "NONE", "No productive-stock inference is needed for the outcome model."),
        compatibility_row("JC0-C007", "DUAL_LAYER", "FIVE_CROP_CHARACTERIZATION", "RICE_MAD_REFERENCE_STRESS_TEST", "PASS", "NONAGGREGATION_FIREWALL", "The linked layers retain different crop scopes."),
        compatibility_row("JC0-C008", "ALTERNATIVES", "NO_OUTCOME_BASED_SELECTION", "TWO_PRESPECIFIED_REFERENCE_CONFIGURATIONS", "PASS", "NONE", "A1/A2 remain frozen and outcome independent."),
        compatibility_row("JC0-C009", "TIMING", "NO_GENERIC_MONTHLY_YIELD", "ALTERNATIVE_SPECIFIC_SIEMBRA_WEIGHTS", "PASS_WITH_GATE", "SCENARIO_EXPOSURE_BUILD", "Frozen timing weights can drive future phenology exposure construction."),
        compatibility_row("JC0-C010", "PRICE_UNIT", "S_PER_KG", "QUANTITY_TM", "PASS_WITH_GATE", "KG_PER_TM_CONVERSION", "TM x 1000 kg/TM x S/kg is soles."),
        compatibility_row("JC0-C011", "PRICE_TIME", "NO_TEMPORAL_RULE", "CAMPAIGN_AND_CALENDAR_OUTCOMES", "PASS_WITH_GATE", "PRICE_MAPPING_GATE", "No price matching or future price rule is frozen."),
        compatibility_row("JC0-C012", "NOMINAL_VALUE", "OBSERVATION_PERIOD_SOLES", "INTERTEMPORAL_COMPARISON_PENDING", "PASS_WITH_GATE", "MONETARY_TREATMENT_GATE", "No deflation or normalization rule is selected."),
        compatibility_row("JC0-C013", "GVP", "DIMENSIONALLY_AUTHORIZED_NOT_BUILT", "NO_ECONOMIC_OUTPUT", "PASS", "NUMERICAL_ECONOMIC_TRANSLATION_GATE", "Only quantity times price is structurally authorized."),
        compatibility_row("JC0-C014", "FIVE_CROP_AGGREGATION", "NOT_BUILT", "NOT_AUTHORIZED", "PASS", "FORMAL_ARCHITECTURE_REOPEN", "Five crop availability does not define a portfolio."),
        compatibility_row("JC0-C015", "RISK", "NO_RISK_METRICS", "TRANSIENT_BLOCK_ONLY", "PASS", "POST_ESTIMATION_RISK_GATE", "Perennials cannot be assumed to cancel in CVaR."),
        compatibility_row("JC0-C016", "LAND", "YIELD_PER_HARVESTED_HA", "NO_LAND_CAP_OR_BOUNDS", "PASS", "NONE", "Joint C0 performs no land feasibility inference."),
        compatibility_row("JC0-C017", "WATER", "NO_WATER_OUTCOME", "WATER_MODEL_NOT_AUTHORIZED", "PASS", "FORMAL_ARCHITECTURE_REOPEN", "No water quantity or entitlement is inferred."),
        compatibility_row("JC0-C018", "IDENTIFICATION", "NO_CAUSAL_AUTHORIZATION", "REFERENCE_STRESS_TEST_NOT_CAUSAL", "PASS", "ECONOMETRIC_DESIGN_FREEZE", "Maximum claim is empirical association/climate response."),
        compatibility_row("JC0-C019", "SUPPORT", "SHORT_UNBALANCED_PANEL", "FUTURE_SCENARIOS_PENDING", "PASS_WITH_GATE", "EMPIRICAL_SUPPORT_ENVELOPE", "Out-of-support prediction is not authorized."),
        compatibility_row("JC0-C020", "RQ_ARCHITECTURE", "FIVE_CROP_CHARACTERIZATION", "RICE_MAD_STRESS_TEST", "PASS", "RQ_REFRAME_AT_DESIGN_FREEZE", "Two linked questions are supported without merging scopes."),
    ]


def build_authorization_rows() -> list[dict[str, str]]:
    return [
        {"COMPONENT": "Rice climate-yield model", "CURRENT_STATUS": "DESIGN_AUTHORIZED_ESTIMATION_BLOCKED", "AUTHORIZED_NEXT_PHASE": "TRUE", "REQUIRES_FUTURE_GATE": "TRANSIENT_OUTCOME_MASTER;PRIMARY_TRANSIENT_ECONOMETRIC_EXPOSURE_SELECTION", "FORBIDDEN": "FALSE", "RATIONALE": "Campaign outcome is defined but not built; primary exposure is not selected."},
        {"COMPONENT": "MAD climate-yield model", "CURRENT_STATUS": "DESIGN_AUTHORIZED_ESTIMATION_BLOCKED", "AUTHORIZED_NEXT_PHASE": "TRUE", "REQUIRES_FUTURE_GATE": "TRANSIENT_OUTCOME_MASTER;PRIMARY_TRANSIENT_ECONOMETRIC_EXPOSURE_SELECTION", "FORBIDDEN": "FALSE", "RATIONALE": "Campaign outcome is defined but not built; primary exposure is not selected."},
        {"COMPONENT": "Mango climate-yield model", "CURRENT_STATUS": "AUTHORIZED_FOR_ECONOMETRIC_DESIGN", "AUTHORIZED_NEXT_PHASE": "TRUE", "REQUIRES_FUTURE_GATE": "ECONOMETRIC_DESIGN_FREEZE_BEFORE_ESTIMATION", "FORBIDDEN": "FALSE", "RATIONALE": "Annual yield and current-year May-Jun exposure keys match."},
        {"COMPONENT": "Lemon climate-yield model", "CURRENT_STATUS": "AUTHORIZED_FOR_ECONOMETRIC_DESIGN", "AUTHORIZED_NEXT_PHASE": "TRUE", "REQUIRES_FUTURE_GATE": "ECONOMETRIC_DESIGN_FREEZE_BEFORE_ESTIMATION", "FORBIDDEN": "FALSE", "RATIONALE": "Annual yield and t/t-1 full-year exposure keys match."},
        {"COMPONENT": "Banana climate-yield model", "CURRENT_STATUS": "AUTHORIZED_FOR_ECONOMETRIC_DESIGN", "AUTHORIZED_NEXT_PHASE": "TRUE", "REQUIRES_FUTURE_GATE": "ECONOMETRIC_DESIGN_FREEZE_BEFORE_ESTIMATION", "FORBIDDEN": "FALSE", "RATIONALE": "Annual yield and t/t-1 full-year exposure keys match."},
        {"COMPONENT": "A1/A2 transient area master", "CURRENT_STATUS": "FROZEN_READY_SOWN_AREA", "AUTHORIZED_NEXT_PHASE": "TRUE", "REQUIRES_FUTURE_GATE": "SOWN_TO_HARVESTED_AREA_MAPPING_BEFORE_PRODUCTION", "FORBIDDEN": "FALSE", "RATIONALE": "Reference areas are empirically realized SIEMBRA hectares."},
        {"COMPONENT": "alternative-specific timing", "CURRENT_STATUS": "FROZEN_READY", "AUTHORIZED_NEXT_PHASE": "TRUE", "REQUIRES_FUTURE_GATE": "DISTRICT_CROP_ALTERNATIVE_SCENARIO_EXPOSURE_BUILD", "FORBIDDEN": "FALSE", "RATIONALE": "Use frozen A1/A2 timing; generic T3 and pooling remain forbidden."},
        {"COMPONENT": "five-crop combined portfolio", "CURRENT_STATUS": "NOT_YET_AUTHORIZED", "AUTHORIZED_NEXT_PHASE": "FALSE", "REQUIRES_FUTURE_GATE": "FORMALLY_VERSIONED_AGGREGATION_ARCHITECTURE", "FORBIDDEN": "TRUE", "RATIONALE": "Layer 1 crop characterization is not a portfolio definition."},
        {"COMPONENT": "A1/A2 five-crop aggregation", "CURRENT_STATUS": "NOT_AUTHORIZED", "AUTHORIZED_NEXT_PHASE": "FALSE", "REQUIRES_FUTURE_GATE": "FORMAL_C0B6_SCOPE_REOPEN", "FORBIDDEN": "TRUE", "RATIONALE": "A1/A2 contain Rice and MAD only."},
        {"COMPONENT": "A1/A2 transient economic aggregation", "CURRENT_STATUS": "STRUCTURAL_SCOPE_COHERENT_NUMERICAL_BLOCKED", "AUTHORIZED_NEXT_PHASE": "FALSE", "REQUIRES_FUTURE_GATE": "YIELD_AREA_MAPPING;PRICE_MAPPING;COMMON_SCENARIO_AND_HORIZON", "FORBIDDEN": "FALSE", "RATIONALE": "Aggregation structure exists but numeric inputs are not authorized."},
        {"COMPONENT": "price mapping", "CURRENT_STATUS": "REQUIRES_PRICE_MAPPING_GATE", "AUTHORIZED_NEXT_PHASE": "FALSE", "REQUIRES_FUTURE_GATE": "TEMPORAL_AND_MONETARY_PRICE_SPECIFICATION", "FORBIDDEN": "FALSE", "RATIONALE": "No annual, harvest-month, campaign, deflation, or future-price rule is frozen."},
        {"COMPONENT": "GVP construction", "CURRENT_STATUS": "DIMENSIONALLY_AUTHORIZED_NOT_BUILT", "AUTHORIZED_NEXT_PHASE": "FALSE", "REQUIRES_FUTURE_GATE": "QUANTITY_AND_PRICE_MAPPING", "FORBIDDEN": "FALSE", "RATIONALE": "Quantity times price is structural only."},
        {"COMPONENT": "VaR", "CURRENT_STATUS": "NOT_AUTHORIZED", "AUTHORIZED_NEXT_PHASE": "FALSE", "REQUIRES_FUTURE_GATE": "POST_ESTIMATION_RISK_SPECIFICATION", "FORBIDDEN": "TRUE", "RATIONALE": "No loss distribution or risk horizon is defined."},
        {"COMPONENT": "CVaR", "CURRENT_STATUS": "NOT_AUTHORIZED_TRANSIENT_BLOCK_ONLY_IF_LATER_OPENED", "AUTHORIZED_NEXT_PHASE": "FALSE", "REQUIRES_FUTURE_GATE": "POST_ESTIMATION_RISK_SPECIFICATION", "FORBIDDEN": "TRUE", "RATIONALE": "Common perennial cancellation is explicitly false."},
        {"COMPONENT": "ENSO scenario prediction", "CURRENT_STATUS": "NOT_AUTHORIZED", "AUTHORIZED_NEXT_PHASE": "FALSE", "REQUIRES_FUTURE_GATE": "MODEL_FREEZE;DIAGNOSTICS;EMPIRICAL_SUPPORT_ENVELOPE;SCENARIO_FREEZE", "FORBIDDEN": "TRUE", "RATIONALE": "Scenario tuning cannot influence econometric specification."},
        {"COMPONENT": "continuous optimization", "CURRENT_STATUS": "NOT_AUTHORIZED", "AUTHORIZED_NEXT_PHASE": "FALSE", "REQUIRES_FUTURE_GATE": "FORMAL_ARCHITECTURE_REOPEN", "FORBIDDEN": "TRUE", "RATIONALE": "No objective, bounds, or continuous decision domain is authorized."},
        {"COMPONENT": "water-constrained model", "CURRENT_STATUS": "NOT_AUTHORIZED", "AUTHORIZED_NEXT_PHASE": "FALSE", "REQUIRES_FUTURE_GATE": "FORMAL_HYDRAULIC_EVIDENCE_AND_ARCHITECTURE", "FORBIDDEN": "TRUE", "RATIONALE": "No water capacity, entitlement, or service fraction is identified."},
    ]


def build_config(
    samples: dict[str, dict[str, Any]], authorization: list[dict[str, str]], artifact_hashes: dict[str, str],
) -> dict[str, Any]:
    return {
        "schema_version": "JOINT_C0_OUTCOME_DECISION_INTEGRATION_V1",
        "phase": "JOINT_C0_OUTCOME_AND_DECISION_ARCHITECTURE_INTEGRATION",
        "immutable_inputs": {
            "c0a_freeze": C0A_FREEZE,
            "c0a_relationship": "SIBLING_NOT_MERGED_READ_VIA_GIT_OBJECTS",
            "c0a_files_sha256": C0A_FILES,
            "c0b6_freeze": C0B6_FREEZE,
            "c0b6_relationship": "CURRENT_FROZEN_BASE",
            "c0b6_files_sha256": C0B6_FILES,
            "frozen_upstream_sha256": FROZEN_UPSTREAM_HASHES,
        },
        "outcome_semantics": {
            "PRODUCCION": {"unit": "METRIC_TONNE", "status": "CERTIFIED_INSTITUTIONAL_CONVERGENCE"},
            "YIELD_RAW": {"unit": "TM_PER_HA", "denominator_semantics": "HARVESTED_AREA_HA"},
            "COSECHA": {"unit": "ha", "semantics": "MONTHLY_HARVESTED_AREA_FLOW"},
            "SIEMBRA": {"unit": "ha", "semantics": "MONTHLY_SOWN_AREA_FLOW"},
            "PRECIO_CHACRA": {"unit": "S_PER_KG", "semantics": "FARM_GATE_PRICE_RECEIVED_BY_PRODUCER_EXCLUDING_IGV"},
            "VERDE_ACTUAL": {"semantics": "CURRENT_INSTALLED_CROP_AREA_STOCK_SNAPSHOT", "productive_stock_inference_authorized": False},
            "monetary_translation_status": "DIMENSIONALLY_AUTHORIZED_NOT_BUILT",
            "gvp_built": False,
        },
        "transient_outcome_contract": {
            "status": "COHERENT_DEFINED_NOT_BUILT_REQUIRES_TRANSIENT_OUTCOME_MASTER",
            "variable": "TRANSIENT_CAMPAIGN_YIELD_RAW",
            "formula": "SUM(PRODUCCION within Aug-Jul campaign) / SUM(COSECHA within Aug-Jul campaign)",
            "unit": "TM_PER_HA",
            "observation_unit": "DISTRICT_CROP_AGRICULTURAL_CAMPAIGN_AUG_JUL",
            "forbidden_replacements": ["MEAN_MONTHLY_YIELD", "SUM_MONTHLY_YIELD", "MAX_MONTHLY_YIELD", "CALENDAR_YEAR_YIELD"],
        },
        "perennial_outcome_contracts": {
            crop: {
                "status": samples[crop]["outcome_contract_status"],
                "unit": "TM_PER_HA",
                "observation_unit": "DISTRICT_CROP_CALENDAR_YEAR",
                "formula": "SUM(PRODUCCION within calendar year) / SUM(COSECHA within calendar year)",
                "verde_actual_used_as_productive_stock": False,
                "cosecha_used_as_installed_stock": False,
            }
            for crop in ("MANGO", "LEMON", "BANANA")
        },
        "dual_analytical_layers": {
            "status": "SUPPORTED_WITH_STRICT_NONAGGREGATION_FIREWALL",
            "layer_1": {"name": "FIVE_CROP_CLIMATE_ECONOMIC_RISK_CHARACTERIZATION", "crop_codes": [CROPS[name][0] for name in CROPS], "combined_portfolio_authorized": False},
            "layer_2": {"name": "RICE_MAD_FINITE_REFERENCE_CONFIGURATION_STRESS_TEST", "crop_codes": [CROPS["RICE"][0], CROPS["MAD"][0]], "alternative_ids": ["C0B5-A2020-2021", "C0B5-A2023-2024"], "districts_n": 13, "perennials_included": False},
            "dual_layer_outcome_compatibility": "PASS",
        },
        "yield_area_mapping": {
            "status": "REQUIRES_SOWN_TO_HARVESTED_AREA_MAPPING_GATE",
            "yield_object": "Y_d,c,s_TM_PER_HARVESTED_HA",
            "reference_area_object": "A_d,c,k_SIEMBRA_HA",
            "dimensional_multiplication_unit": "METRIC_TONNE",
            "physical_production_mapping_authorized": False,
            "reason": "SOWN_AREA_AND_HARVESTED_AREA_ARE_NOT_SEMANTICALLY_INTERCHANGEABLE",
        },
        "alternative_timing_to_climate_mapping": {
            "status": "STRUCTURALLY_COMPATIBLE_REQUIRES_SCENARIO_EXPOSURE_BUILD",
            "future_unit": "DISTRICT_CROP_ALTERNATIVE_SCENARIO",
            "use_frozen_alternative_specific_timing_weights": True,
            "generic_t3_rule_authorized": False,
            "pooled_timing_profile_authorized": False,
        },
        "economic_translation": {
            "monetary_dimensional_identity": "PASS_TM_PER_HA_X_HA_X_1000_KG_PER_TM_X_S_PER_KG_EQUALS_S",
            "price_temporal_mapping_status": "REQUIRES_PRICE_MAPPING_GATE",
            "structural_form_status": "STRUCTURAL_FORM_AUTHORIZED",
            "numerical_status": "NUMERICAL_MAPPING_PENDING",
            "nominal_price_comparability_status": "REQUIRES_EXPLICIT_MONETARY_TREATMENT_GATE",
            "invented_price_rules": [],
            "gvp_built": False,
        },
        "aggregation_and_risk": {
            "layer1_five_crop_aggregation_status": "NOT_YET_AUTHORIZED",
            "five_crop_a1_a2_aggregation_status": "NOT_AUTHORIZED",
            "a1_a2_transient_economic_aggregation_structure_status": "STRUCTURAL_SCOPE_COHERENT_NUMERICAL_AGGREGATION_PENDING_YIELD_AREA_PRICE_TIME_GATES",
            "a1_a2_risk_metric_scope": "TRANSIENT_BLOCK_ONLY",
            "common_perennial_random_component_can_be_assumed_to_cancel_in_cvar": False,
        },
        "sample_contracts": samples,
        "temporal_depth_status": "SHORT_T_UNBALANCED_7_CAMPAIGN_TRANSIENT_8_YEAR_PERENNIAL_NO_LONG_PANEL_CLAIM",
        "extreme_year_influence_diagnostic_required": True,
        "maximum_econometric_claim_status": "EMPIRICAL_ASSOCIATION_CLIMATE_RESPONSE_ONLY",
        "out_of_support_control_required": True,
        "scenario_model_separation": {
            "status": "PASS",
            "required_order": [
                "OUTCOME_CONTRACT", "ECONOMETRIC_DESIGN", "MODEL_ESTIMATION", "MODEL_DIAGNOSTICS",
                "EMPIRICAL_SUPPORT_CHARACTERIZATION", "PROSPECTIVE_ENSO_SCENARIO_CONSTRUCTION",
                "PREDICTION_STRESS_TESTING", "ECONOMIC_TRANSLATION", "RISK_METRICS",
            ],
            "scenario_tuning_may_influence_econometric_specification": False,
        },
        "joint_rq_architecture_status": "SUPPORTED_AS_TWO_LINKED_NONMERGED_ANALYTICAL_QUESTIONS",
        "authorization_matrix": authorization,
        "econometric_design_phase_status": "AUTHORIZED_WITH_TARGETED_PRE_ESTIMATION_GATES",
        "targeted_pre_estimation_gates": [
            "TRANSIENT_CAMPAIGN_OUTCOME_MASTER_BUILD_AND_AUDIT",
            "PRIMARY_TRANSIENT_ECONOMETRIC_EXPOSURE_SELECTION",
            "ECONOMETRIC_DESIGN_FREEZE_BEFORE_MODEL_ESTIMATION",
        ],
        "downstream_mapping_gates": [
            "SOWN_TO_HARVESTED_AREA_MAPPING_BEFORE_PHYSICAL_PRODUCTION",
            "PRICE_TEMPORAL_AND_MONETARY_TREATMENT_BEFORE_NUMERICAL_ECONOMIC_TRANSLATION",
            "EMPIRICAL_SUPPORT_ENVELOPE_BEFORE_SCENARIO_PREDICTION",
        ],
        "firewalls": {
            "no_model_fitting": True,
            "no_outcome_driven_architecture_selection": True,
            "no_causal_claim": True,
            "no_enso_scenario": True,
            "no_economic_result": True,
            "no_var_cvar": True,
            "no_alternative_ranking": True,
            "water_model_status": "NOT_AUTHORIZED",
            "continuous_optimization_status": "NOT_AUTHORIZED",
            "land_capacity_inference_used": False,
        },
        "artifact_sha256": dict(artifact_hashes),
        "final_status": FINAL_STATUS,
    }


def build_report(config: dict[str, Any], artifact_hashes: dict[str, str]) -> bytes:
    samples = config["sample_contracts"]
    lines = [
        "# Joint C0 Outcome and Decision Architecture Integration Report", "",
        "## 1. Executive verdict", "",
        f"`JOINT_C0_STATUS={FINAL_STATUS}`. Econometric design is authorized with explicit gates; estimation and downstream calculation remain blocked.", "",
        "## 2. Immutable frozen inputs", "",
        f"C0A sibling `{C0A_FREEZE}` is read only through Git objects and is not merged. C0B6 `{C0B6_FREEZE}` is the exact current frozen base.", "",
        "## 3. C0A outcome semantics", "",
        "PRODUCCION is `METRIC_TONNE`, YIELD_RAW is `TM_PER_HA` of harvested area, COSECHA and SIEMBRA are monthly hectare flows, and PRECIO_CHACRA is farm-gate `S_PER_KG`. VERDE_ACTUAL is an installed-area stock snapshot, not productive stock.", "",
        "## 4. Transient outcome contract", "",
        "Rice and MAD require `TRANSIENT_CAMPAIGN_YIELD_RAW = SUM(PRODUCCION Aug-Jul) / SUM(COSECHA Aug-Jul)`. This contract is coherent and defined but not built. Monthly-yield averaging, summation, maxima, and calendar-year substitution are forbidden.", "",
        "## 5. Perennial outcome contracts", "",
        "Mango, lemon, and banana use district-crop-calendar-year YIELD_RAW in TM/ha. Their valid outcome keys match the frozen calendar-year exposure keys. COSECHA is not installed stock and VERDE_ACTUAL is not productive stock.", "",
        "## 6. Dual analytical layers", "",
        "Layer 1 characterizes five crops without defining a combined portfolio. Layer 2 stress-tests only Rice/MAD alternatives on 13 districts and contains no perennial component.", "",
        "## 7. Yield-area mapping gate", "",
        "A future yield is TM per harvested hectare, while A1/A2 areas are SIEMBRA hectares. Multiplication is dimensionally tonnes but is not yet a certified physical-production mapping. `TRANSIENT_YIELD_AREA_MAPPING_STATUS=REQUIRES_SOWN_TO_HARVESTED_AREA_MAPPING_GATE` before Q = Y x A can be implemented.", "",
        "## 8. Alternative timing and climate", "",
        "Frozen A1/A2 monthly SIEMBRA profiles are compatible with cohort-weighted phenology windows. Future scenario exposure must be district x crop x alternative x scenario using alternative-specific weights. Generic T3 and pooled profiles remain forbidden.", "",
        "## 9. Monetary dimensional identity", "",
        "`TM/ha x ha x 1000 kg/TM x S/kg = S` passes dimensionally. This does not build GVP or authorize a numerical economic result.", "",
        "## 10. Price temporal and nominal-value gate", "",
        "No annual mean, harvest-month price, campaign-weighted price, constant future price, deflator, or normalization rule is frozen. Price mapping and monetary comparability require later explicit gates.", "",
        "## 11. Aggregation and risk firewalls", "",
        "Five-crop Layer 1 aggregation is not yet authorized. Five-crop A1/A2 aggregation is not authorized. `A1_A2_RISK_METRIC_SCOPE=TRANSIENT_BLOCK_ONLY`; a common perennial component cannot be assumed to cancel.", "",
        "## 12. Prospective sample contracts", "",
        "| Crop | Outcome unit | Exposure unit | Periods | Districts | Usable outcomes | Complete grid |", "|---|---|---|---:|---:|---:|---:|",
    ]
    for crop in ("RICE", "MAD", "MANGO", "LEMON", "BANANA"):
        item = samples[crop]
        lines.append(f"| {crop} | {item['outcome_observation_unit']} | {item['climate_exposure_unit']} | {item['time_periods_n']} | {item['districts_n']} | {item['usable_outcome_observations']} | {item['expected_observations_if_complete']} |")
    lines.extend([
        "", "Rice/MAD usable counts are prospective raw campaign-ratio candidates before model-specific exposure complete-case loss. Perennial counts are frozen annual YIELD_RAW keys and match valid exposure keys.", "",
        "## 13. Short-T and extreme years", "",
        "The support is short and unbalanced: seven non-left-truncated transient campaigns and eight perennial calendar years. No long-panel or causal claim is authorized. Years 2017 and 2023 are retained; later influence diagnostics are mandatory.", "",
        "## 14. Identification ceiling", "",
        "The maximum permissible interpretation is `EMPIRICAL_ASSOCIATION_CLIMATE_RESPONSE_ONLY`. Causal effects, structural production functions, and globally transferable biological responses are not authorized.", "",
        "## 15. Empirical support and scenarios", "",
        "An empirical support envelope is required before prospective prediction. Outcome contract, design, estimation, diagnostics, and support characterization must precede ENSO scenario construction.", "",
        "## 16. Joint RQ architecture", "",
        "The architecture supports two linked but nonmerged questions: five-crop phenology-aligned characterization and a 13-district Rice/MAD reference-configuration stress test.", "",
        "## 17. Authorization matrix", "",
        "The accompanying matrix distinguishes design authorization from estimation, economic translation, risk, scenario, water, and optimization authorization. No ambiguous status is used.", "",
        "## 18. Targeted pre-estimation gates", "",
        "Required before fitting Rice/MAD models: transient campaign Outcome Master construction and audit, primary transient econometric exposure selection, and a frozen econometric design. Perennial models may enter design now but cannot be estimated before that design is frozen.", "",
        "## 19. Downstream mapping gates", "",
        "Physical production requires sown-to-harvested-area mapping. Numerical value requires temporal price and monetary treatment. Scenario prediction requires a post-diagnostic empirical support envelope.", "",
        "## 20. No-model-fitting certification", "",
        "Joint C0 creates no coefficient, p-value, standard error, R-squared, model selection, lag optimization, cross-validation, forecast, ENSO scenario, economic result, risk metric, ranking, or optimization result.", "",
        "## 21. Artifact hashes", "",
    ])
    for path, digest in artifact_hashes.items():
        lines.append(f"- `{path}`: `{digest}`")
    lines.extend(["", "## 22. Final authorization", "", "`ECONOMETRIC_DESIGN_PHASE_STATUS=AUTHORIZED_WITH_TARGETED_PRE_ESTIMATION_GATES`. Joint C0 does not authorize estimation."])
    return ("\n".join(lines) + "\n").encode("utf-8")


def build_output_bytes() -> tuple[dict[Path, bytes], dict[str, Any]]:
    conclusions = c0a_conclusions()
    if conclusions["produccion"]["DECISION_VALUE"] != "METRIC_TONNE":
        raise ValueError("C0A PRODUCCION unit changed")
    samples = sample_contracts()
    evidence = build_evidence_rows(samples)
    compatibility = build_compatibility_rows()
    authorization = build_authorization_rows()
    outputs: dict[Path, bytes] = {
        EVIDENCE_PATH: csv_bytes(EVIDENCE_COLUMNS, evidence),
        COMPATIBILITY_PATH: csv_bytes(COMPATIBILITY_COLUMNS, compatibility),
        AUTHORIZATION_PATH: csv_bytes(AUTHORIZATION_COLUMNS, authorization),
    }
    artifact_hashes = {
        path.relative_to(ROOT).as_posix(): sha256_bytes(payload)
        for path, payload in outputs.items()
    }
    config = build_config(samples, authorization, artifact_hashes)
    config_bytes = (json.dumps(config, indent=2, sort_keys=True, ensure_ascii=True) + "\n").encode("utf-8")
    outputs[CONFIG_PATH] = config_bytes
    artifact_hashes[CONFIG_PATH.relative_to(ROOT).as_posix()] = sha256_bytes(config_bytes)
    outputs[REPORT_PATH] = build_report(config, artifact_hashes)
    return outputs, config


def write_outputs() -> None:
    outputs, _ = build_output_bytes()
    for path, payload in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_preflight() -> tuple[list[str], dict[str, Any]]:
    require(git("branch", "--show-current") == EXPECTED_BRANCH, "wrong Joint C0 branch")
    require(git("rev-parse", "HEAD") == C0B6_FREEZE, "wrong C0B6 frozen base")
    ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", C0B6_FREEZE, "HEAD"], cwd=ROOT)
    require(ancestor.returncode == 0, "C0B6 is not an ancestor")
    sibling = subprocess.run(["git", "cat-file", "-e", f"{C0A_FREEZE}^{{commit}}"], cwd=ROOT)
    require(sibling.returncode == 0, "C0A sibling commit is absent")
    merged = subprocess.run(["git", "merge-base", "--is-ancestor", C0A_FREEZE, "HEAD"], cwd=ROOT)
    require(merged.returncode != 0, "C0A was merged or cherry-picked into the Joint C0 base")
    introduced = c0a_introduced_files()
    require(introduced == {path: "A" for path in C0A_FILES}, "wrong C0A introduced-file set")
    for path, expected in C0A_FILES.items():
        require(sha256_bytes(git_bytes("show", f"{C0A_FREEZE}:{path}")) == expected, f"C0A object hash changed: {path}")
        require(not (ROOT / path).exists(), f"C0A file copied into Joint C0: {path}")
    for path, expected in {**C0B6_FILES, **FROZEN_UPSTREAM_HASHES}.items():
        require(sha256_file(ROOT / path) == expected, f"frozen artifact hash changed: {path}")

    tracked = set(filter(None, git("diff", "--name-only").splitlines()))
    staged = set(filter(None, git("diff", "--cached", "--name-only").splitlines()))
    untracked = {line.replace("\\", "/") for line in git("ls-files", "--others", "--exclude-standard").splitlines() if line}
    require(not tracked, f"tracked frozen modifications exist: {sorted(tracked)}")
    require(not staged, f"staged files exist: {sorted(staged)}")
    require(untracked == AUTHORIZED_SCOPE, f"Joint C0 persistent scope mismatch: {sorted(untracked)}")

    expected_outputs, expected_config = build_output_bytes()
    for path, payload in expected_outputs.items():
        require(path.read_bytes() == payload, f"deterministic artifact mismatch: {path.name}")
    for path in (*expected_outputs, SCRIPT_PATH, TEST_PATH):
        raw = path.read_bytes()
        require(not raw.startswith(b"\xef\xbb\xbf"), f"UTF-8 BOM found: {path.name}")
        require(b"\r" not in raw, f"non-LF line ending found: {path.name}")
        require(raw.endswith(b"\n") and not raw.endswith(b"\n\n"), f"final LF mismatch: {path.name}")

    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    require(config == expected_config, "Joint C0 config does not reproduce")
    semantics = config["outcome_semantics"]
    require(semantics["PRODUCCION"]["unit"] == "METRIC_TONNE", "wrong PRODUCCION unit")
    require(semantics["YIELD_RAW"]["unit"] == "TM_PER_HA", "wrong yield unit")
    require(semantics["PRECIO_CHACRA"]["unit"] == "S_PER_KG", "wrong price unit")
    transient = config["transient_outcome_contract"]
    require(transient["formula"] == "SUM(PRODUCCION within Aug-Jul campaign) / SUM(COSECHA within Aug-Jul campaign)", "monthly-yield averaging replaced the campaign outcome")
    require("MEAN_MONTHLY_YIELD" in transient["forbidden_replacements"], "monthly-yield mean firewall missing")
    require(all(item["status"] == "AUTHORIZED_FOR_ECONOMETRIC_DESIGN" for item in config["perennial_outcome_contracts"].values()), "perennial outcome design status changed")
    require(not config["dual_analytical_layers"]["layer_2"]["perennials_included"], "perennials added to A1/A2")
    require(config["aggregation_and_risk"]["five_crop_a1_a2_aggregation_status"] == "NOT_AUTHORIZED", "five-crop A1/A2 aggregation authorized")
    require(not config["aggregation_and_risk"]["common_perennial_random_component_can_be_assumed_to_cancel_in_cvar"], "false perennial CVaR cancellation authorized")
    require(not config["alternative_timing_to_climate_mapping"]["generic_t3_rule_authorized"], "generic T3 rule authorized")
    economic = config["economic_translation"]
    require(economic["price_temporal_mapping_status"] == "REQUIRES_PRICE_MAPPING_GATE", "price rule invented")
    require(not economic["invented_price_rules"], "invented price mapping exists")
    require(not economic["gvp_built"] and economic["numerical_status"] == "NUMERICAL_MAPPING_PENDING", "GVP claimed built")
    require(config["maximum_econometric_claim_status"] == "EMPIRICAL_ASSOCIATION_CLIMATE_RESPONSE_ONLY", "causal effect authorized")
    require(config["scenario_model_separation"]["status"] == "PASS", "scenario/model separation failed")
    require(not config["scenario_model_separation"]["scenario_tuning_may_influence_econometric_specification"], "scenario tuning may select model")
    require(config["out_of_support_control_required"], "out-of-support prediction authorized")
    require(config["yield_area_mapping"]["status"] == "REQUIRES_SOWN_TO_HARVESTED_AREA_MAPPING_GATE", "sown and harvested area silently equated")
    firewalls = config["firewalls"]
    require(firewalls["no_model_fitting"], "model fitting output authorized")
    require(firewalls["water_model_status"] == "NOT_AUTHORIZED", "water model authorized")
    require(firewalls["continuous_optimization_status"] == "NOT_AUTHORIZED", "continuous optimization authorized")
    require(firewalls["no_alternative_ranking"], "A1/A2 ranking authorized")
    require(firewalls["no_enso_scenario"] and firewalls["no_economic_result"] and firewalls["no_var_cvar"], "downstream output created")
    require(config["final_status"] == FINAL_STATUS, "wrong Joint C0 final status")

    for crop, expected in EXPECTED_SAMPLE_FACTS.items():
        observed = config["sample_contracts"][crop]
        require(observed["districts_n"] == expected["districts_n"], f"{crop} district support changed")
        require(observed["usable_outcome_observations"] == expected["usable"], f"{crop} usable observations changed")
        require(observed["expected_observations_if_complete"] == expected["complete_grid"], f"{crop} complete grid changed")
        if "c0b6_usable" in expected:
            require(observed["c0b6_support_usable_observations"] == expected["c0b6_usable"], f"{crop} C0B6 support changed")

    with AUTHORIZATION_PATH.open("r", encoding="utf-8", newline="") as handle:
        authorization = list(csv.DictReader(handle))
    require(authorization == build_authorization_rows(), "authorization matrix changed")
    require(len(authorization) == 17, "authorization matrix row count changed")
    require(all(row["AUTHORIZED_NEXT_PHASE"] in {"TRUE", "FALSE"} and row["FORBIDDEN"] in {"TRUE", "FALSE"} for row in authorization), "ambiguous authorization status")

    script_tree = ast.parse(SCRIPT_PATH.read_text(encoding="utf-8"))
    imported = {
        alias.name.split(".")[0]
        for node in ast.walk(script_tree) if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        (node.module or "").split(".")[0]
        for node in ast.walk(script_tree) if isinstance(node, ast.ImportFrom)
    }
    require(imported.isdisjoint({"statsmodels", "sklearn", "linearmodels"}), "modelling library imported")

    lines = [
        "C0A_IMMUTABILITY_GATE=PASS",
        "C0B6_IMMUTABILITY_GATE=PASS",
        "PERSISTENT_SCOPE_GATE=PASS",
        "TRANSIENT_OUTCOME_CONTRACT_GATE=PASS_DEFINED_NOT_BUILT",
        "PERENNIAL_OUTCOME_CONTRACT_GATE=PASS_FOR_ECONOMETRIC_DESIGN",
        "DUAL_LAYER_OUTCOME_COMPATIBILITY=PASS",
        "NO_MODEL_FITTING_GATE=PASS",
        "NO_OUTCOME_LEAKAGE_GATE=PASS",
        "NO_WATER_MODEL_GATE=PASS",
        "NO_OPTIMIZATION_GATE=PASS",
        f"JOINT_C0_PREFLIGHT={FINAL_STATUS}",
    ]
    return lines, config


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="materialize deterministic Joint C0 artifacts")
    args = parser.parse_args()
    try:
        if args.write:
            write_outputs()
        lines, _ = run_preflight()
        for line in lines:
            print(line)
    except Exception as exc:  # pragma: no cover - terminal diagnostic
        print(f"JOINT_C0_PREFLIGHT=FAIL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
