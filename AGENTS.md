# CLIMATE MASTER v1 RULES

# PROJECT FREEZE STATE

DATASET MASTER v1 - FROZEN
CLIMATE MASTER v1.1 - FROZEN
PHENOLOGY MASTER v1 - NOT STARTED

No agent may modify frozen scientific outputs without explicit instruction to reopen a phase.

No p-value-driven phenological-window selection.
No outcome-driven window search.
No causal claim unless identification is separately established.
No automatic outlier deletion.
No assumed YIELD_RAW physical unit.

1. Official sources only.
2. Final climate products preferred over preliminary products.
3. No silent substitution between datasets.
4. Every external file must have provenance and SHA-256.
5. Raw externally downloaded files are immutable.
6. No raster may be resampled unless scientifically necessary and explicitly documented.
7. Prefer transforming vector geometries into raster CRS rather than resampling climate values.
8. Missing raster values must never be silently replaced with zero.
9. Precipitation cannot be negative.
10. For temperature, Tmin must not exceed Tmax after aggregation.
11. Spatial coverage must be quantified for every district-month.
12. Whole-district climate is the primary historical exposure geography.
13. A 2024 agricultural-area mask may only be used as a sensitivity analysis, not as the primary historical exposure for 2016-2023.
14. PISCO versus CHIRPS is product-sensitivity/concordance, not fully independent validation.
15. Final phenological windows are NOT selected during this phase.
16. WMO 1991-2020 is the primary climatological-normal period.
17. No later econometric or optimization method is allowed in CLIMATE MASTER v1.
18. Deterministic outputs must reproduce byte-for-byte when inputs and environment are unchanged.
