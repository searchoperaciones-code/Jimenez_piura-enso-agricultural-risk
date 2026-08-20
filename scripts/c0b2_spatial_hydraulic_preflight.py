"""Read-only preflight for the C0B2RD spatial-hydraulic correction package."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_BRANCH = "phase/c0b-decision-feasibility-v1"
EXPECTED_HEAD = "59e0dacd432998682713fbfca6347de33111012e"
EXPECTED_PARENT = "77526c9cb41b20062a5fa61a95167af5859295f2"
EXPECTED_COMMIT_MESSAGE = "Freeze C0B1 decision variable ontology"

REGISTRY_PATH = ROOT / "outputs/decision_feasibility/C0B2_SPATIAL_EVIDENCE_REGISTRY.csv"
AGENCY_PATH = ROOT / "outputs/decision_feasibility/C0B2_AGENCY_UBIGEO_CROSSWALK.csv"
HYDRAULIC_PATH = ROOT / "outputs/decision_feasibility/C0B2_HYDRAULIC_UBIGEO_CROSSWALK.csv"
ELIGIBILITY_PATH = ROOT / "outputs/decision_feasibility/C0B2_DISTRICT_SPATIAL_ELIGIBILITY.csv"
REPORT_PATH = ROOT / "outputs/decision_feasibility/C0B2_SPATIAL_HYDRAULIC_REPORT.md"
SCRIPT_PATH = ROOT / "scripts/c0b2_spatial_hydraulic_preflight.py"
TEST_PATH = ROOT / "tests/test_c0b2_spatial_hydraulic.py"
PANEL_PATH = ROOT / "data/processed/panel_master.csv"
LAND_PATH = ROOT / "data/processed/land_physical.csv"

AUTHORIZED_SCOPE = {
    "outputs/decision_feasibility/C0B2_SPATIAL_EVIDENCE_REGISTRY.csv",
    "outputs/decision_feasibility/C0B2_AGENCY_UBIGEO_CROSSWALK.csv",
    "outputs/decision_feasibility/C0B2_HYDRAULIC_UBIGEO_CROSSWALK.csv",
    "outputs/decision_feasibility/C0B2_DISTRICT_SPATIAL_ELIGIBILITY.csv",
    "outputs/decision_feasibility/C0B2_SPATIAL_HYDRAULIC_REPORT.md",
    "scripts/c0b2_spatial_hydraulic_preflight.py",
    "tests/test_c0b2_spatial_hydraulic.py",
}

C0B0_HASHES = {
    "outputs/decision_feasibility/C0B_EVIDENCE_REGISTRY.csv": "d634b2ab95824cf25117d49a2f0443444fc1aa0fac4d08ad584fcd2dc15918d1",
    "outputs/decision_feasibility/C0B_CONSTRAINT_CANDIDATES.csv": "473563a6fafbdd907e572214ffdf4514e85edba62905454932ac064836d68447",
    "outputs/decision_feasibility/C0B_DECISION_FEASIBILITY_REPORT.md": "1bedb367e9632b317fd138c222b2be4f05f0162877b3c1005e8b923aadf54f13",
    "scripts/c0b_decision_feasibility_preflight.py": "7c277bbd627d02a8dbe6931df655e7cd13b52158997f44f507b41021edd0f2f4",
    "tests/test_c0b_decision_feasibility_preflight.py": "b03bbc12b322d86a097e6d2c9721fed6b24f5fa878cf18f0ed0d88c2fa8868fd",
}
C0B1_HASHES = {
    "config/decision_ontology/decision_variable_ontology_v1.json": "a8f28394ea1c007413938600623f8e418491c69a9f9351d83d6256122ad4c534",
    "outputs/decision_feasibility/C0B1_ARCHITECTURE_COMPARISON.csv": "314b6a5ef9305b4768a3beb996475c9a86c0365756908db7aada789dbe9508bb",
    "outputs/decision_feasibility/C0B1_DECISION_ONTOLOGY_REPORT.md": "5ac132bdf32d544711d12b0dd7ba86b37e872b6d76198953bdc363590ead379f",
    "scripts/c0b1_decision_ontology_preflight.py": "b94a870af2a946c37e5f7d6581e2518e66ba284d166d45e8d64093a8e8274e60",
    "tests/test_c0b1_decision_ontology.py": "cadbb785cc8780025b43196284842b9ca0c8ac42012968f894ea61304c12484c",
}

TARGET_CROPS = {"14010020000", "14010070000", "13010210000", "13010170102", "15010040000"}
MODEL_DISTRICT_N = 55
RECOVERY_STATUS = "PASS_FOR_FINAL_NOTARIAL_C0B2_FREEZE_AUDIT"
SCIENTIFIC_ENDSTATE = "SPATIAL_MEMBERSHIP_RECOVERED_BUT_SERVICE_PARTITION_INSUFFICIENT"
OPERATIONAL_SYSTEMS = {
    "Sistema Hidraulico Chira Piura",
    "Sistema Hidraulico San Lorenzo",
    "Sistema Hidraulico Alto Piura",
}
FORMER_UNRESOLVED_IDS = {
    "200502", "200503", "200504", "200505", "200506",
    "200507", "200606", "200607", "200608", "200804",
}
SERVICE_LEVEL_IDS = {
    "200101", "200105", "200107", "200301", "200306", "200308",
    *FORMER_UNRESOLVED_IDS,
}
NAMED_SERVICE_UNIT_IDS = {"200101", "200306", "200308", "200608"}
CONFIRMED_MULTI_IDS = {"200308"}
CONDITIONAL_MULTI_IDS = {
    "200101", "200111", "200114", "200202", "200301",
    "200303", "200304", "200306", "200601",
}
FALSE_LADDER_MULTI_IDS = {"200105", "200107", "200307"}

PIURA_ANTECEDENT_CODE = "PMBP-05-B025"
PIURA_OPERATIVE_2022_CODE = "PMBP-05-B03"
GEOSNIRH_POINT_EVIDENCE_IDS = {
    "C0B2-GIS-001", "C0B2-GIS-002", "C0B2-GIS-003", "C0B2-HYD-013",
}

CURRENT_CANONICAL_PIURA_JUNTAS = {
    "Junta de Usuarios de Chira",
    "Junta de Usuarios de Sechura",
    "Junta de Usuarios de Huancabamba",
    "Junta de Usuarios Medio y Bajo Piura",
    "Junta de Usuarios Alto Piura",
    "Junta de Usuarios San Lorenzo",
}
JUNTA_SOURCE_LABEL_TO_CANONICAL = {
    **{name: name for name in CURRENT_CANONICAL_PIURA_JUNTAS},
    "Junta de Usuarios del Sector Hidraulico Chira": "Junta de Usuarios de Chira",
    "Junta de Usuarios del Sector Hidraulico Menor Sechura - Clase A": "Junta de Usuarios de Sechura",
    "Junta de Usuarios del Sector Hidraulico Menor Huancabamba": "Junta de Usuarios de Huancabamba",
    "Junta de Usuarios Sector Hidraulico Medio y Bajo Piura": "Junta de Usuarios Medio y Bajo Piura",
    "Junta de Usuarios Sector Hidraulico San Lorenzo": "Junta de Usuarios San Lorenzo",
    "Junta de Usuarios Valle Andino Huancabamba": "Junta de Usuarios de Huancabamba",
}
HISTORICAL_JUNTA_LABELS = {"Junta de Usuarios Valle Andino Huancabamba"}
UNSUPPORTED_JUNTA_ALIASES = {"Junta de Usuarios del Distrito de Riego Huancabamba"}
NON_JUNTA_HYDRAULIC_LABELS = {"Junta de Usuarios del Canal Chicope"}

CROSS_TEMPORAL_COMMISSION_INVENTORY = {
    "ALTO_PIURA": {
        "Serran", "Bigote", "Malacasi", "Ingenio Buenos Aires", "La Gallega",
        "Pabur", "Charanal", "Yapatera", "Sancor", "Vicus",
    },
    "SAN_LORENZO": {
        "San Isidro I-II", "TJ 05", "Hualtaco III", "Tejedores", "M-Malingas",
        "Chipillico Bajo", "Hualtaco I-II-IV", "Valle de los Incas", "Somate Bajo",
        "Yuscay Tablazo Alto", "TG-Malingas", "Somate Alto", "Algarrobo Valle Hermoso",
        "Quiroz-Paimas", "Quebrada Tototal", "Chipillico Alto",
    },
    "MEDIO_Y_BAJO_PIURA": {
        "Margen Izquierda", "Margen Derecha", "Castilla", "Puyuntala", "La Bruja",
        "Palo Parado", "Cumbibira", "Shaz", "Casarana", "Sinchao parte alta",
        "Chato", "Seminario",
    },
    "SECHURA": {"Parte Alta", "San Andres", "Margen Izquierda", "Margen Derecha", "Delegados de Canal"},
    "HUANCABAMBA": {
        "Chantaco Shaya Tacarpo", "Putaga Jicate", "Cataluco", "Tierra Amarillas",
        "Cascapampa", "Sondorillo", "Los Laureles de Parguyuc",
    },
}
CURRENT_EXHAUSTIVE_SAN_LORENZO_ROSTER = CROSS_TEMPORAL_COMMISSION_INVENTORY["SAN_LORENZO"]
COMMISSION_SOURCE_SPELLING_ALIASES = {
    "Quebrada Totoral": ("Quebrada Tototal", "C0B2-HYD-006"),
}
DISTRICT_RESOLVED_COMMISSIONS = {
    "Comision de Usuarios Cascapampa",
    "Comision de Usuarios del Subsector Hidraulico El Arenal",
    "Comision de Usuarios del Subsector Hidraulico San Andres",
    "Comision de Usuarios Los Laureles de Parguyuc",
    "Comision de Usuarios Medio Piura Margen Derecha",
    "Comision de Usuarios Puyuntala",
    "Comision de Usuarios Quebrada Chantaco, Shumaya, Tacarpo",
    "Comision de Usuarios San Pablo de la Capilla",
    "Comision de Usuarios Sub Sector Hidraulico Canal Nancho",
    "Comision de Usuarios Tierras Amarillas",
    "Hualtaco III", "San Isidro I-II", "Tejedores", "TJ 05",
}
NAMED_IRRIGATION_BLOCKS = {
    "Poechos Somate", "Maran Santa Rosa", "La Limonera", "Parkinsonia",
    "Bloque Los Chinguel", "Bloque 50+500 Izquierda PMBP-05-B03",
    "Bloque de Riego El Molle", "Bloque de Riego Bolsanada",
}

REGISTRY_SCHEMA = [
    "EVIDENCE_ID", "DOMAIN", "SOURCE_TIER", "SOURCE_AUTHORITY", "SOURCE_TITLE",
    "SOURCE_DATE", "SOURCE_URL", "SOURCE_DOCUMENT_TYPE", "PAGE_OR_SECTION",
    "ENTITY_TYPE", "ENTITY_NAME", "CLAIM_TYPE", "RAW_PLACE_NAME",
    "DISTRICT_NAME", "PROVINCE_NAME", "UBIGEO", "EVIDENCE_SCOPE",
    "EXHAUSTIVENESS_STATUS", "EVIDENCE_STATUS", "EXACT_FINDING", "LIMITATION", "NOTES",
]
AGENCY_SCHEMA = [
    "AGENCY_NAME", "DISTRICT_NAME", "PROVINCE_NAME", "UBIGEO", "RELATION_STATUS",
    "EXHAUSTIVENESS_STATUS", "RELATIONSHIP_CLASS", "EVIDENCE_IDS", "PCR_GROUP_USE",
    "DISTRICT_PCR_DISAGGREGATION_AUTHORIZED", "CRITICAL_GAP", "NOTES",
]
HYDRAULIC_SCHEMA = [
    "HYDRAULIC_SYSTEM", "ALA", "JUNTA", "COMMISSION_OR_SUBSECTOR",
    "IRRIGATION_BLOCK", "WATER_SOURCE", "DISTRICT_NAME", "PROVINCE_NAME", "UBIGEO",
    "SERVICE_RELATION_STATUS", "EXHAUSTIVENESS_STATUS", "RELATIONSHIP_CLASS",
    "EVIDENCE_IDS", "MODEL_SPATIAL_ROLE", "SERVICE_FRACTION_AVAILABLE",
    "SERVICE_FRACTION_VALUE", "DOUBLE_COUNTING_RISK", "CRITICAL_GAP", "NOTES",
]
ELIGIBILITY_SCHEMA = [
    "UBIGEO", "DISTRICT_NAME", "PROVINCE_NAME", "IN_MODEL_UNIVERSE",
    "TARGET_CROPS_OBSERVED", "AGENCY_RELATION_COUNT", "AGENCY_MAPPING_STATUS",
    "PCR_GROUP_REFERENCE_STATUS", "HYDRAULIC_SYSTEM_COUNT", "JUNTA_COUNT",
    "COMMISSION_OR_SUBSECTOR_COUNT", "HYDRAULIC_MAPPING_STATUS",
    "IRRIGATION_SERVICE_STATUS", "RAINFED_STATUS", "DOUBLE_COUNTING_RISK",
    "DISTRICT_INDEX_STATUS", "FUTURE_WATER_SPATIAL_ROLE",
    "UNRESOLVED_CRITICAL_GAP", "EVIDENCE_IDS",
]

DOMAINS = {
    "AGENCY", "PCR", "HYDRAULIC_SYSTEM", "ALA", "JUNTA", "COMMISSION",
    "SUBSECTOR", "IRRIGATION_BLOCK", "IRRIGATION_SERVICE_AREA",
    "IRRIGATION_STATUS", "DISTRICT_LINKAGE",
}
SOURCE_TIERS = {
    "INTERNAL_FROZEN", "A1_OFFICIAL_DRAP", "H1_MASTER_OFFICIAL_SOURCE",
    "H2_EXACT_OFFICIAL_ADMINISTRATIVE_RECORD",
    "H3_PRIMARY_OFFICIAL_INSTITUTIONAL_EVIDENCE", "H4_CONTEXT_ONLY",
}
EVIDENCE_STATUSES = {
    "CERTIFIED_EXACT_SERVICE_RELATION", "CERTIFIED_EXACT_POLITICAL_LOCATION",
    "SUPPORTED_PARTIAL_PRESENCE", "SUPPORTED_JURISDICTION", "PRESENCE_ONLY", "UNRESOLVED",
}
EXHAUSTIVENESS = {"COMPLETE_EXHAUSTIVE", "PARTIAL_KNOWN", "NONEXHAUSTIVE_PRESENCE_ONLY", "UNKNOWN"}
RELATIONSHIP_CLASSES = {"ONE_TO_ONE", "ONE_TO_MANY", "MANY_TO_ONE", "MANY_TO_MANY", "PARTIAL_UNKNOWN"}
PCR_USES = {"GROUP_LEVEL_PCR_SOFT_REFERENCE", "CONTEXT_ONLY", "UNRESOLVED"}
MODEL_ROLES = {
    "SPATIALLY_ELIGIBLE_AFTER_SERVICE_PARTITION",
    "SPATIALLY_ELIGIBLE_AFTER_SERVICE_PARTITION_OR_SUBINDEX",
    "CONDITIONAL_WATER_SPATIAL_ELIGIBILITY", "INSTITUTIONAL_MEMBERSHIP_ONLY",
    "PARTIAL_COVERAGE_ONLY", "SENSITIVITY_ONLY", "CONTEXT_ONLY", "UNRESOLVED",
}
DOUBLE_COUNTING = {
    "CONFIRMED_MULTI_SERVICE_DOUBLE_COUNTING_RISK",
    "CONDITIONAL_MULTI_RELATION_REQUIRES_ADJUDICATION",
    "NO_CONFIRMED_MULTI_SERVICE",
}
INDEX_STATUSES = {
    "SUBINDEX_REQUIRED_BY_CONFIRMED_MULTI_SERVICE",
    "SUBINDEX_OR_PARTITION_REQUIRED_PENDING_SERVICE_EVIDENCE",
    "POTENTIAL_SUBINDEX_ONLY",
}

REPORT_HEADINGS = [
    *(f"## {number}. {title}" for number, title in enumerate([
        "Executive verdict", "Frozen C0B1 identity", "Canonical model district universe",
        "Agency architecture", "Agency-to-UBIGEO reconstruction", "PCR implications",
        "Hydraulic institutional hierarchy", "Chira system", "San Lorenzo system",
        "Medio y Bajo Piura system", "Sechura system", "Alto Piura context",
        "Other relevant systems/highland/rainfed contexts", "Irrigation-block evidence",
        "District linkage", "Many-to-many relationships", "Double-counting risk",
        "Irrigated/rainfed limitations", "District-only versus hydraulic-subindex requirement",
        "Spatial coverage diagnostics", "Future system-level constraint eligibility",
        "Districts/areas requiring scope reduction", "Forbidden interpretations",
        "Remaining evidence gaps", "Final C0B2 verdict",
    ], start=1)),
    "### C0B2RA independent audit correction",
    "### Junta / Commission recovery",
    "### Hydraulic entity ontology reclassification",
    "### Former unresolved ten correction",
]

FORBIDDEN_CONTENT_PATTERNS = [
    r"DISTRICT_WATER_BUDGET_CREATED", r"SERVICE_FRACTION_VALUE\s*[,=]\s*[0-9]",
    r"PCR.*DISAGGREGATED_TO_DISTRICT", r"OPTIMAL_HECTARES", r"SOLVER_INVOCATION",
]
FORBIDDEN_PATH_PARTS = ("outputs/optimization", "outputs/scenario", "config/optimization", "scripts/optimize", "C0B3")


def _run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, text=True, encoding="utf-8",
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    )
    return result.stdout.strip()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _schema(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return next(csv.reader(handle))


def canonical_model_universe() -> dict[str, set[str]]:
    universe: dict[str, set[str]] = {}
    for row in _read_csv(PANEL_PATH):
        if row["COD_CULTIVO"] in TARGET_CROPS:
            universe.setdefault(row["UBIGEO"], set()).add(row["COD_CULTIVO"])
    return universe


def checkpoint_gate() -> dict[str, object]:
    checks = {
        "BRANCH": _run_git(["branch", "--show-current"]) == EXPECTED_BRANCH,
        "HEAD": _run_git(["rev-parse", "HEAD"]) == EXPECTED_HEAD,
        "PARENT": _run_git(["rev-parse", "HEAD^"]) == EXPECTED_PARENT,
        "COMMIT_MESSAGE": _run_git(["log", "-1", "--pretty=%s"]) == EXPECTED_COMMIT_MESSAGE,
        "ORIGIN_HEAD": _run_git(["rev-parse", "origin/phase/c0b-decision-feasibility-v1"]) == EXPECTED_HEAD,
        "DIVERGENCE": _run_git(["rev-list", "--left-right", "--count", "HEAD...origin/phase/c0b-decision-feasibility-v1"]) == "0\t0",
    }
    failures = [name for name, passed in checks.items() if not passed]
    return {"status": "PASS" if not failures else "FAIL", "failures": failures}


def immutable_gate() -> dict[str, object]:
    failures = [
        rel for rel, expected in {**C0B0_HASHES, **C0B1_HASHES}.items()
        if _sha256(ROOT / rel) != expected
    ]
    return {"status": "PASS" if not failures else "FAIL", "failures": failures}


def persistent_scope_gate() -> dict[str, object]:
    observed = set(filter(None, _run_git(["ls-files", "--others", "--exclude-standard"]).splitlines()))
    failures = []
    if observed != AUTHORIZED_SCOPE:
        failures.append("UNTRACKED_SCOPE")
    if _run_git(["diff", "--name-only"]):
        failures.append("TRACKED_DIFF")
    if _run_git(["diff", "--cached", "--name-only"]):
        failures.append("STAGED_DIFF")
    failures.extend(
        f"FORBIDDEN_PATH:{path}" for path in observed
        if any(part in path for part in FORBIDDEN_PATH_PARTS)
    )
    return {"status": "PASS" if not failures else "FAIL", "failures": failures, "observed": sorted(observed)}


def schema_gate() -> dict[str, object]:
    expected = {
        REGISTRY_PATH: REGISTRY_SCHEMA, AGENCY_PATH: AGENCY_SCHEMA,
        HYDRAULIC_PATH: HYDRAULIC_SCHEMA, ELIGIBILITY_PATH: ELIGIBILITY_SCHEMA,
    }
    failures = [str(path.relative_to(ROOT)) for path, schema in expected.items() if _schema(path) != schema]
    return {"status": "PASS" if not failures else "FAIL", "failures": failures}


def vocabulary_gate() -> dict[str, object]:
    failures: list[str] = []
    for row in _read_csv(REGISTRY_PATH):
        if row["DOMAIN"] not in DOMAINS:
            failures.append(f"DOMAIN:{row['EVIDENCE_ID']}")
        if row["SOURCE_TIER"] not in SOURCE_TIERS:
            failures.append(f"SOURCE_TIER:{row['EVIDENCE_ID']}")
        if row["EVIDENCE_STATUS"] not in EVIDENCE_STATUSES:
            failures.append(f"EVIDENCE_STATUS:{row['EVIDENCE_ID']}")
        if row["EXHAUSTIVENESS_STATUS"] not in EXHAUSTIVENESS:
            failures.append(f"EXHAUSTIVENESS:{row['EVIDENCE_ID']}")
    for row in _read_csv(AGENCY_PATH):
        if row["RELATION_STATUS"] not in EVIDENCE_STATUSES:
            failures.append(f"AGENCY_RELATION:{row['UBIGEO']}")
        if row["EXHAUSTIVENESS_STATUS"] not in EXHAUSTIVENESS:
            failures.append(f"AGENCY_EXHAUSTIVENESS:{row['UBIGEO']}")
        if row["RELATIONSHIP_CLASS"] not in RELATIONSHIP_CLASSES:
            failures.append(f"AGENCY_RELCLASS:{row['UBIGEO']}")
        if row["PCR_GROUP_USE"] not in PCR_USES:
            failures.append(f"PCR_USE:{row['UBIGEO']}")
    for row in _read_csv(HYDRAULIC_PATH):
        if row["SERVICE_RELATION_STATUS"] not in EVIDENCE_STATUSES:
            failures.append(f"HYD_STATUS:{row['UBIGEO']}")
        if row["EXHAUSTIVENESS_STATUS"] not in EXHAUSTIVENESS:
            failures.append(f"HYD_EXHAUSTIVENESS:{row['UBIGEO']}")
        if row["RELATIONSHIP_CLASS"] not in RELATIONSHIP_CLASSES:
            failures.append(f"HYD_RELCLASS:{row['UBIGEO']}")
        if row["MODEL_SPATIAL_ROLE"] not in MODEL_ROLES:
            failures.append(f"HYD_ROLE:{row['UBIGEO']}")
        if row["DOUBLE_COUNTING_RISK"] not in DOUBLE_COUNTING:
            failures.append(f"HYD_DOUBLE:{row['UBIGEO']}")
    for row in _read_csv(ELIGIBILITY_PATH):
        if row["DOUBLE_COUNTING_RISK"] not in DOUBLE_COUNTING:
            failures.append(f"ELIG_DOUBLE:{row['UBIGEO']}")
        if row["DISTRICT_INDEX_STATUS"] not in INDEX_STATUSES:
            failures.append(f"ELIG_INDEX:{row['UBIGEO']}")
        if row["FUTURE_WATER_SPATIAL_ROLE"] not in MODEL_ROLES:
            failures.append(f"ELIG_ROLE:{row['UBIGEO']}")
    return {"status": "PASS" if not failures else "FAIL", "failures": failures}


def ubigeo_gate() -> dict[str, object]:
    universe = canonical_model_universe()
    expected = set(universe)
    failures: list[str] = []
    if len(universe) != MODEL_DISTRICT_N:
        failures.append("MODEL_UNIVERSE_N")
    if not expected.issubset({row["UBIGEO"] for row in _read_csv(LAND_PATH)}):
        failures.append("LAND_PHYSICAL_LINK")
    if {row["UBIGEO"] for row in _read_csv(AGENCY_PATH)} != expected:
        failures.append("AGENCY_UNIVERSE")
    if {row["UBIGEO"] for row in _read_csv(HYDRAULIC_PATH)} != expected:
        failures.append("HYDRAULIC_UNIVERSE")
    if {row["UBIGEO"] for row in _read_csv(ELIGIBILITY_PATH)} != expected:
        failures.append("ELIGIBILITY_UNIVERSE")
    return {"status": "PASS" if not failures else "FAIL", "failures": failures, "model_n": len(universe)}


def evidence_id_gate() -> dict[str, object]:
    ids = [row["EVIDENCE_ID"] for row in _read_csv(REGISTRY_PATH)]
    failures: list[str] = []
    if len(ids) != len(set(ids)):
        failures.append("DUPLICATE_EVIDENCE_IDS")
    if any(not re.match(r"^C0B2-[A-Z]+-[0-9]{3}$", eid) for eid in ids):
        failures.append("NONDETERMINISTIC_ID_PATTERN")
    known = set(ids)
    for path in (AGENCY_PATH, HYDRAULIC_PATH, ELIGIBILITY_PATH):
        for row in _read_csv(path):
            for eid in filter(None, row.get("EVIDENCE_IDS", "").split(";")):
                if eid not in known:
                    failures.append(f"UNRESOLVED_EVIDENCE_ID:{eid}")
    return {"status": "PASS" if not failures else "FAIL", "failures": sorted(set(failures))}


def relationship_gate() -> dict[str, object]:
    registry = _read_csv(REGISTRY_PATH)
    agency = _read_csv(AGENCY_PATH)
    hydraulic = _read_csv(HYDRAULIC_PATH)
    eligibility = _read_csv(ELIGIBILITY_PATH)
    registry_by_id = {row["EVIDENCE_ID"]: row for row in registry}
    failures: list[str] = []
    hyd_keys = [
        (r["HYDRAULIC_SYSTEM"], r["ALA"], r["JUNTA"], r["COMMISSION_OR_SUBSECTOR"],
         r["IRRIGATION_BLOCK"], r["WATER_SOURCE"], r["UBIGEO"]) for r in hydraulic
    ]
    if len(hyd_keys) != len(set(hyd_keys)):
        failures.append("DUPLICATE_HYDRAULIC_RELATION")
    agency_keys = [(r["AGENCY_NAME"], r["DISTRICT_NAME"], r["UBIGEO"]) for r in agency]
    if len(agency_keys) != len(set(agency_keys)):
        failures.append("DUPLICATE_AGENCY_RELATION")
    for row in hydraulic:
        ubigeo = row["UBIGEO"]
        if row["SERVICE_FRACTION_AVAILABLE"] != "FALSE" or row["SERVICE_FRACTION_VALUE"]:
            failures.append(f"INVENTED_SERVICE_FRACTION:{ubigeo}")
        if row["EXHAUSTIVENESS_STATUS"] == "COMPLETE_EXHAUSTIVE":
            failures.append(f"EXHAUSTIVE_HYDRAULIC_OVERCLAIM:{ubigeo}")
        if row["EXHAUSTIVENESS_STATUS"] == "NONEXHAUSTIVE_PRESENCE_ONLY" and row["SERVICE_RELATION_STATUS"] == "CERTIFIED_EXACT_SERVICE_RELATION":
            failures.append(f"PRESENCE_PROMOTED_TO_SERVICE:{ubigeo}")
        if row["HYDRAULIC_SYSTEM"] and row["HYDRAULIC_SYSTEM"] not in OPERATIONAL_SYSTEMS:
            failures.append(f"NONCANONICAL_MAJOR_SYSTEM:{ubigeo}")
        if row["ALA"] in {"Chinchipe Chamaya", "Motupe Olmos La Leche"} and row["HYDRAULIC_SYSTEM"]:
            failures.append(f"ALA_PROMOTED_TO_OPERATIONAL_SYSTEM:{ubigeo}")
        if row["EVIDENCE_IDS"] == "C0B2-GIS-001;C0B2-GIS-002;C0B2-GIS-003":
            if "EVIDENCE_LEVEL=L1_OFFICIAL_HYDRAULIC_PRESENCE;GEOMETRY=POINT" not in row["NOTES"]:
                failures.append(f"GEOSNIRH_POINT_SEMANTICS:{ubigeo}")
            if any(row[field] for field in ("HYDRAULIC_SYSTEM", "JUNTA", "COMMISSION_OR_SUBSECTOR", "IRRIGATION_BLOCK")):
                failures.append(f"GEOSNIRH_POINT_PROMOTED:{ubigeo}")
        if row["SERVICE_RELATION_STATUS"] == "CERTIFIED_EXACT_SERVICE_RELATION":
            evidence_ids = set(filter(None, row["EVIDENCE_IDS"].split(";")))
            independent_l3 = {
                eid for eid in evidence_ids
                if eid in registry_by_id
                and registry_by_id[eid]["EVIDENCE_STATUS"] == "CERTIFIED_EXACT_SERVICE_RELATION"
                and registry_by_id[eid]["SOURCE_DOCUMENT_TYPE"] != "OFFICIAL_WFS_CSV_RECORD"
                and registry_by_id[eid]["CLAIM_TYPE"].startswith("L3_")
            }
            if not independent_l3:
                failures.append(f"L3_WITHOUT_INDEPENDENT_NON_GEOSNIRH_SOURCE:{ubigeo}")
        if row["IRRIGATION_BLOCK"] and "EVIDENCE_LEVEL=L3_NAMED_SERVICE_UNIT" not in row["NOTES"]:
            failures.append(f"BLOCK_NOT_NAMED_SERVICE_UNIT:{ubigeo}")
        if "L4_OFFICIAL_PARTITION_OR_FRACTION" in row["NOTES"]:
            failures.append(f"NAMED_UNIT_MISCLASSIFIED_AS_PARTITION:{ubigeo}")
        if "Canal Chicope" in row["JUNTA"]:
            failures.append(f"INFRASTRUCTURE_COUNTED_AS_JUNTA:{ubigeo}")
    commissions = {r["COMMISSION_OR_SUBSECTOR"] for r in hydraulic if r["COMMISSION_OR_SUBSECTOR"]}
    if commissions != DISTRICT_RESOLVED_COMMISSIONS:
        failures.append("DISTRICT_COMMISSION_MASTER_MISMATCH")
    if any(label in commissions for label in ("Canal Chicope-Cajunga", "Comite de Usuarios de Agua Canal Chajapampa")):
        failures.append("INVALID_COMMISSION_ENTITY_TYPE")
    if any(row["DISTRICT_PCR_DISAGGREGATION_AUTHORIZED"] != "FALSE" for row in agency):
        failures.append("PCR_DISAGGREGATION_AUTHORIZED")
    if any(row["EXHAUSTIVENESS_STATUS"] == "COMPLETE_EXHAUSTIVE" for row in agency):
        failures.append("AGENCY_EXHAUSTIVENESS_OVERCLAIM")
    by_ubigeo = {row["UBIGEO"]: row for row in eligibility}
    for ubigeo in FALSE_LADDER_MULTI_IDS:
        if by_ubigeo[ubigeo]["DOUBLE_COUNTING_RISK"] != "NO_CONFIRMED_MULTI_SERVICE":
            failures.append(f"FALSE_LADDER_MULTI:{ubigeo}")
    return {"status": "PASS" if not failures else "FAIL", "failures": failures}


def recovery_gate() -> dict[str, object]:
    registry = _read_csv(REGISTRY_PATH)
    agency = _read_csv(AGENCY_PATH)
    hydraulic = _read_csv(HYDRAULIC_PATH)
    eligibility = _read_csv(ELIGIBILITY_PATH)
    by_id = {row["EVIDENCE_ID"]: row for row in registry}
    elig_by_id = {row["UBIGEO"]: row for row in eligibility}
    failures: list[str] = []
    required_ids = {"C0B2-GIS-001", "C0B2-GIS-002", "C0B2-GIS-003", *(f"C0B2-HYD-{n:03d}" for n in range(15, 29))}
    if not required_ids.issubset(by_id):
        failures.append("TARGETED_EVIDENCE_REGISTRY_INCOMPLETE")
    gis_text = "\n".join(" ".join(by_id[eid].values()) for eid in ("C0B2-GIS-001", "C0B2-GIS-002", "C0B2-GIS-003"))
    for token in (
        "SERV_Formalizacion", "esriGeometryPoint", "EPSG:4326", "GetFeature",
        "RAW_WFS_CSV_SHA256", "54 district-ALA families",
        "FORMALIZATION_ENTITIES_NOT_IRRIGATION_BLOCKS", "1504 byte-distinct",
    ):
        if token not in gis_text:
            failures.append(f"GEOSNIRH_METADATA_MISSING:{token}")
    hyd_ids = {row["UBIGEO"] for row in hydraulic}
    if len(hyd_ids) != MODEL_DISTRICT_N:
        failures.append("HYDRAULIC_COVERAGE_NOT_55")
    if not FORMER_UNRESOLVED_IDS.issubset(hyd_ids):
        failures.append("FORMER_UNRESOLVED_NOT_CORRECTED")
    if any("UNRESOLVED" in elig_by_id[ubigeo]["HYDRAULIC_MAPPING_STATUS"] for ubigeo in FORMER_UNRESOLVED_IDS):
        failures.append("FORMER_UNRESOLVED_STATUS_RETAINED")
    service = {r["UBIGEO"] for r in hydraulic if r["SERVICE_RELATION_STATUS"] == "CERTIFIED_EXACT_SERVICE_RELATION"}
    if service != SERVICE_LEVEL_IDS:
        failures.append("SERVICE_LEVEL_DISTRICT_SET")
    named_units = {r["UBIGEO"] for r in hydraulic if "EVIDENCE_LEVEL=L3_NAMED_SERVICE_UNIT" in r["NOTES"]}
    if named_units != NAMED_SERVICE_UNIT_IDS:
        failures.append("NAMED_SERVICE_UNIT_DISTRICT_SET")
    cristo = [r for r in hydraulic if r["UBIGEO"] == "200804"]
    if len(cristo) != 1 or "Sechura" not in cristo[0]["JUNTA"] or "San Andres" not in cristo[0]["COMMISSION_OR_SUBSECTOR"]:
        failures.append("CRISTO_NOS_VALGA_HIERARCHY")
    if any("Medio y Bajo Piura" in r["JUNTA"] for r in cristo):
        failures.append("CRISTO_INCORRECT_PARENT_RETAINED")
    systems_record = by_id.get("C0B2-HYD-001", {}).get("ENTITY_NAME", "")
    if set(filter(None, systems_record.split(";"))) != OPERATIONAL_SYSTEMS:
        failures.append("OPERATIONAL_SYSTEM_MASTER")
    junta_roster = set(filter(None, by_id.get("C0B2-HYD-028", {}).get("ENTITY_NAME", "").split(";")))
    if junta_roster != CURRENT_CANONICAL_PIURA_JUNTAS:
        failures.append("CURRENT_CANONICAL_PIURA_JUNTA_ROSTER")
    if "Junta de Usuarios Alto Piura" not in junta_roster:
        failures.append("ALTO_PIURA_JUNTA_MISSING")
    raw_juntas = {r["JUNTA"] for r in hydraulic if r["JUNTA"]}
    unknown_juntas = raw_juntas - set(JUNTA_SOURCE_LABEL_TO_CANONICAL)
    if unknown_juntas:
        failures.append(f"UNADJUDICATED_JUNTA_LABELS:{sorted(unknown_juntas)}")
    evidence_backed_alias_fields = "\n".join(
        [r["ENTITY_NAME"] for r in registry]
        + [r["JUNTA"] for r in hydraulic]
    )
    if any(alias in evidence_backed_alias_fields for alias in UNSUPPORTED_JUNTA_ALIASES):
        failures.append("UNSUPPORTED_HUANCABAMBA_ALIAS")
    if any("Canal Chicope" in r["JUNTA"] for r in hydraulic):
        failures.append("CANAL_CHICOPE_COUNTED_AS_JUNTA")
    if JUNTA_SOURCE_LABEL_TO_CANONICAL.get("Junta de Usuarios Valle Andino Huancabamba") != "Junta de Usuarios de Huancabamba":
        failures.append("HUANCABAMBA_HISTORICAL_LINEAGE")
    if not all(label not in CURRENT_CANONICAL_PIURA_JUNTAS for label in HISTORICAL_JUNTA_LABELS):
        failures.append("HISTORICAL_JUNTA_COUNTED_AS_CURRENT")
    if "HISTORICAL_JUNTA_LABEL=JUNTA_VALLE_ANDINO_HUANCABAMBA" not in by_id["C0B2-HYD-009"]["NOTES"]:
        failures.append("HUANCABAMBA_LINEAGE_PROVENANCE_MISSING")
    for ubigeo, eligibility_row in elig_by_id.items():
        normalized = {
            JUNTA_SOURCE_LABEL_TO_CANONICAL[r["JUNTA"]]
            for r in hydraulic
            if r["UBIGEO"] == ubigeo
            and r["JUNTA"] in JUNTA_SOURCE_LABEL_TO_CANONICAL
        }
        if int(eligibility_row["JUNTA_COUNT"]) != len(normalized):
            failures.append(f"CANONICAL_JUNTA_COUNT_MISMATCH:{ubigeo}")

    commission_count = sum(len(values) for values in CROSS_TEMPORAL_COMMISSION_INVENTORY.values())
    roster = set(filter(None, by_id.get("C0B2-HYD-015", {}).get("ENTITY_NAME", "").split(";")))
    if commission_count != 50:
        failures.append("CROSS_TEMPORAL_COMMISSION_INVENTORY_NOT_50")
    if roster != CURRENT_EXHAUSTIVE_SAN_LORENZO_ROSTER or len(roster) != 16:
        failures.append("SAN_LORENZO_CURRENT_EXHAUSTIVE_ROSTER")
    if not {"Somate Alto", "Somate Bajo", "Quebrada Tototal"}.issubset(roster):
        failures.append("SAN_LORENZO_CURRENT_ROSTER_CONTENT")
    if "Quebrada Totoral" in roster:
        failures.append("TOTORAL_USED_AS_CURRENT_CANONICAL")
    alias_target, alias_evidence = COMMISSION_SOURCE_SPELLING_ALIASES["Quebrada Totoral"]
    if alias_target != "Quebrada Tototal" or "Quebrada Totoral" not in by_id[alias_evidence]["ENTITY_NAME"]:
        failures.append("TOTORAL_ALIAS_PROVENANCE")
    temporal_claim_text = "\n".join([REPORT_PATH.read_text(encoding="utf-8")] + [" ".join(r.values()) for r in registry])
    for forbidden in (
        "50 valid current canonical commission",
        "50_CURRENT_OFFICIAL_COMMISSION_SUBSECTOR_ENTITIES",
        "CURRENT_EXHAUSTIVE_PIURA_COMMISSION_SUBSECTOR_N=50",
    ):
        if forbidden.lower() in temporal_claim_text.lower():
            failures.append(f"GLOBAL_50_CURRENT_COMMISSION_CLAIM:{forbidden}")
    combined_registry = "\n".join(" ".join(row.values()) for row in registry)
    if any(block not in combined_registry for block in NAMED_IRRIGATION_BLOCKS):
        failures.append("NAMED_IRRIGATION_BLOCK_INVENTORY")
    piura_active = [
        r for r in hydraulic
        if r["UBIGEO"] == "200101" and r["IRRIGATION_BLOCK"]
    ]
    if len(piura_active) != 1 or PIURA_OPERATIVE_2022_CODE not in piura_active[0]["IRRIGATION_BLOCK"]:
        failures.append("PIURA_OPERATIVE_2022_CODE")
    if any(PIURA_ANTECEDENT_CODE in r["IRRIGATION_BLOCK"] for r in piura_active):
        failures.append("PIURA_ANTECEDENT_USED_AS_OPERATIVE")
    piura_source = by_id["C0B2-HYD-010"]
    required_piura_roles = {
        f"PIURA_SERVICE_UNIT_ANTECEDENT_CODE={PIURA_ANTECEDENT_CODE}",
        f"PIURA_SERVICE_UNIT_OPERATIVE_2022_CODE={PIURA_OPERATIVE_2022_CODE}",
        f"PIURA_SERVICE_UNIT_CANONICAL_FOR_2022_RELATION={PIURA_OPERATIVE_2022_CODE}",
    }
    if not all(token in piura_source["NOTES"] for token in required_piura_roles):
        failures.append("PIURA_DUAL_CODE_ROLE_PROVENANCE")
    documented_codes = set(re.findall(r"PMBP-05-B\d+", combined_registry + "\n" + "\n".join(r["IRRIGATION_BLOCK"] for r in hydraulic)))
    if documented_codes != {PIURA_ANTECEDENT_CODE, PIURA_OPERATIVE_2022_CODE}:
        failures.append(f"PIURA_UNEXPLAINED_NORMALIZED_CODES:{sorted(documented_codes)}")

    geosnirh_el_molle = by_id["C0B2-HYD-013"]
    ana_el_molle = by_id["C0B2-HYD-027"]
    if (
        geosnirh_el_molle["SOURCE_DOCUMENT_TYPE"] != "OFFICIAL_WFS_CSV_RECORD"
        or geosnirh_el_molle["EVIDENCE_STATUS"] == "CERTIFIED_EXACT_SERVICE_RELATION"
        or not geosnirh_el_molle["CLAIM_TYPE"].startswith("L1_")
    ):
        failures.append("EL_MOLLE_GEOSNIRH_NOT_L1_ONLY")
    if (
        ana_el_molle["SOURCE_DOCUMENT_TYPE"] != "OFFICIAL_ANA_RESOLUTION_PDF"
        or ana_el_molle["SOURCE_DATE"] != "2016-10-03"
        or ana_el_molle["UBIGEO"] != "200308"
        or ana_el_molle["EVIDENCE_STATUS"] != "CERTIFIED_EXACT_SERVICE_RELATION"
        or "Bloque de Riego El Molle" not in ana_el_molle["ENTITY_NAME"]
    ):
        failures.append("EL_MOLLE_INDEPENDENT_ANA_PROVENANCE")
    el_molle_rows = [r for r in hydraulic if r["IRRIGATION_BLOCK"] == "Bloque de Riego El Molle"]
    if len(el_molle_rows) != 1 or "C0B2-HYD-027" not in el_molle_rows[0]["EVIDENCE_IDS"].split(";"):
        failures.append("EL_MOLLE_CROSSWALK_PROVENANCE")
    if by_id["C0B2-HYD-021"]["SOURCE_DATE"] != "2016-10-03":
        failures.append("HYD021_EXACT_SOURCE_DATE")
    if by_id["C0B2-HYD-022"]["SOURCE_DATE"] != "2025-04-08":
        failures.append("HYD022_EXACT_SOURCE_DATE")
    expected_multi = {
        "CONFIRMED_MULTI_SERVICE_DOUBLE_COUNTING_RISK": CONFIRMED_MULTI_IDS,
        "CONDITIONAL_MULTI_RELATION_REQUIRES_ADJUDICATION": CONDITIONAL_MULTI_IDS,
        "NO_CONFIRMED_MULTI_SERVICE": set(elig_by_id) - CONFIRMED_MULTI_IDS - CONDITIONAL_MULTI_IDS,
    }
    for status, expected in expected_multi.items():
        observed = {r["UBIGEO"] for r in eligibility if r["DOUBLE_COUNTING_RISK"] == status}
        if observed != expected:
            failures.append(f"MULTI_STATUS:{status}")
    expected_index = {
        "SUBINDEX_REQUIRED_BY_CONFIRMED_MULTI_SERVICE": CONFIRMED_MULTI_IDS,
        "SUBINDEX_OR_PARTITION_REQUIRED_PENDING_SERVICE_EVIDENCE": CONDITIONAL_MULTI_IDS,
        "POTENTIAL_SUBINDEX_ONLY": set(elig_by_id) - CONFIRMED_MULTI_IDS - CONDITIONAL_MULTI_IDS,
    }
    for status, expected in expected_index.items():
        observed = {r["UBIGEO"] for r in eligibility if r["DISTRICT_INDEX_STATUS"] == status}
        if observed != expected:
            failures.append(f"SUBINDEX_STATUS:{status}")
    if len(agency) != 56:
        failures.append("AGENCY_ROW_COUNT")
    sapillica = [r for r in agency if r["UBIGEO"] == "200208"]
    if len(sapillica) != 2 or {r["AGENCY_NAME"] for r in sapillica} != {"Agencia Agraria Ayabaca", "Agencia Agraria San Lorenzo"}:
        failures.append("SAPILLICA_TEMPORAL_RELATION")
    if any(row["RAINFED_STATUS"] != "UNRESOLVED_NOT_ASSUMED_RAINFED" for row in eligibility):
        failures.append("RAINFED_INFERENCE")
    return {"status": "PASS" if not failures else "FAIL", "failures": failures}


def firewall_gate() -> dict[str, object]:
    paths = [REGISTRY_PATH, AGENCY_PATH, HYDRAULIC_PATH, ELIGIBILITY_PATH, REPORT_PATH]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in paths)
    report = REPORT_PATH.read_text(encoding="utf-8")
    failures = [
        f"FORBIDDEN_PATTERN:{pattern}" for pattern in FORBIDDEN_CONTENT_PATTERNS
        if re.search(pattern, combined, flags=re.IGNORECASE)
    ]
    required = [
        "PCR_DISTRICT_DISAGGREGATION_AUTHORIZED=FALSE",
        "WATER_HARD_CONSTRAINT_CURRENTLY_AUTHORIZED=FALSE",
        "SPATIAL_SCOPE_REDUCTION_CURRENTLY_AUTHORIZED=NO",
        "SERVICE_FRACTIONS_INVENTED=0", "NO_OPTIMIZATION",
        "No equal split, area-share split, historical crop-share split, population allocation",
        "Missing service evidence is not classified as rainfed",
        "C0B2 authorizes no optimizer",
        "Poechos supplies all Piura agriculture: FALSE / NOT AUTHORIZED",
    ]
    failures.extend(f"REPORT_MISSING:{phrase}" for phrase in required if phrase not in report)
    if any(row["DISTRICT_PCR_DISAGGREGATION_AUTHORIZED"] != "FALSE" for row in _read_csv(AGENCY_PATH)):
        failures.append("PCR_DISTRICT_ALLOCATION")
    if any(row["SERVICE_FRACTION_AVAILABLE"] != "FALSE" or row["SERVICE_FRACTION_VALUE"] for row in _read_csv(HYDRAULIC_PATH)):
        failures.append("SERVICE_FRACTION_INVENTED")
    return {"status": "PASS" if not failures else "FAIL", "failures": failures}


def report_gate() -> dict[str, object]:
    text = REPORT_PATH.read_text(encoding="utf-8")
    failures = [heading for heading in REPORT_HEADINGS if heading not in text]
    required = [
        RECOVERY_STATUS, SCIENTIFIC_ENDSTATE, "No automatic scope reduction is declared",
        "not a scientific freeze", "C0B2A under-retrieved", "C0B2R recovered",
        "C0B2RA then identified", "REJECTED_INCORRECT_SEED",
        "MAJOR_OPERATIONAL_HYDRAULIC_SYSTEM", "CURRENT_CANONICAL_JUNTA",
        "HISTORICAL_JUNTA_LABEL", "CROSS_TEMPORAL_COMMISSION_INVENTORY",
        "CURRENT_EXHAUSTIVE_ROSTER", "FORMALIZATION_ENTITY",
        "PIURA_SERVICE_UNIT_CANONICAL_FOR_2022_RELATION=PMBP-05-B03",
        "CURRENT_CANONICAL_PIURA_JUNTAS_N=6",
        "CROSS_TEMPORAL_COMMISSION_SUBSECTOR_INVENTORY_N=50",
        "CURRENT_EXHAUSTIVE_COMMISSION_ROSTER_VERIFIED_SCOPE=SAN_LORENZO_ONLY",
        "HYD021_SOURCE_DATE=2016-10-03", "HYD022_SOURCE_DATE=2025-04-08",
    ]
    failures.extend(f"MISSING:{token}" for token in required if token not in text)
    if "FULL_MULTISCALE_SPATIAL_FEASIBILITY" in text:
        failures.append("FORBIDDEN_ENDSTATE")
    return {"status": "PASS" if not failures else "FAIL", "failures": failures}


def coverage_diagnostics() -> dict[str, object]:
    registry = _read_csv(REGISTRY_PATH)
    eligibility = _read_csv(ELIGIBILITY_PATH)
    agency = _read_csv(AGENCY_PATH)
    hydraulic = _read_csv(HYDRAULIC_PATH)
    agency_any = {r["UBIGEO"] for r in agency if r["AGENCY_NAME"]}
    agency_supported = {r["UBIGEO"] for r in agency if r["RELATION_STATUS"] == "SUPPORTED_JURISDICTION"}
    hyd_any = {r["UBIGEO"] for r in hydraulic}
    service = {r["UBIGEO"] for r in hydraulic if r["SERVICE_RELATION_STATUS"] == "CERTIFIED_EXACT_SERVICE_RELATION"}
    named_units = {r["UBIGEO"] for r in hydraulic if "EVIDENCE_LEVEL=L3_NAMED_SERVICE_UNIT" in r["NOTES"]}
    l2_strongest = {r["UBIGEO"] for r in eligibility if r["HYDRAULIC_MAPPING_STATUS"].startswith("L2_")}
    l1_strongest = {r["UBIGEO"] for r in eligibility if r["HYDRAULIC_MAPPING_STATUS"].startswith("L1_")}
    confirmed = {r["UBIGEO"] for r in eligibility if r["DOUBLE_COUNTING_RISK"] == "CONFIRMED_MULTI_SERVICE_DOUBLE_COUNTING_RISK"}
    conditional = {r["UBIGEO"] for r in eligibility if r["DOUBLE_COUNTING_RISK"] == "CONDITIONAL_MULTI_RELATION_REQUIRES_ADJUDICATION"}
    commissions = {r["COMMISSION_OR_SUBSECTOR"] for r in hydraulic if r["COMMISSION_OR_SUBSECTOR"]}
    registry_by_id = {row["EVIDENCE_ID"]: row for row in registry}
    raw_juntas = {r["JUNTA"] for r in hydraulic if r["JUNTA"]}
    normalized_juntas = {
        JUNTA_SOURCE_LABEL_TO_CANONICAL[label]
        for label in raw_juntas if label in JUNTA_SOURCE_LABEL_TO_CANONICAL
    }
    l3_geosnirh_only = 0
    for row in hydraulic:
        if row["SERVICE_RELATION_STATUS"] != "CERTIFIED_EXACT_SERVICE_RELATION":
            continue
        ids = set(filter(None, row["EVIDENCE_IDS"].split(";")))
        independent_l3 = {
            eid for eid in ids
            if eid in registry_by_id
            and registry_by_id[eid]["EVIDENCE_STATUS"] == "CERTIFIED_EXACT_SERVICE_RELATION"
            and registry_by_id[eid]["SOURCE_DOCUMENT_TYPE"] != "OFFICIAL_WFS_CSV_RECORD"
            and registry_by_id[eid]["CLAIM_TYPE"].startswith("L3_")
        }
        l3_geosnirh_only += not bool(independent_l3)
    return {
        "model_n": len(eligibility),
        "province_n": len({r["PROVINCE_NAME"] for r in eligibility}),
        "agency_any": len(agency_any),
        "agency_supported": len(agency_supported),
        "agency_exhaustive": sum(r["EXHAUSTIVENESS_STATUS"] == "COMPLETE_EXHAUSTIVE" for r in agency),
        "agency_rows": len(agency),
        "hyd_any": len(hyd_any),
        "institutional_membership": len(l2_strongest),
        "service_level": len(service),
        "named_service_units": len(named_units),
        "partition_level": 0,
        "geometric_partition": 0,
        "official_area_partition": 0,
        "official_numeric_fraction": sum(r["SERVICE_FRACTION_AVAILABLE"] == "TRUE" for r in hydraulic),
        "service_fractions_invented": sum(bool(r["SERVICE_FRACTION_VALUE"]) for r in hydraulic),
        "presence_only": len(l1_strongest),
        "multi_hyd": len(confirmed | conditional),
        "confirmed_multi": len(confirmed),
        "conditional_multi": len(conditional),
        "false_multi": sum(eligibility_id in FALSE_LADDER_MULTI_IDS and r["DOUBLE_COUNTING_RISK"] != "NO_CONFIRMED_MULTI_SERVICE" for eligibility_id, r in ((row["UBIGEO"], row) for row in eligibility)),
        "hyd_unresolved": sum("UNRESOLVED" in r["HYDRAULIC_MAPPING_STATUS"] for r in eligibility),
        "irrigation_evidence": len(service),
        "operational_systems": len(OPERATIONAL_SYSTEMS),
        "junta_raw_labels": len(raw_juntas),
        "named_juntas": len(normalized_juntas),
        "current_canonical_piura_juntas": len(CURRENT_CANONICAL_PIURA_JUNTAS),
        "historical_junta_labels": len(HISTORICAL_JUNTA_LABELS),
        "non_junta_hydraulic_labels": len(NON_JUNTA_HYDRAULIC_LABELS),
        "cross_temporal_commissions": sum(len(values) for values in CROSS_TEMPORAL_COMMISSION_INVENTORY.values()),
        "current_exhaustive_san_lorenzo_commissions": len(CURRENT_EXHAUSTIVE_SAN_LORENZO_ROSTER),
        "named_commissions": len(commissions),
        "named_blocks": len(NAMED_IRRIGATION_BLOCKS),
        "formalization_raw_names": 1504,
        "l3_geosnirh_only": l3_geosnirh_only,
        "subindex_confirmed": sum(r["DISTRICT_INDEX_STATUS"] == "SUBINDEX_REQUIRED_BY_CONFIRMED_MULTI_SERVICE" for r in eligibility),
        "subindex_conditional": sum(r["DISTRICT_INDEX_STATUS"] == "SUBINDEX_OR_PARTITION_REQUIRED_PENDING_SERVICE_EVIDENCE" for r in eligibility),
        "subindex_potential": sum(r["DISTRICT_INDEX_STATUS"] == "POTENTIAL_SUBINDEX_ONLY" for r in eligibility),
        "agency_coverage_pct": round(len(agency_any) / len(eligibility) * 100, 1),
        "hyd_coverage_pct": round(len(hyd_any) / len(eligibility) * 100, 1),
    }


def run_all_gates() -> dict[str, dict[str, object]]:
    return {
        "checkpoint": checkpoint_gate(), "immutability": immutable_gate(),
        "persistent_scope": persistent_scope_gate(), "schemas": schema_gate(),
        "vocabulary": vocabulary_gate(), "ubigeo": ubigeo_gate(),
        "evidence_ids": evidence_id_gate(), "relationships": relationship_gate(),
        "recovery": recovery_gate(), "firewalls": firewall_gate(), "report": report_gate(),
    }


def main() -> int:
    gates = run_all_gates()
    failures = {name: gate for name, gate in gates.items() if gate["status"] != "PASS"}
    diag = coverage_diagnostics()
    for name, gate in gates.items():
        print(f"{name}={gate['status']}")
    print(f"MODEL_DISTRICT_UNIVERSE_N={diag['model_n']}")
    print(f"ANY_HYDRAULIC_EVIDENCE_N={diag['hyd_any']}")
    print(f"HYDRAULIC_UNRESOLVED_N={diag['hyd_unresolved']}")
    print(f"SERVICE_LEVEL_EVIDENCE_N={diag['service_level']}")
    print(f"NAMED_SERVICE_UNIT_N={diag['named_service_units']}")
    print(f"CURRENT_CANONICAL_PIURA_JUNTAS_N={diag['current_canonical_piura_juntas']}")
    print(f"CROSS_TEMPORAL_COMMISSION_SUBSECTOR_INVENTORY_N={diag['cross_temporal_commissions']}")
    print(f"CURRENT_EXHAUSTIVE_SAN_LORENZO_COMMISSION_N={diag['current_exhaustive_san_lorenzo_commissions']}")
    print(f"L3_GEOSNIRH_ONLY_RELATIONS_N={diag['l3_geosnirh_only']}")
    print(f"CONFIRMED_MULTI_SERVICE_N={diag['confirmed_multi']}")
    print(f"CONDITIONAL_MULTI_RELATION_N={diag['conditional_multi']}")
    print(f"SUBINDEX_CONFIRMED_REQUIRED_N={diag['subindex_confirmed']}")
    print(f"SUBINDEX_OR_PARTITION_CONDITIONAL_N={diag['subindex_conditional']}")
    print(f"POTENTIAL_SUBINDEX_ONLY_N={diag['subindex_potential']}")
    print(f"OFFICIAL_NUMERIC_SERVICE_FRACTION_N={diag['official_numeric_fraction']}")
    print("C0B2_PREFLIGHT=" + ("PASS" if not failures else "FAIL"))
    if failures:
        print(json.dumps(failures, indent=2, sort_keys=True))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
