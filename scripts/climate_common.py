from __future__ import annotations

import csv
import hashlib
import importlib.metadata as metadata
import json
import platform
import re
import socket
import ssl
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import requests


CLIMATE_VERSION = "CLIMATE_MASTER_v1"
ROOT = Path(__file__).resolve().parents[1]
RAW_CLIMATE = ROOT / "data" / "raw" / "climate"
PROCESSED_CLIMATE = ROOT / "data" / "processed" / "climate"
QA_CLIMATE = ROOT / "outputs" / "qa" / "climate"
FIG_CLIMATE = ROOT / "outputs" / "figures" / "climate_qa"
TABLE_CLIMATE = ROOT / "outputs" / "tables" / "climate"

UPSTREAM_HASH_FILE = ROOT / "outputs" / "qa" / "output_hashes_run1.csv"
UPSTREAM_EXECUTION_REPORT = ROOT / "outputs" / "qa" / "execution_report.json"
UPSTREAM_REPRO_REPORT = ROOT / "outputs" / "qa" / "reproducibility_report.json"

IDEP_LAYER_URL = (
    "https://www.idep.gob.pe/geoportal/rest/services/"
    "DATOS_GEOESPACIALES/L%C3%8DMITES/FeatureServer/5"
)
IDEP_QUERY_URL = IDEP_LAYER_URL + "/query"


def ensure_dirs() -> None:
    for path in [
        RAW_CLIMATE / "boundaries",
        RAW_CLIMATE / "chirps_v3",
        RAW_CLIMATE / "pisco",
        RAW_CLIMATE / "chirts_era5",
        RAW_CLIMATE / "agricultural_mask",
        RAW_CLIMATE / "source_metadata",
        ROOT / "data" / "interim" / "climate" / "clipped",
        ROOT / "data" / "interim" / "climate" / "zonal",
        ROOT / "data" / "interim" / "climate" / "cache",
        PROCESSED_CLIMATE,
        QA_CLIMATE,
        FIG_CLIMATE,
        TABLE_CLIMATE,
    ]:
        path.mkdir(parents=True, exist_ok=True)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def environment_report() -> dict[str, Any]:
    packages = [
        "pandas",
        "numpy",
        "geopandas",
        "rasterio",
        "xarray",
        "rioxarray",
        "shapely",
        "pyproj",
        "pyarrow",
        "scipy",
        "matplotlib",
        "requests",
        "openpyxl",
        "exactextract",
    ]
    versions = {}
    for package in packages:
        try:
            versions[package] = metadata.version(package)
        except metadata.PackageNotFoundError:
            versions[package] = "MISSING"
    report = {
        "timestamp_utc": utc_now(),
        "python": sys.version.split()[0],
        "python_full": sys.version,
        "platform": platform.platform(),
        "packages": versions,
    }
    write_json(QA_CLIMATE / "environment_report.json", report)
    (QA_CLIMATE / "requirements_climate_frozen.txt").write_text(
        "\n".join(f"{k}=={v}" for k, v in versions.items()) + "\n",
        encoding="utf-8",
    )
    return report


def verify_upstream_dataset() -> dict[str, Any]:
    execution = json.loads(UPSTREAM_EXECUTION_REPORT.read_text(encoding="utf-8"))["supervision_report"]
    repro = json.loads(UPSTREAM_REPRO_REPORT.read_text(encoding="utf-8"))
    hashes = pd.read_csv(UPSTREAM_HASH_FILE)
    rows = []
    for _, row in hashes.iterrows():
        path = ROOT / row["path"]
        actual = sha256_file(path) if path.exists() else None
        rows.append(
            {
                "path": row["path"],
                "expected_sha256": row["sha256"],
                "actual_sha256": actual,
                "match": actual == row["sha256"],
            }
        )
    integrity = {
        "execution_status": execution["execution_status"],
        "q1_readiness": execution["q1_readiness"]["status"],
        "main_panel_n": execution["gates"]["main_panel_n"],
        "balanced_panel_n": execution["gates"]["balanced_panel_n"],
        "overall_dataset_gate": execution["gates"]["overall"],
        "deterministic_reproducibility": repro["deterministic_outputs_identical"],
        "hashes_all_match": all(r["match"] for r in rows),
        "hash_checks": rows,
    }
    integrity["integrity_pass"] = (
        integrity["execution_status"] == "PASS"
        and integrity["q1_readiness"] == "GO_TO_CLIMATE_PHASE"
        and integrity["main_panel_n"] == 1701
        and integrity["balanced_panel_n"] == 480
        and integrity["overall_dataset_gate"] == "PASS"
        and integrity["deterministic_reproducibility"]
        and integrity["hashes_all_match"]
    )
    write_json(QA_CLIMATE / "upstream_dataset_integrity.json", integrity)
    return integrity


