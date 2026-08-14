# CLIMATE EXPOSURE SPEC v1 FREEZE

CLIMATE_EXPOSURE_SPEC_V1: PASS
SPECIFICATION_STATUS: PASS_FROZEN
DIRECTOR_FREEZE_DECISION: PASS
UPSTREAM_PHENOLOGY: PASS_FROZEN
UPSTREAM_CLIMATE: PASS_FROZEN
TRANSIENT_TIME_BASIS: AGRICULTURAL_CAMPAIGN_AUG_JUL
PERENNIAL_TIME_BASIS: CALENDAR_YEAR
TRANSIENT_COHORT_LAYER: READY
STRICT_CAMPAIGN_LAYER: READY_AS_AUDIT
PRIMARY_TRANSIENT_ECONOMETRIC_ROLE: UNRESOLVED
EXPOSURE_DATA_BUILD: READY_FROM_FROZEN_SPEC
TRANSIENT_OUTCOME_MASTER: BLOCKED
ECONOMETRICS: BLOCKED
ENSO_SCENARIOS: BLOCKED
MEAN_CVAR: BLOCKED

The machine-readable frozen specification is `config/climate_exposure/climate_exposure_spec_v1.json`. Subsequent Climate Exposure Build work must conform exactly to this frozen contract.

## Rationale

The transient campaign-year time basis was selected from institutional and statistical evidence before campaign feasibility was calculated. Gobierno Regional Piura / DRA Piura and MIDAGRI / SIEA define agricultural campaign practice as August through July for crop sowing statistics and transient crop planning. The campaign-year selection was not based on outcome data, model fit, regression performance, or sample-size maximization.

Transient crops use `AGRICULTURAL_CAMPAIGN_AUG_JUL`. Perennial crops retain `CALENDAR_YEAR`. The specification does not force all five crops onto one temporal basis.

## Diagnostics

Calendar strict reference-year diagnostic:

`23 / 745 = 3.09%`

Campaign strict diagnostic:

`38 / 745 = 5.10%`

Rice campaign diagnostic:

`31 / 340 = 9.12%`

Maiz amarillo duro campaign diagnostic:

`7 / 405 = 1.73%`

These diagnostic Ns did not select the time basis and must not be used to alter the attribution rule.

## Status

The transient cohort exposure ledger is the primary Stage-B data product. The strict campaign aggregation layer is an audit and strict-identification layer only. No climate exposure data have been built by this freeze. No transient campaign outcome has been calculated. Econometrics, ENSO scenarios, and mean-CVaR optimization remain blocked.
