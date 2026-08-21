"""Read-only preflight for the C0B3 perennial feasibility package."""

from __future__ import annotations

import ast
import csv
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_BRANCH = "phase/c0b3-perennial-feasibility-v1"
EXPECTED_HEAD = "eee4cfae0556135dd7f26e553b29a8437498b6ea"
EXPECTED_SUBJECT = "Freeze C0B2 spatial hydraulic crosswalk"

REGISTRY_PATH = ROOT / "outputs/decision_feasibility/C0B3_PERENNIAL_EVIDENCE_REGISTRY.csv"
ADJUDICATION_PATH = ROOT / "outputs/decision_feasibility/C0B3_CROP_STATE_ADJUDICATION.csv"
BIOLOGY_PATH = ROOT / "outputs/decision_feasibility/C0B3_BIOLOGICAL_PARAMETER_EVIDENCE.csv"
REPORT_PATH = ROOT / "outputs/decision_feasibility/C0B3_PERENNIAL_DECISION_REPORT.md"
CONFIG_PATH = ROOT / "config/decision_ontology/perennial_state_adjudication_v1.json"
SCRIPT_PATH = ROOT / "scripts/c0b3_perennial_preflight.py"
TEST_PATH = ROOT / "tests/test_c0b3_perennial.py"

AUTHORIZED_SCOPE = {
    "outputs/decision_feasibility/C0B3_PERENNIAL_EVIDENCE_REGISTRY.csv",
    "outputs/decision_feasibility/C0B3_CROP_STATE_ADJUDICATION.csv",
    "outputs/decision_feasibility/C0B3_BIOLOGICAL_PARAMETER_EVIDENCE.csv",
    "outputs/decision_feasibility/C0B3_PERENNIAL_DECISION_REPORT.md",
    "config/decision_ontology/perennial_state_adjudication_v1.json",
    "scripts/c0b3_perennial_preflight.py",
    "tests/test_c0b3_perennial.py",
}

C0B2_HASHES = {
    "outputs/decision_feasibility/C0B2_SPATIAL_EVIDENCE_REGISTRY.csv": "0d9e8d1639e5cb5656b3db4b18a4cd730f2848fe5713c65aa4333b618bab47e2",
    "outputs/decision_feasibility/C0B2_AGENCY_UBIGEO_CROSSWALK.csv": "339a619083e28936a772d1e10b827a7077203bffd86be911d88d5557a630902c",
    "outputs/decision_feasibility/C0B2_HYDRAULIC_UBIGEO_CROSSWALK.csv": "86930c8de48a87d428b75c42b9de3d22e5b96c79b0b3363237f4c75608573fa0",
    "outputs/decision_feasibility/C0B2_DISTRICT_SPATIAL_ELIGIBILITY.csv": "a394b4727a7cb8a649ffd82fc704ab5db42d2673fc174a68c20e279146e875ad",
    "outputs/decision_feasibility/C0B2_SPATIAL_HYDRAULIC_REPORT.md": "f1445859718a64ce59e6a677dc333c00e2ac600f4a778d6cc340750136c16b46",
    "scripts/c0b2_spatial_hydraulic_preflight.py": "4d0076ae41b7a191b34df177bf0a9719564adf0b21a9dd75790f6d8fa5c80e77",
    "tests/test_c0b2_spatial_hydraulic.py": "c4e346c92cc3bc16e3da8956e26dd78dfecdd93a2a24282cd9b39dbd307534f8",
}

C0B1_HASHES = {
    "config/decision_ontology/decision_variable_ontology_v1.json": "a8f28394ea1c007413938600623f8e418491c69a9f9351d83d6256122ad4c534",
    "outputs/decision_feasibility/C0B1_ARCHITECTURE_COMPARISON.csv": "314b6a5ef9305b4768a3beb996475c9a86c0365756908db7aada789dbe9508bb",
    "outputs/decision_feasibility/C0B1_DECISION_ONTOLOGY_REPORT.md": "5ac132bdf32d544711d12b0dd7ba86b37e872b6d76198953bdc363590ead379f",
    "scripts/c0b1_decision_ontology_preflight.py": "b94a870af2a946c37e5f7d6581e2518e66ba284d166d45e8d64093a8e8274e60",
    "tests/test_c0b1_decision_ontology.py": "cadbb785cc8780025b43196284842b9ca0c8ac42012968f894ea61304c12484c",
}