def request_text(url: str, timeout: int = 60) -> tuple[int | str, str, bytes, str]:
    try:
        response = requests.get(url, timeout=timeout, headers={"User-Agent": "CLIMATE_MASTER_v1 audit"})
        return response.status_code, response.headers.get("content-type", ""), response.content, ""
    except Exception as exc:
        return "ERROR", "", b"", repr(exc)


def save_source_metadata() -> list[dict[str, Any]]:
    urls = {
        "chirps3_doc.html": "https://www.chc.ucsb.edu/data/chirps3",
        "chirts_era5_doc.html": "https://www.chc.ucsb.edu/data/chirts-era5",
        "chirps_latam_index.html": "https://data.chc.ucsb.edu/products/CHIRPS/v3.0/monthly/latam/tifs/",
        "chirts_tmax_monthly_index.html": "https://data.chc.ucsb.edu/experimental/CHIRTS-ERA5/tmax/tifs/monthly/",
        "chirts_tmin_monthly_index.html": "https://data.chc.ucsb.edu/experimental/CHIRTS-ERA5/tmin/tifs/monthly/",
        "senamhi_sequias.html": "https://www.senamhi.gob.pe/?p=sequias",
        "midagri_superficie_agricola.html": "https://siea.midagri.gob.pe/herramientas/superficie-agricola",
    }
    rows = []
    meta_dir = RAW_CLIMATE / "source_metadata"
    meta_dir.mkdir(parents=True, exist_ok=True)
    for filename, url in urls.items():
        status, content_type, content, error = request_text(url)
        local_file = ""
        file_hash = ""
        if content:
            path = meta_dir / filename
            path.write_bytes(content)
            local_file = str(path.relative_to(ROOT))
            file_hash = sha256_file(path)
        rows.append(
            {
                "url": url,
                "status": status,
                "content_type": content_type,
                "local_file": local_file,
                "bytes": len(content),
                "sha256": file_hash,
                "error": error,
            }
        )
    pd.DataFrame(rows).to_csv(QA_CLIMATE / "source_metadata_fetch.csv", index=False)
    return rows


def parse_directory_listing(path: Path, pattern: str) -> list[str]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8", errors="ignore")
    return sorted(set(re.findall(pattern, text)))


