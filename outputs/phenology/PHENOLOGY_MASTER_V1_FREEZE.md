# PHENOLOGY MASTER v1 Freeze

PHENOLOGY_MASTER_V1: PASS
STAGE_A: PASS_CLOSED
EVIDENCE_ADJUDICATION: PASS
EVIDENCE_ARCHITECTURE_FREEZE: PASS_FROZEN
CLIMATE_EXPOSURE_BUILD: READY
ECONOMETRICS: BLOCKED
ENSO_SCENARIOS: BLOCKED
MEAN_CVAR: BLOCKED

This certificate freezes the phenological evidence and architecture for PHENOLOGY MASTER v1. The canonical machine-readable freeze artifact is `data/processed/phenology/phenology_windows_frozen.csv`.

## Frozen Architectures

ARROZ uses a sowing-cohort-weighted architecture anchored on SIEMBRA. For PHENOLOGY MASTER v1, SIEMBRA is interpreted as definitive-field establishment / transplant proxy. The canonical biological flowering window is 95-110 days after the anchor. The m+3:m+4 month range is only its monthly operational envelope.

MAIZ AMARILLO DURO uses a sowing-cohort-weighted architecture anchored on SIEMBRA. The frozen exposure window is m+1:m+3 relative to the sowing cohort.

MANGO uses a seasonal perennial architecture. The frozen calendar window is May-June in calendar year t. No t-1 to t rollover is applied.

LIMON SUTIL uses a recurrent perennial broad architecture. Both January-December of year t and January-December of year t-1 are retained as explicit logical windows.

PLATANOS Y BANANAS uses a multistage continuous architecture. Both January-December of year t and January-December of year t-1 are retained as explicit logical windows.

No yield, price, production outcome, regression, p-value, or downstream optimization result was used to select or alter these frozen windows.

Climate Exposure Build has not been executed by this freeze. It is READY to begin from the frozen phenology windows.

Changing `data/processed/phenology/phenology_windows_frozen.csv` after this freeze requires a formal reopening of PHENOLOGY MASTER and a new PHENOLOGY MASTER version.