TARGET_CODES = {"13010210000", "13010170102", "15010040000"}
TARGET_NAMES = {"MANGO", "LIMON SUTIL", "PLATANOS Y BANANAS"}
SIEA_PRIMARY_PDF_URL = "https://siea.midagri.gob.pe/media/documentos/Lineamientos_Metodologicos_SIEA.pdf"
SIEA_PRIMARY_PDF_SHA256 = "8fe81dcf74acc74803f9fa0c19ace73d54024133a527854e9f95e7d846df2230"
SIEA_LEGAL_PDF_URL = "https://siea.midagri.gob.pe/media/documentos/RM_035-2013-AG.pdf"
SIEA_LEGAL_PDF_SHA256 = "70d173d9a407e0fb205f1cbefa1e149f9a3a9f7167b9834e97c8d0846abca2de"
SIEA_HISTORICAL_URL = "https://siea.midagri.gob.pe/portal/media/attachments/nosotros/gestion/Lineamientos_Metodologicos_SIEA.pdf"
SIEA_PRIVATE_MIRROR_URL = "https://www.normaslegalesonline.pe/imagenes/13/12/2017/1513177801890_RM_194_2016_MINAGRI_2.pdf"
SIEA_PRIVATE_MIRROR_STATUS = "AUXILIARY_RETRIEVAL_COPY_NOT_CANONICAL_NOT_REQUIRED_FOR_SCIENTIFIC_CLAIMS"
RM_0194_2016_ROLE = "INCORPORATES_COMPLETE_AGRICULTURAL_STATISTICAL_SECTOR_REGISTER_INTO_F1"
RM_0194_ROLE_SOURCE_SHA256 = "44b51dfc528a6352c9aa0189601c3c3e7f04c7d17afecab17aa8d5076fb15fb0"
TRANSIENT_CODES = {"14010020000", "14010070000"}
ARCHITECTURE = "ARCH_F_SET3_REQUIRED_ALL_PERENNIALS"

REGISTRY_COLUMNS = [
    "EVIDENCE_ID", "CROP_CODE", "CROP_STD", "EVIDENCE_DOMAIN", "SOURCE_TIER",
    "SOURCE_AUTHORITY", "SOURCE_TITLE", "SOURCE_DATE", "SOURCE_URL",
    "PAGE_OR_SECTION", "RAW_TERM", "STATE_CONCEPT", "UNIT",
    "QUANTITATIVE_VALUE", "VALUE_LOWER", "VALUE_UPPER", "TIME_UNIT",
    "CULTIVAR_OR_SYSTEM", "GEOGRAPHIC_RELEVANCE", "EVIDENCE_STRENGTH",
    "PARAMETER_ADMISSIBILITY", "EXACT_FINDING", "LIMITATION", "NOTES",
]
ADJUDICATION_COLUMNS = [
    "CROP_CODE", "CROP_STD", "CROP_CLASS", "INSTALLED_STOCK_CANDIDATE",
    "INSTALLED_STOCK_STATUS", "INSTALLED_STOCK_STATE", "INSTALLED_STOCK_UNIT",
    "PRODUCTIVE_STOCK_CANDIDATE", "PRODUCTIVE_STOCK_STATUS",
    "ESTABLISHMENT_FLOW_CANDIDATE", "ESTABLISHMENT_FLOW_STATUS",
    "ESTABLISHMENT_FLOW_QUALIFICATION", "STOCK_FLOW_IDENTITY_STATUS",
    "REMOVAL_FLOW_CANDIDATE", "REMOVAL_FLOW_STATUS", "REMOVAL_DERIVABILITY",
    "LAG_STATUS", "LAG_REQUIRED_CONCEPT",
    "NEAR_TERM_ESTABLISHMENT_OUTPUT_RELEVANCE", "P2_OPERATIONAL_STATUS",
    "P3_FALLBACK_REQUIRED", "EVIDENCE_IDS", "CRITICAL_GAPS", "NOTES",
]
BIOLOGY_COLUMNS = [
    "CROP_CODE", "CROP_STD", "PARAMETER_CONCEPT", "SOURCE_VALUE",
    "SOURCE_LOWER", "SOURCE_UPPER", "SOURCE_UNIT", "SOURCE_CONTEXT",
    "CULTIVAR_OR_SYSTEM", "GEOGRAPHIC_RELEVANCE", "EVIDENCE_IDS",
    "PARAMETER_ADMISSIBILITY", "MODEL_VALUE_AUTHORIZED", "AUTHORIZED_VALUE",
    "AUTHORIZED_LOWER", "AUTHORIZED_UPPER", "LIMITATION", "NOTES",
]


def _git(*args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, text=True, encoding="utf-8",
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=check,
    )
    return result.stdout.strip()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def _split_lines(value: str) -> set[str]:
    return {line.replace("\\", "/") for line in value.splitlines() if line}