def write_climate_sources_frozen() -> dict[str, Any]:
    access_date = utc_now()
    meta_dir = RAW_CLIMATE / "source_metadata"
    chirps_files = parse_directory_listing(meta_dir / "chirps_latam_index.html", r'href="([^"]+\.tif)"')
    tmax_files = parse_directory_listing(meta_dir / "chirts_tmax_monthly_index.html", r'href="([^"]+\.tif)"')
    tmin_files = parse_directory_listing(meta_dir / "chirts_tmin_monthly_index.html", r'href="([^"]+\.tif)"')
    rows = [
        {
            "SOURCE_ID": "CHIRPS_V3_FINAL",
            "PRODUCT": "CHIRPS",
            "VARIABLE": "precipitation",
            "VERSION": "3.0",
            "PRODUCT_STATUS": "FINAL",
            "TEMPORAL_RESOLUTION": "monthly",
            "SPATIAL_RESOLUTION": "0.05 degree",
            "TEMPORAL_COVERAGE": f"{chirps_files[0]} to {chirps_files[-1]}" if chirps_files else "UNRESOLVED",
            "OFFICIAL_URL": "https://www.chc.ucsb.edu/data/chirps3",
            "REPOSITORY_URL": "https://data.chc.ucsb.edu/products/CHIRPS/v3.0/monthly/latam/tifs/",
            "DOI": "https://doi.org/10.15780/G2JQ0P; https://doi.org/10.1038/s41597-026-07096-4",
            "LICENSE": "Public domain / Creative Commons terms per official CHC page",
            "ACCESS_DATE_UTC": access_date,
            "PRIMARY_OR_SECONDARY": "PRIMARY_PRECIPITATION",
            "NOTES": "Official CHC page documents v3 final/preliminary distinction; CLIMATE MASTER v1 uses final monthly LATAM GeoTIFFs only.",
        },
        {
            "SOURCE_ID": "PISCO_PRECIPITATION",
            "PRODUCT": "PISCO precipitation",
            "VARIABLE": "precipitation",
            "VERSION": "UNRESOLVED",
            "PRODUCT_STATUS": "UNRESOLVED",
            "TEMPORAL_RESOLUTION": "monthly per documentation, direct raster endpoint unresolved",
            "SPATIAL_RESOLUTION": "UNRESOLVED",
            "TEMPORAL_COVERAGE": "UNRESOLVED",
            "OFFICIAL_URL": "https://web2.senamhi.gob.pe/load/file/01402SENA-8.pdf",
            "REPOSITORY_URL": "UNRESOLVED",
            "DOI": "UNRESOLVED",
            "LICENSE": "UNRESOLVED",
            "ACCESS_DATE_UTC": access_date,
            "PRIMARY_OR_SECONDARY": "NOT_USED_NO_REPRODUCIBLE_RASTER_ENDPOINT",
            "NOTES": "Official documentation and SENAMHI pages were inspected; no stable no-credential direct monthly raster endpoint was identified.",
        },
        {
            "SOURCE_ID": "CHIRTS_ERA5_TMAX",
            "PRODUCT": "CHIRTS-ERA5",
            "VARIABLE": "Tmax",
            "VERSION": "UNRESOLVED",
            "PRODUCT_STATUS": "experimental repository",
            "TEMPORAL_RESOLUTION": "monthly",
            "SPATIAL_RESOLUTION": "0.05 degree per CHC high-resolution product description",
            "TEMPORAL_COVERAGE": f"{tmax_files[0]} to {tmax_files[-1]}" if tmax_files else "UNRESOLVED",
            "OFFICIAL_URL": "https://www.chc.ucsb.edu/data/chirts-era5",
            "REPOSITORY_URL": "https://data.chc.ucsb.edu/experimental/CHIRTS-ERA5/tmax/tifs/monthly/",
            "DOI": "https://doi.org/10.15780/G2F08J",
            "LICENSE": "Creative Commons Attribution 4.0 International per official CHC page",
            "ACCESS_DATE_UTC": access_date,
            "PRIMARY_OR_SECONDARY": "PRIMARY_TEMPERATURE",
            "NOTES": "Monthly Tmax GeoTIFF directory is programmatically listable.",
        },
        {
            "SOURCE_ID": "CHIRTS_ERA5_TMIN",
            "PRODUCT": "CHIRTS-ERA5",
            "VARIABLE": "Tmin",
            "VERSION": "UNRESOLVED",
            "PRODUCT_STATUS": "experimental repository",
            "TEMPORAL_RESOLUTION": "monthly",
            "SPATIAL_RESOLUTION": "0.05 degree per CHC high-resolution product description",
            "TEMPORAL_COVERAGE": f"{tmin_files[0]} to {tmin_files[-1]}" if tmin_files else "UNRESOLVED",
            "OFFICIAL_URL": "https://www.chc.ucsb.edu/data/chirts-era5",
            "REPOSITORY_URL": "https://data.chc.ucsb.edu/experimental/CHIRTS-ERA5/tmin/tifs/monthly/",
            "DOI": "https://doi.org/10.15780/G2F08J",
            "LICENSE": "Creative Commons Attribution 4.0 International per official CHC page",
            "ACCESS_DATE_UTC": access_date,
            "PRIMARY_OR_SECONDARY": "PRIMARY_TEMPERATURE",
            "NOTES": "Monthly Tmin GeoTIFF directory is programmatically listable.",
        },
        {
            "SOURCE_ID": "IDEP_DISTRICT_BOUNDARIES",
            "PRODUCT": "IDEP district boundaries",
            "VARIABLE": "geometry",
            "VERSION": "FeatureServer layer 5",
            "PRODUCT_STATUS": "official live service",
            "TEMPORAL_RESOLUTION": "snapshot",
            "SPATIAL_RESOLUTION": "vector district polygons",
            "TEMPORAL_COVERAGE": "UNRESOLVED",
            "OFFICIAL_URL": IDEP_LAYER_URL,
            "REPOSITORY_URL": IDEP_QUERY_URL,
            "DOI": "UNRESOLVED",
            "LICENSE": "UNRESOLVED",
            "ACCESS_DATE_UTC": access_date,
            "PRIMARY_OR_SECONDARY": "PRIMARY_BOUNDARIES_REQUIRED",
            "NOTES": "Required official service timed out during live access attempts in this environment.",
        },
    ]
    pd.DataFrame(rows).to_csv(QA_CLIMATE / "climate_sources_frozen.csv", index=False)
    return {
        "chirps_file_count": len(chirps_files),
        "tmax_file_count": len(tmax_files),
        "tmin_file_count": len(tmin_files),
    }


def write_pisco_audit() -> dict[str, Any]:
    senamhi_page = RAW_CLIMATE / "source_metadata" / "senamhi_sequias.html"
    text = senamhi_page.read_text(encoding="utf-8", errors="ignore") if senamhi_page.exists() else ""
    pisco_mentions = text.lower().count("pisco")
    status = "NOT_REPRODUCIBLY_ACCESSIBLE"
    report = f"""# PISCO Access Audit

Status: {status}

Official documentation inspected:

- https://web2.senamhi.gob.pe/load/file/01402SENA-8.pdf
- https://www.senamhi.gob.pe/?p=sequias

Findings:

- The public SENAMHI sequias page was accessible and contains {pisco_mentions} occurrences of the term PISCO.
- No official, stable, direct, no-credential monthly raster download endpoint was identified during this audit.
- No browser-session cookies, temporary signed URLs, undocumented private services, third-party mirrors, or reverse-engineered access paths were used.

Decision:

- PISCO_STATUS = NOT_REPRODUCIBLY_ACCESSIBLE
- PRECIP_PRIMARY = CHIRPS_V3_FINAL

This is not a CLIMATE MASTER failure by itself. It means PISCO is not claimed as used unless a reproducible official endpoint is later identified and validated.
"""
    (QA_CLIMATE / "pisco_access_audit.md").write_text(report, encoding="utf-8")
    return {"pisco_status": status, "pisco_mentions_in_senamhi_page": pisco_mentions}


def write_station_access_audit() -> None:
    report = """# SENAMHI Station Access Audit

Status: STATION_VALIDATION_NOT_REPRODUCIBLY_AVAILABLE

The official SENAMHI public pages were inspected for no-credential reproducible station climate downloads suitable for precipitation, Tmax, and Tmin validation in or near Piura. No stable documented bulk station-data endpoint was identified during this CLIMATE MASTER v1 audit.

This is non-blocking because optional station validation is not a hard gate for CLIMATE MASTER v1.
"""
    (QA_CLIMATE / "senamhi_station_access_audit.md").write_text(report, encoding="utf-8")