def run_preflight() -> list[str]:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    # Repository identity and immutable upstream state.
    require(_git("branch", "--show-current") == EXPECTED_BRANCH, "wrong branch")
    require(_git("rev-parse", "HEAD") == EXPECTED_HEAD, "HEAD is not the C0B2 freeze")
    require(_git("show", "-s", "--format=%s", EXPECTED_HEAD) == EXPECTED_SUBJECT, "C0B2 freeze subject mismatch")
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", EXPECTED_HEAD, "HEAD"],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    require(ancestor.returncode == 0, "C0B2 freeze is not an ancestor")

    for relative, expected_hash in {**C0B1_HASHES, **C0B2_HASHES}.items():
        path = ROOT / relative
        require(path.is_file(), f"missing frozen file: {relative}")
        if path.is_file():
            require(_sha256(path) == expected_hash, f"frozen hash mismatch: {relative}")

    tracked_changes = _split_lines(_git("diff", "--name-only"))
    tracked_changes |= _split_lines(_git("diff", "--cached", "--name-only"))
    untracked = _split_lines(_git("ls-files", "--others", "--exclude-standard"))
    require(not tracked_changes, f"tracked files changed: {sorted(tracked_changes)}")
    require(untracked == AUTHORIZED_SCOPE, f"persistent scope mismatch: {sorted(untracked)}")
    require(not any(path.lower().endswith(".pdf") for path in untracked), "persistent PDF created")

    required_paths = [REGISTRY_PATH, ADJUDICATION_PATH, BIOLOGY_PATH, REPORT_PATH, CONFIG_PATH, SCRIPT_PATH, TEST_PATH]
    for path in required_paths:
        require(path.is_file(), f"missing C0B3 file: {path.relative_to(ROOT)}")
    if any(not path.is_file() for path in required_paths):
        return errors

    registry_columns, registry = _read_csv(REGISTRY_PATH)
    adjudication_columns, adjudications = _read_csv(ADJUDICATION_PATH)
    biology_columns, biology = _read_csv(BIOLOGY_PATH)
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    report = REPORT_PATH.read_text(encoding="utf-8")

    require(registry_columns == REGISTRY_COLUMNS, "evidence registry schema mismatch")
    require(adjudication_columns == ADJUDICATION_COLUMNS, "crop adjudication schema mismatch")
    require(biology_columns == BIOLOGY_COLUMNS, "biological evidence schema mismatch")
    require(len(adjudications) == 3, "crop adjudication must have exactly three rows")
    require({row["CROP_CODE"] for row in adjudications} == TARGET_CODES, "target crop codes mismatch")
    require({row["CROP_STD"] for row in adjudications} == TARGET_NAMES, "target crop names mismatch")
    require(not ({row["CROP_CODE"] for row in adjudications} & TRANSIENT_CODES), "transient crop ontology modified")

    evidence_ids = [row["EVIDENCE_ID"] for row in registry]
    require(len(evidence_ids) == len(set(evidence_ids)), "duplicate evidence IDs")
    evidence_set = set(evidence_ids)
    referenced_ids: set[str] = set()
    for row in [*adjudications, *biology]:
        referenced_ids.update(value for value in row["EVIDENCE_IDS"].split(";") if value)
    require(referenced_ids <= evidence_set, f"unresolved evidence IDs: {sorted(referenced_ids - evidence_set)}")

    verde_rows = [row for row in registry if row["RAW_TERM"] == "VERDE_ACTUAL"]
    require(len(verde_rows) == 3, "VERDE_ACTUAL requires one evidence row per crop")
    require(all(not row["UNIT"] for row in verde_rows), "dictionary unit cell no longer represented faithfully")
    methodology = {row["EVIDENCE_ID"]: row for row in registry}
    for evidence_id in ("C0B3-E026", "C0B3-E027", "C0B3-E028", "C0B3-E029"):
        require(evidence_id in methodology, f"official SIEA evidence missing: {evidence_id}")
    if "C0B3-E026" in methodology:
        require(methodology["C0B3-E026"]["UNIT"] == "ha", "SIEA hectare certification missing")
        require(methodology["C0B3-E026"]["SOURCE_TIER"] == "P1", "SIEA methodology is not primary evidence")
        require(methodology["C0B3-E026"]["SOURCE_URL"] == SIEA_PRIMARY_PDF_URL, "official SIEA primary PDF locator missing")
        require(f"PRIMARY_PDF_SHA256={SIEA_PRIMARY_PDF_SHA256}" in methodology["C0B3-E026"]["NOTES"], "SIEA registry primary PDF hash missing")
        require("APPROVING_NORM=RESOLUCION_MINISTERIAL_N_0035-2013-AG" in methodology["C0B3-E026"]["NOTES"], "SIEA registry approving norm missing")
        require("APPROVING_NORM_ROLE=APPROVES_SIEA_METHODOLOGICAL_GUIDELINES" in methodology["C0B3-E026"]["NOTES"], "SIEA registry approving norm role missing")
        require(f"RM_0194_2016_ROLE={RM_0194_2016_ROLE}" in methodology["C0B3-E026"]["NOTES"], "RM 0194 role missing from registry")
        require(all(row["SOURCE_URL"] == SIEA_PRIMARY_PDF_URL for row in methodology.values() if row["EVIDENCE_ID"] in {"C0B3-E026", "C0B3-E027", "C0B3-E028", "C0B3-E029"}), "SIEA evidence does not use the official primary PDF")
        require(all(f"PRIMARY_PDF_SHA256={SIEA_PRIMARY_PDF_SHA256}" in row["NOTES"] for row in methodology.values() if row["EVIDENCE_ID"] in {"C0B3-E026", "C0B3-E027", "C0B3-E028", "C0B3-E029"}), "SIEA primary hash not propagated")
        require(all("normaslegalesonline.pe" not in row["SOURCE_URL"] for row in methodology.values() if row["EVIDENCE_ID"] in {"C0B3-E026", "C0B3-E027", "C0B3-E028", "C0B3-E029"}), "private mirror remains canonical in registry")

    verde = config["variable_adjudication"]["VERDE_ACTUAL"]
    require(verde["source_semantics"] == "NUMERIC_MONTHLY_TOTAL_AREA_OF_INSTALLED_CROPS", "VERDE_ACTUAL semantics unresolved")
    require(verde["unit"] == "ha", "VERDE_ACTUAL unit unresolved")
    require(verde["status"] == "INSTALLED_STOCK_CERTIFIED", "VERDE_ACTUAL installed-stock status unresolved")
    require(verde["may_be_used_as_numeric_installed_hectares"], "VERDE_ACTUAL hectares not authorized")
    require(all(row["INSTALLED_STOCK_STATUS"] == "OBSERVED_AND_UNIT_CERTIFIED" for row in adjudications), "installed stock is not observed and unit-certified")
    require(all(row["INSTALLED_STOCK_UNIT"] == "ha" for row in adjudications), "crop installed-stock unit mismatch")
    expected_states = {
        "MANGO": "INSTALLED_PERENNIAL_STOCK_AREA",
        "LIMON SUTIL": "INSTALLED_PERENNIAL_STOCK_AREA",
        "PLATANOS Y BANANAS": "CONTINUOUS_SEMIPERMANENT_INSTALLED_STAND_AREA",
    }
    require(all(row["INSTALLED_STOCK_STATE"] == expected_states[row["CROP_STD"]] for row in adjudications), "crop installed-stock ontology mismatch")

    cosecha = config["variable_adjudication"]["COSECHA"]
    require(cosecha["source_semantics"] == "HARVEST_FLOW_AREA", "COSECHA is not frozen as harvest-flow area")
    require(cosecha["unit"] == "ha", "COSECHA unit mismatch")
    require(not cosecha["may_equal_installed_stock_automatically"], "COSECHA promoted to installed stock")
    require(not cosecha["may_equal_productive_stock_automatically"], "COSECHA promoted to productive stock")
    require(all(row["PRODUCTIVE_STOCK_STATUS"] == "HARVESTED_AREA_PROXY_ONLY" for row in adjudications), "harvested area promoted to productive stock")
    require(all(row["INSTALLED_STOCK_CANDIDATE"] != row["PRODUCTIVE_STOCK_CANDIDATE"] for row in adjudications), "harvested area equated to installed stock")

    siembra = config["variable_adjudication"]["SIEMBRA"]
    require(siembra["source_semantics"] == "MONTHLY_GROSS_AREA_INSTALLED_BY_SOWING_OR_TRANSPLANTING", "SIEMBRA semantics underclassified")
    require(siembra["unit"] == "ha", "SIEMBRA unit mismatch")
    require(siembra["gross_establishment_observed"], "gross establishment is not observed")
    require(not siembra["is_total_stock"], "SIEMBRA treated as total stock")
    require(not siembra["is_campaign_cumulative_stock"], "SIEMBRA treated as campaign cumulative stock")
    require(not siembra["is_net_stock_expansion"], "SIEMBRA treated as net expansion")
    require(all(row["ESTABLISHMENT_FLOW_STATUS"] == "DIRECTLY_OBSERVED" for row in adjudications), "Mango or lemon SIEMBRA remains proxy-only")
    banana = next(row for row in adjudications if row["CROP_STD"] == "PLATANOS Y BANANAS")
    require("NOT_INTERNAL_SUCKER_SUCCESSION" in banana["ESTABLISHMENT_FLOW_QUALIFICATION"], "banana SIEMBRA interpreted as internal sucker succession")
    require(not siembra["banana_internal_sucker_succession_observed"], "banana internal sucker succession treated as SIEMBRA")

    stock_difference = config["variable_adjudication"]["stock_difference"]
    require(stock_difference["status"] == "APPROXIMATE_ONLY", "stock-flow identity overclassified")
    require(stock_difference["accounting_residual_diagnostic_only"], "stock residual not restricted to diagnostic use")
    require(not stock_difference["may_equal_observed_removal"], "stock residual treated as observed removal")
    require(not stock_difference["model_authorized"], "stock residual authorized for model")
    require(all(row["STOCK_FLOW_IDENTITY_STATUS"] == "APPROXIMATE_ONLY" for row in adjudications), "crop stock-flow identity mismatch")
    require(all(row["REMOVAL_FLOW_STATUS"] == "NOT_OBSERVED" for row in adjudications), "removal flow silently derived")
    require(all(row["REMOVAL_DERIVABILITY"] == "NOT_DERIVABLE_WITHOUT_ASSUMPTION" for row in adjudications), "removal derivability overclassified")
    require(not config["removal_adjudication"]["zero_removal_allowed"], "removal set to zero")
    require(not config["frozen_upstream"]["new_establishment_not_immediate_productive_stock"] is False, "immediate productivity assumed")

    authorized = [row for row in biology if row["MODEL_VALUE_AUTHORIZED"] == "TRUE"]
    require(len(biology) == 9, "biological evidence row count changed")
    for row in authorized:
        require(row["PARAMETER_ADMISSIBILITY"] == "MODEL_ADMISSIBLE", f"unauthorized admissibility: {row['PARAMETER_CONCEPT']}")
        require(bool(row["EVIDENCE_IDS"]), f"authorized value lacks provenance: {row['PARAMETER_CONCEPT']}")
        require(any(row[key] for key in ("AUTHORIZED_VALUE", "AUTHORIZED_LOWER", "AUTHORIZED_UPPER")), f"authorized row lacks value: {row['PARAMETER_CONCEPT']}")
    require(not authorized, "C0B3 unexpectedly authorizes biological model values")
    require(config["biological_parameter_policy"]["evidence_rows"] == 9, "JSON biological evidence count mismatch")
    require(config["biological_parameter_policy"]["model_authorized_values"] == 0, "JSON authorizes biological model values")
    require(all(not row[key] for row in biology for key in ("AUTHORIZED_VALUE", "AUTHORIZED_LOWER", "AUTHORIZED_UPPER")), "authorized value fields must be blank")
    require(not config["biological_parameter_policy"]["midpoint_inference_allowed"], "midpoint inference enabled")
    require(not config["biological_parameter_policy"]["cultivar_or_system_generalization_allowed"], "cultivar generalization enabled")
    require(not config["biological_parameter_policy"]["first_harvest_equals_economically_productive_stock"], "first harvest promoted to productive stock")
    require(any("Kent" in row["CULTIVAR_OR_SYSTEM"] for row in registry if row["CROP_STD"] == "MANGO"), "Kent specificity missing")

    banana = next(row for row in adjudications if row["CROP_STD"] == "PLATANOS Y BANANAS")
    require(banana["CROP_CLASS"] == "SEMIPERMANENT_CONTINUOUS_STAND_WITH_MOTHER_SUCKER_SUCCESSION", "banana ontology forced to woody orchard")
    banana_ontology = config["banana_state_ontology"]
    require(banana_ontology["status"] == "CONTINUOUS_MOTHER_DAUGHTER_GRANDDAUGHTER_STAND", "banana succession ontology missing")
    require(banana_ontology["woody_perennial_ontology"] == "REJECTED", "banana woody-perennial ontology not rejected")
    require(not banana_ontology["internal_sucker_succession_is_new_district_area_establishment"], "banana sucker succession treated as district-area establishment")
    require(all(row["LAG_STATUS"] == "CONTEXT_ONLY" for row in adjudications), "maturity status exceeds evidence")
    require(all(row["NEAR_TERM_ESTABLISHMENT_OUTPUT_RELEVANCE"] == "UNRESOLVED" for row in adjudications), "near-term output relevance invented")
    horizon = config["decision_horizon"]
    require(horizon["status"] == "QUALITATIVELY_NEAR_TERM_ONLY", "decision horizon status changed")
    require(not horizon["numeric_horizon_frozen"], "numeric near-term horizon invented")
    require(not horizon["lag_comparison_authorized"], "qualitative horizon compared with context-only lag")

    expected_diagnostics = {
        "MANGO": (4111, 4111, 0, 4076, 3, 32, -100, 40, -0.155254),
        "LIMON SUTIL": (4730, 4730, 0, 4699, 0, 31, -683, 0, -0.274841),
        "PLATANOS Y BANANAS": (5576, 5574, 2, 5481, 2, 91, -470, 50, -0.751525),
    }
    diagnostics = config["empirical_identity_diagnostics"]
    require(diagnostics["admissibility"] == "ACCOUNTING_RESIDUAL_DIAGNOSTIC_ONLY_NOT_MODEL_AUTHORIZED", "identity residual admissibility mismatch")
    diagnostic_keys = ("total_candidate_pairs", "nonmissing_analyzable_pairs", "missing_pairs", "exact_identity_pairs", "positive", "negative", "minimum", "maximum", "mean")
    for crop, expected in expected_diagnostics.items():
        require(tuple(diagnostics[crop][key] for key in diagnostic_keys) == expected, f"identity diagnostic mismatch: {crop}")
        require(diagnostics[crop]["total_candidate_pairs"] == diagnostics[crop]["nonmissing_analyzable_pairs"] + diagnostics[crop]["missing_pairs"], f"diagnostic pair accounting mismatch: {crop}")
        require(diagnostics[crop]["nonmissing_analyzable_pairs"] == diagnostics[crop]["exact_identity_pairs"] + diagnostics[crop]["positive"] + diagnostics[crop]["negative"], f"diagnostic residual denominator mismatch: {crop}")

    supported = [row for row in adjudications if row["P2_OPERATIONAL_STATUS"].startswith("SUPPORTED")]
    for row in supported:
        require(row["INSTALLED_STOCK_STATUS"] == "OBSERVED_AND_UNIT_CERTIFIED", f"P2 lacks installed stock: {row['CROP_STD']}")
        require(row["PRODUCTIVE_STOCK_STATUS"] in {"DIRECTLY_OBSERVED", "DERIVABLE_WITH_CERTIFIED_RULE", "NOT_REQUIRED_FOR_NEAR_TERM_MODEL"}, f"P2 lacks productive stock: {row['CROP_STD']}")
        require(row["ESTABLISHMENT_FLOW_STATUS"] in {"DIRECTLY_OBSERVED", "DERIVABLE_FROM_STOCK_IDENTITY", "BOUNDED_BY_OFFICIAL_EVIDENCE"}, f"P2 lacks establishment: {row['CROP_STD']}")
        require(row["REMOVAL_FLOW_STATUS"] in {"DIRECTLY_OBSERVED", "DERIVABLE_WITH_CERTIFIED_IDENTITY", "BOUNDED_BY_OFFICIAL_EVIDENCE"}, f"P2 lacks removal: {row['CROP_STD']}")
        require(row["LAG_STATUS"] in {"MODEL_ADMISSIBLE_EXACT", "MODEL_ADMISSIBLE_RANGE", "NOT_REQUIRED"}, f"P2 lacks lag: {row['CROP_STD']}")
    require(all(row["P2_OPERATIONAL_STATUS"] == "NOT_SUPPORTED_USE_P3" for row in adjudications), "crop P2 verdict is not deterministic")
    matrix = config["p2_necessary_condition_matrix"]
    for crop in TARGET_NAMES:
        require(matrix[crop]["installed_stock"] == "PASS", f"installed-stock gate failed: {crop}")
        require(matrix[crop]["unit"] == "PASS", f"unit gate failed: {crop}")
        expected_establishment = "PASS_WITH_BIOLOGICAL_QUALIFICATION" if crop == "PLATANOS Y BANANAS" else "PASS"
        require(matrix[crop]["gross_establishment"] == expected_establishment, f"establishment gate mismatch: {crop}")
        require(matrix[crop]["productive_stock"] == "FAIL_PROXY_ONLY", f"productive-stock gate weakened: {crop}")
        require(matrix[crop]["removal_replacement"] == "FAIL_NOT_OBSERVED", f"removal gate weakened: {crop}")
        require(matrix[crop]["model_admissible_productivity_lag"] == "FAIL_CONTEXT_ONLY", f"lag gate weakened: {crop}")
        require(matrix[crop]["numeric_horizon_compatibility"] == "UNRESOLVED", f"horizon gate weakened: {crop}")
        require(matrix[crop]["p2"] == "NOT_SUPPORTED_USE_P3", f"P2 supported from incomplete evidence: {crop}")
    require(all(row["P3_FALLBACK_REQUIRED"] == "TRUE" for row in adjudications), "P3 fallback missing")
    require(config["architecture_adjudication"] == ARCHITECTURE, "architecture verdict mismatch")
    require(set(config["p3_required_crops"]) == TARGET_NAMES, "P3 crop set mismatch")
    require(config["architecture_status"]["ARCH_E_SET2_STATUS"] == "NOT_SUPPORTED", "ARCH_E status mismatch")
    require(config["architecture_status"]["ARCH_F_SET3_STATUS"] == "REQUIRED", "ARCH_F status mismatch")
    require(config["p2_failure_independent_of_current_horizon"] is True, "P2 failure made dependent on numeric horizon")
    rationale = config["architecture_rationale"]
    for token in ("INSTALLED_STOCK_AND_GROSS_ESTABLISHMENT_ARE_OBSERVED", "PRODUCTIVE_STATE", "REMOVAL_REPLACEMENT", "MODEL_ADMISSIBLE_LAG", "NUMERIC_HORIZON"):
        require(token in rationale, f"architecture rationale missing: {token}")
    p3 = config["p3_interpretation"]
    require(p3["resolution"] == "P3_FIXED_STOCK_NEAR_TERM_HORIZON", "P3 fixed-stock resolution changed")
    require(p3["perennial_decision_endogeneity"] == "EXOGENOUS_FIXED_WITHIN_CURRENT_NEAR_TERM_ARCHITECTURE", "P3 perennial endogeneity changed")
    require(p3["future_time_varying_exogenous_perennial_path_status"] == "NOT_YET_AUTHORIZED", "future time-varying exogenous perennial path authorized")
    require(p3["perennial_installed_stocks"] == "OBSERVED_BUT_EXOGENOUS_TO_NEAR_TERM_OPTIMIZER", "P3 does not preserve observed stock")
    require(p3["historical_characterization_authorized"], "historical stock characterization disabled")
    require(p3["district_crop_baseline_measurement_authorized"], "district/crop baseline measurement disabled")
    require(p3["baseline_initialization_authorized"], "baseline initialization disabled")
    require(p3["descriptive_historical_stock_trajectories_authorized"], "descriptive historical stock trajectories disabled")
    require(not p3["historical_observed_variation_authorizes_future_modeled_variation"], "historical variation promoted to future modeled variation")
    require(not p3["scenario_specific_perennial_area_reallocation_authorized"], "scenario-specific perennial area reallocation authorized")
    require(not p3["optimizer_chosen_perennial_adjustment_authorized"], "optimizer-chosen perennial adjustment authorized")
    require(not p3["endogenous_perennial_establishment_authorized"], "endogenous perennial establishment authorized")
    require(not p3["endogenous_perennial_removal_authorized"], "endogenous perennial removal authorized")
    require(not p3["exogenous_means_unobserved"], "P3 describes exogenous stock as unobserved")
    require(not p3["arbitrary_optimizer_area_adjustment_authorized"], "P3 authorizes arbitrary perennial adjustment")

    headings = [f"## {number}. {title}" for number, title in enumerate([
        "Executive verdict", "Frozen C0B1/C0B2 identity", "Why perennial stock-flow ontology matters",
        "Source hierarchy", "Dataset variable semantics", "VERDE_ACTUAL adjudication",
        "Mango state architecture", "Limón Sutil state architecture", "Plátanos/Bananas state architecture",
        "Installed-stock evidence", "Productive-stock evidence", "Establishment evidence",
        "Removal/replacement evidence", "Maturity/productivity lag", "Near-term ENSO relevance",
        "Crop-specific P2 verdicts", "P3 fallback implications", "Architecture adjudication",
        "Forbidden interpretations", "Remaining gaps", "Final C0B3 verdict",
    ], start=1)]
    require(all(heading in report for heading in headings), "report section missing")
    for token in (
        "VERDE_ACTUAL_STATUS=INSTALLED_STOCK_CERTIFIED",
        "VERDE_ACTUAL_UNIT=ha",
        "STOCK_FLOW_IDENTITY_STATUS=APPROXIMATE_ONLY",
        "ACCOUNTING_RESIDUAL_DIAGNOSTIC",
        "MODEL_AUTHORIZED_BIOLOGICAL_PARAMETERS_N=0",
        "DECISION_HORIZON_STATUS=QUALITATIVELY_NEAR_TERM_ONLY",
        "P3_RESOLUTION=P3_FIXED_STOCK_NEAR_TERM_HORIZON",
        "PERENNIAL_DECISION_ENDOGENEITY=EXOGENOUS_FIXED_WITHIN_CURRENT_NEAR_TERM_ARCHITECTURE",
        "FUTURE_TIME_VARYING_EXOGENOUS_PERENNIAL_PATH_STATUS=NOT_YET_AUTHORIZED",
        "P2_FAILURE_INDEPENDENT_OF_CURRENT_HORIZON=TRUE",
        "SIEA_PRIMARY_SOURCE_AUTHORITY=MIDAGRI_SIEA",
        f"SIEA_PRIMARY_PDF_SHA256={SIEA_PRIMARY_PDF_SHA256}",
        "SIEA_APPROVING_NORM=RESOLUCION_MINISTERIAL_N_0035-2013-AG",
        "SIEA_APPROVING_NORM_ROLE=APPROVES_SIEA_METHODOLOGICAL_GUIDELINES",
        "SIEA_LEGAL_VS_METHODOLOGICAL_SOURCE_FIREWALL=PASS_DISTINCT_SOURCE_ROLES_RECORDED",
        f"RM_0194-2016-MINAGRI` does not approve the original guidelines",
        "Total candidate pairs",
        "Nonmissing analyzable pairs",
        "Exogenous does not mean unobserved",
        "Architecture F survives",
    ):
        require(token in report, f"report semantic correction missing: {token}")
    require("architecture f is selected because installed stock is unobserved" not in report.lower(), "report retains false unobserved-stock rationale")

    provenance = config["official_source_provenance"]
    require(provenance["data_dictionary"]["sha256"] == "9df8aedf987a7a882d265ffc629d105f8058a5208738d5dcd1b213b30d347ce0", "dictionary provenance hash mismatch")
    require(provenance["metadata"]["sha256"] == "a66ede624b8d2f502df65620c84233dd04a9ebcc29ae9969c38e2272ec812ea7", "metadata provenance hash mismatch")
    siea = provenance["siea_methodology"]
    require(siea["evidence_domain"] == "VARIABLE_AND_STATE_SEMANTICS_ONLY_NOT_BIOLOGICAL_PARAMETER", "SIEA evidence promoted beyond semantics")
    require(siea["primary_source_authority"] == "MIDAGRI_SIEA", "SIEA primary authority mismatch")
    require(siea["primary_source_title"] == "Lineamientos Metodológicos de la Actividad Estadística del Sistema Integrado de Estadística Agraria - SIEA", "SIEA primary title mismatch")
    require(siea["primary_requested_url"] == SIEA_PRIMARY_PDF_URL, "SIEA requested primary locator mismatch")
    require(siea["primary_final_resolved_url"].startswith("https://siea.midagri.gob.pe/"), "SIEA final primary locator is not official")
    require("normaslegalesonline.pe" not in siea["primary_requested_url"] + siea["primary_final_resolved_url"], "private mirror used as canonical SIEA source")
    require(siea["primary_http_status"] == "HTTP_200_APPLICATION_PDF", "SIEA primary retrieval did not yield a PDF")
    require(siea["primary_pdf_sha256"] == SIEA_PRIMARY_PDF_SHA256, "SIEA primary PDF hash mismatch")
    require(re.fullmatch(r"[0-9a-f]{64}", siea["primary_pdf_sha256"]) is not None, "SIEA primary PDF hash is not 64-hex")
    require(siea["primary_pdf_pages"] == 491, "SIEA primary PDF page count mismatch")
    require(siea["official_discovery_page_url"].startswith("https://siea.midagri.gob.pe/"), "official SIEA discovery page missing")
    historical = siea["historical_official_locator"]
    require(historical["requested_url"] == SIEA_HISTORICAL_URL, "historical SIEA locator mismatch")
    require(historical["status"] == "OBSOLETE_REDIRECTS_TO_OFFICIAL_SIEA_HOME_HTML_NOT_PDF", "historical non-PDF redirect not disclosed")
    require(historical["canonical_primary_source"] is False, "obsolete SIEA locator remains canonical")
    definitions = siea["methodological_definition_source"]
    require(definitions["document_role"] == "METHODOLOGICAL_DEFINITION_SOURCE", "methodological definition source role missing")
    require(definitions["pages"] == "61-65", "SIEA methodological definition pages mismatch")
    require(definitions["verde_actual_pages"] == "61-62_AND_65", "VERDE_ACTUAL methodological pages missing")
    require(definitions["siembra_page"] == "63", "SIEMBRA methodological page missing")
    require(definitions["cosecha_page"] == "64", "COSECHA methodological page missing")
    require(definitions["definitions_verified_in_primary_pdf"] is True, "SIEA definitions not verified in primary PDF")
    legal = siea["legal_approval_source"]
    require(legal["document_role"] == "LEGAL_APPROVAL_SOURCE", "legal approval source role missing")
    require(legal["source_authority"] == "MIDAGRI_SIEA", "legal approval source is not official MIDAGRI/SIEA")
    require(legal["requested_url"] == SIEA_LEGAL_PDF_URL, "legal approval locator mismatch")
    require(legal["final_resolved_url"].startswith("https://siea.midagri.gob.pe/"), "legal approval final locator is not official")
    require(legal["http_status"] == "HTTP_200_APPLICATION_PDF", "legal approval retrieval did not yield a PDF")
    require(legal["pdf_sha256"] == SIEA_LEGAL_PDF_SHA256, "legal approval PDF hash mismatch")
    require(re.fullmatch(r"[0-9a-f]{64}", legal["pdf_sha256"]) is not None, "legal approval PDF hash is not 64-hex")
    require(legal["approving_norm"] == "RESOLUCION_MINISTERIAL_N_0035-2013-AG", "SIEA approving norm mismatch")
    require(legal["approving_norm_date"] == "2013-02-01", "SIEA approving norm date mismatch")
    require(legal["approving_norm_role"] == "APPROVES_SIEA_METHODOLOGICAL_GUIDELINES", "SIEA approving norm role mismatch")
    rm_0194 = siea["rm_0194_2016"]
    require(rm_0194["role"] == RM_0194_2016_ROLE, "RM 0194 role conflated with original approval")
    require(rm_0194["is_original_guidelines_approving_norm"] is False, "RM 0194 described as original approving norm")
    require(rm_0194["is_primary_methodological_source"] is False, "RM 0194 described as primary methodological source")
    require(rm_0194["authentication_source_url"].startswith("https://www.leyes.congreso.gob.pe/"), "RM 0194 official role source missing")
    require(rm_0194["authentication_source_sha256"] == RM_0194_ROLE_SOURCE_SHA256, "RM 0194 role source hash mismatch")
    private_mirror = siea["auxiliary_private_mirror"]
    require(private_mirror["status"] == SIEA_PRIVATE_MIRROR_STATUS, "private mirror status exceeds auxiliary role")
    require(private_mirror["url"] == SIEA_PRIVATE_MIRROR_URL, "private mirror locator mismatch")
    require(private_mirror["not_primary_source"] is True, "private mirror marked as primary")
    require(private_mirror["no_scientific_claim_depends_solely_on_copy"] is True, "scientific claim depends solely on private mirror")
    require(siea["legal_vs_methodological_source_firewall"] == "PASS_DISTINCT_SOURCE_ROLES_RECORDED", "legal and methodological source roles conflated")

    require("VERDE_ACTUAL_UNIT_UNRESOLVED" not in config["critical_gaps"], "resolved VERDE_ACTUAL unit remains a critical gap")
    require("ESTABLISHMENT_NOT_IDENTIFIED_AS_STOCK_ENTRY" not in config["critical_gaps"], "resolved gross establishment remains a critical gap")
    firewalls = config["firewalls"]
    require(firewalls["verde_actual_unit_certified_by_official_methodology"], "official hectare certification missing")
    require(not firewalls["stock_residual_equals_observed_removal_assumed"], "stock residual promoted to removal")
    require(not firewalls["removal_set_to_zero"], "removal set to zero")
    require(not firewalls["numeric_near_term_horizon_invented"], "numeric horizon invented")
    require(not firewalls["p2_supported_from_installed_stock_and_establishment_only"], "P2 supported from incomplete gates")
    require(not firewalls["p3_described_as_unobserved_stock"], "P3 described as unobserved stock")

    imported_modules: set[str] = set()
    for path in (SCRIPT_PATH, TEST_PATH):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.add(node.module)
    forbidden_modules = {"pulp", "cvxpy", "pyomo", "scipy.optimize"}
    require(not any(module in forbidden_modules or module.startswith("scipy.optimize.") for module in imported_modules), "optimizer implementation detected")
    require(config["authorizations"]["optimizer"] is False, "optimizer authorized")
    require(config["authorizations"]["water_model"] is False, "water model authorized")
    require(config["authorizations"]["water_hard_constraint"] is False, "water hard constraint authorized")
    require(config["final_status"] == "PASS_FOR_FINAL_NOTARIAL_C0B3_FREEZE_AUDIT", "final C0B3 status mismatch")
    return errors


def main() -> int:
    errors = run_preflight()
    if errors:
        for error in errors:
            print(f"C0B3_PREFLIGHT_ERROR={error}")
        print("C0B2_IMMUTABILITY_GATE=FAIL")
        print("PERSISTENT_SCOPE_GATE=FAIL")
        print("NO_INVENTED_PARAMETER_GATE=FAIL")
        print("NO_OPTIMIZATION_GATE=FAIL")
        print("NO_WATER_MODEL_GATE=FAIL")
        print("C0B3_PREFLIGHT=FAIL")
        return 1

    print("C0B2_IMMUTABILITY_GATE=PASS")
    print("PERSISTENT_SCOPE_GATE=PASS")
    print("NO_INVENTED_PARAMETER_GATE=PASS")
    print("NO_OPTIMIZATION_GATE=PASS")
    print("NO_WATER_MODEL_GATE=PASS")
    print("C0B3_PREFLIGHT=PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