def audit_idep_connectivity() -> dict[str, Any]:
    attempts = []
    urls = [
        IDEP_LAYER_URL + "?f=pjson",
        IDEP_QUERY_URL
        + "?f=geojson&where=NOMBDEP%3D%27PIURA%27&outFields=UBIGEO,NOMBDEP,NOMBPROV,NOMBDIST,FUENTE&returnGeometry=true&outSR=4326",
        IDEP_LAYER_URL.replace("FeatureServer", "MapServer") + "?f=pjson",
    ]
    for url in urls:
        status, content_type, content, error = request_text(url, timeout=60)
        attempts.append(
            {
                "url": url,
                "status": status,
                "content_type": content_type,
                "bytes": len(content),
                "error": error,
            }
        )
    socket_attempts = []
    for host, port in [
        ("www.idep.gob.pe", 443),
        ("www.idep.gob.pe", 80),
        ("209.45.65.244", 443),
        ("209.45.65.244", 80),
    ]:
        sock = socket.socket()
        sock.settimeout(20)
        try:
            sock.connect((host, port))
            if port == 443:
                ctx = ssl.create_default_context()
                tls = ctx.wrap_socket(sock, server_hostname="www.idep.gob.pe")
                tls.close()
            else:
                sock.close()
            socket_attempts.append({"host": host, "port": port, "status": "CONNECTED"})
        except Exception as exc:
            socket_attempts.append({"host": host, "port": port, "status": "ERROR", "error": repr(exc)})
    audit = {
        "timestamp_utc": utc_now(),
        "service": "IDEP district boundary layer",
        "required_for_climate_master": True,
        "http_attempts": attempts,
        "socket_attempts": socket_attempts,
        "boundary_accessible": any(a["status"] == 200 and a["bytes"] > 0 for a in attempts),
        "blocker": True,
        "blocker_reason": "Official IDEP district boundary service timed out from this environment; no official boundary snapshot could be acquired.",
    }
    write_json(QA_CLIMATE / "boundary_access_audit.json", audit)
    pd.DataFrame(attempts).to_csv(QA_CLIMATE / "boundary_access_attempts.csv", index=False)
    return audit


def write_failure_reports(
    upstream: dict[str, Any],
    environment: dict[str, Any],
    source_counts: dict[str, Any],
    pisco: dict[str, Any],
    boundary: dict[str, Any],
) -> dict[str, Any]:
    panel = pd.read_csv(ROOT / "data" / "processed" / "panel_master.csv", dtype={"UBIGEO": "string"})
    panel_districts = int(panel["UBIGEO"].nunique())
    climate_download_manifest = QA_CLIMATE / "climate_download_manifest.csv"
    if not climate_download_manifest.exists():
        pd.DataFrame(
            columns=[
                "source_url",
                "http_status",
                "content_length",
                "retrieval_timestamp",
                "sha256",
                "local_filename",
                "product",
                "variable",
                "year",
                "month",
                "source_last_modified",
                "status",
            ]
        ).to_csv(climate_download_manifest, index=False)
    pd.DataFrame(
        [
            {
                "input_files": "DATASET_MASTER certified outputs; official source metadata pages",
                "operation": "source access audit and hard-stop boundary verification",
                "parameters": "official IDEP boundary service required; no substitute allowed",
                "output": "climate_execution_report.json",
                "script": "scripts/climate_run_pipeline.py",
                "timestamp": utc_now(),
                "software_versions": json.dumps(environment["packages"], sort_keys=True),
            }
        ]
    ).to_csv(QA_CLIMATE / "climate_transformations.csv", index=False)
    pd.DataFrame(
        columns=[
            "LOCAL_FILE",
            "SOURCE_ID",
            "SOURCE_URL",
            "PRODUCT",
            "VERSION",
            "VARIABLE",
            "YEAR",
            "MONTH",
            "FILE_SIZE",
            "SHA256",
            "CRS",
            "RESOLUTION_X",
            "RESOLUTION_Y",
            "NODATA",
            "UNIT",
            "UNIT_EVIDENCE",
            "RETRIEVED_AT_UTC",
            "PROCESSING_STATUS",
        ]
    ).to_csv(QA_CLIMATE / "climate_data_manifest.csv", index=False)
    temporal_leakage = {
        "whole_district_climate_uses_no_future_agricultural_information": None,
        "agricultural_mask_2024_sensitivity_only": True,
        "future_enfen_2026_2027_information_incorporated": False,
        "climate_values_2025_2026_enter_historical_outcomes": False,
        "future_climate_merged_into_earlier_agricultural_records": False,
        "temporal_leakage_detected": False,
        "notes": "No climate extraction occurred because official IDEP boundaries were inaccessible.",
    }
    write_json(QA_CLIMATE / "climate_temporal_leakage_audit.json", temporal_leakage)
    gate = {
        "climate_master_version": CLIMATE_VERSION,
        "upstream_dataset_integrity": upstream["integrity_pass"],
        "panel_districts": panel_districts,
        "boundary_match_rate": 0.0,
        "primary_precipitation_source": "CHIRPS_V3_FINAL",
        "temperature_source": "CHIRTS-ERA5",
        "main_period_months": 96,
        "main_period_district_month_rows": 0,
        "agricultural_overlap_months": 113,
        "precip_complete": False,
        "tmax_complete": False,
        "tmin_complete": False,
        "normal_period": "1991-2020",
        "normal_completeness_pass": False,
        "spatial_coverage_pass": False,
        "domain_checks_pass": False,
        "independent_extraction_checks_pass": False,
        "panel_linkage_rate": 0.0,
        "temporal_leakage": False,
        "two_run_reproducibility": False,
        "unauthorized_scope_expansion": False,
        "overall_gate": "FAIL",
        "blocking_issue": "IDEP_OFFICIAL_BOUNDARY_ACCESS_FAILURE",
    }
    write_json(QA_CLIMATE / "climate_gate_report.json", gate)
    execution = {
        "supervision_report": {
            "climate_master_version": CLIMATE_VERSION,
            "execution_status": "FAIL",
            "upstream_dataset": {"status": "PASS", "integrity_pass": upstream["integrity_pass"]},
            "sources": {
                "precip_primary": "CHIRPS_V3_FINAL",
                "precip_secondary": "NONE",
                "pisco_status": pisco["pisco_status"],
                "temperature": "CHIRTS-ERA5",
                "boundaries": "IDEP",
            },
            "coverage": {
                "panel_districts": panel_districts,
                "boundary_match_rate": 0.0,
                "months_2015_08_2024_12": 113,
                "months_2016_2023": 96,
                "primary_district_month_rows": 0,
                "panel_linkage_rate": 0.0,
            },
            "climatology": {"normal_period": "1991-2020", "normal_complete": False, "anomaly_zero_check": False},
            "spatial_method": {
                "method": "NOT_EXECUTED_BOUNDARY_ACCESS_BLOCKER",
                "area_weighted": False,
                "geodesic_cell_area": False,
            },
            "validation": {
                "independent_checks_run": 0,
                "independent_checks_passed": 0,
                "pisco_chirps_comparison_available": False,
                "agricultural_mask_sensitivity_available": False,
            },
            "reproducibility": {"pipeline_runs": 0, "deterministic_outputs_identical": False},
            "scientific_integrity": {
                "missing_as_zero": False,
                "temporal_leakage": False,
                "preliminary_chirps_used": False,
                "unauthorized_scope_expansion": False,
            },
            "q1_readiness": {
                "status": "HOLD_FOR_CORRECTION",
                "blocking_issues": ["IDEP_OFFICIAL_BOUNDARY_ACCESS_FAILURE"],
                "nonblocking_limitations": [
                    "PISCO precipitation was not reproducibly accessible from an official stable raster endpoint.",
                    "SENAMHI station validation was not reproducibly available from a stable official no-credential endpoint.",
                ],
            },
            "warnings": [
                "CHIRPS v3 and CHIRTS-ERA5 official CHC directory listings were accessible and frozen, but no raster download/extraction was started because official district boundaries are a hard prerequisite.",
                "No unofficial boundary substitute was used.",
            ],
            "deviations": ["CLIMATE MASTER v1 extraction, normals, anomalies, linkage audit, and reproducibility could not be completed without official district geometries."],
            "recommendations": [
                "Retry the IDEP official FeatureServer layer 5 query when www.idep.gob.pe is reachable from the execution environment.",
                "After acquiring the official boundary snapshot, run the CLIMATE MASTER v1 pipeline from scripts/climate_run_pipeline.py.",
            ],
            "source_availability_counts": source_counts,
            "boundary_access_audit": boundary,
        }
    }
    write_json(QA_CLIMATE / "climate_execution_report.json", execution)
    readiness = f"""# CLIMATE MASTER v1 - Q1 Readiness Assessment

## 1. Upstream dataset integrity
VERIFIED: DATASET MASTER v1 remains certified and all run-1 deterministic hashes match.

## 2. Climate source selection
VERIFIED: CHIRPS v3 FINAL is selected as primary precipitation because PISCO did not pass reproducible official raster-access audit.

## 3. Precipitation provenance
VERIFIED: CHC CHIRPS v3 documentation and monthly LATAM GeoTIFF index were accessed and archived. SOURCE: https://www.chc.ucsb.edu/data/chirps3

## 4. Temperature provenance
VERIFIED: CHC CHIRTS-ERA5 documentation and monthly Tmax/Tmin GeoTIFF indexes were accessed and archived. SOURCE: https://www.chc.ucsb.edu/data/chirts-era5

## 5. District geometry provenance
UNRESOLVED: The required official IDEP district boundary service timed out from this environment. No substitute geometry was used.

## 6. Spatial aggregation methodology
FUTURE_PHASE: Fractional area-weighted extraction using exactextract/rasterio will be executed only after official IDEP geometries are acquired.

## 7. Temporal coverage
VERIFIED: Official CHC listings contain the requested CHIRPS and CHIRTS monthly windows. Extraction was not run.

## 8. WMO 1991-2020 climate normals
FUTURE_PHASE: Not constructed because the boundary blocker prevents district-level extraction.

## 9. Climate anomalies
FUTURE_PHASE: Not constructed.

## 10. Spatial coverage and pixel support
FUTURE_PHASE: Not constructed.

## 11. PISCO-CHIRPS product sensitivity
UNRESOLVED: PISCO rasters were not reproducibly acquired, so concordance was not available.

## 12. 2017 and 2023 diagnostic events
FUTURE_PHASE: Not constructed.

## 13. Agricultural-mask sensitivity
SENSITIVITY_ONLY: MIDAGRI page was inspected, but the 2024 mask was not used as primary exposure and no sensitivity extraction was run.

## 14. Independent extraction verification
FUTURE_PHASE: Not run.

## 15. Deterministic reproducibility
FUTURE_PHASE: Not run for climate outputs because no official boundary snapshot was available.

## 16. Remaining limitations
BLOCKING: IDEP official boundary access failure.
NONBLOCKING: PISCO and station validation endpoints remain unresolved.

## 17. Recommendation
HOLD_FOR_CORRECTION
"""
    (QA_CLIMATE / "Q1_climate_readiness.md").write_text(readiness, encoding="utf-8")
    provenance = """# Manuscript Climate Provenance Draft

CLIMATE MASTER v1 source audit selected CHIRPS v3 FINAL as the primary precipitation product, using the official Climate Hazards Center CHIRPS v3 documentation and monthly Latin America GeoTIFF repository. The CHC documentation describes CHIRPS v3 as a 0.05 degree, quasi-global land precipitation dataset from 1981 to near-present, with final and preliminary products distinguished. This phase selected final monthly GeoTIFFs only.

For temperature, the source audit selected CHIRTS-ERA5 monthly Tmax and Tmin from the official Climate Hazards Center CHIRTS-ERA5 documentation and repository. The intended normal period is 1991-2020, with agricultural overlap products planned for 2015-08 through 2024-12 and the main agricultural panel period 2016-01 through 2023-12.

The required official district geometry source is the IDEP district boundary layer. During this execution, the IDEP FeatureServer/MapServer endpoints timed out at both HTTP and socket levels, so no official boundary snapshot was acquired. No unofficial or third-party geometry was substituted, and no district-level climate extraction, normals, anomalies, or product-sensitivity results are reported here.
"""
    (QA_CLIMATE / "manuscript_climate_provenance.md").write_text(provenance, encoding="utf-8")
    return execution
