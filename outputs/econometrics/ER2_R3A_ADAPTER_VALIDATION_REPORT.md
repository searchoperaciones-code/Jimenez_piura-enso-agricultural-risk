# ER2 R3A Named-Coefficient WCR Adapter Validation v1

SYNTHETIC DATA ONLY. No real outcomes or real R3 execution.

VERDICT = ER2_R3A_HOLD_CONTRAST_PERMUTATION_DISAGREEMENT

## Prespecified synthetic design

Seed 2026090501; 16 synthetic districts x 8 periods; three- and six-regressor full models.
Unequal fixed coefficients, district/period FE, AR(1) synthetic noise and district-specific time slopes.
Specification SHA-256: 1f2d1457deb942045e2f59287274a195c86a9da54feddd42c4e3012b92183479
B=2001; PCG64 seed=20260903; Rademacher batches=1000+1000+1; atol=rtol=1e-10.
The exact observed-statistic gate is separate from the tolerance diagnostic. No rounding to manufacture equivalence.

## Three independent paths

A: named permutation adapter. B: explicit permutation and frozen ED1 first-coefficient API.
C: original-order one-hot KKT restriction, independent full-design OLS/CR2 bootstrap.
Read-only frame tracing captures the frozen engine counts and draws; no RNG calls are inserted.
The original rounded ED1 p-value is preserved in the adapter API; exact finite p uses captured integer counts.

## Positional certification

| Size | Position | A/B | A/C | A/C t exact | A/C t absolute error | Exceedances A/B/C |
| --- | --- | --- | --- | --- | --- | --- |
| 3 | 0 | PASS | HOLD | False | 4.218847493575595e-15 | 930/930/930 |
| 3 | 1 | PASS | HOLD | False | 2.6645352591003757e-15 | 165/165/165 |
| 3 | 2 | PASS | HOLD | False | 6.039613253960852e-14 | 0/0/0 |
| 6 | 0 | PASS | HOLD | False | 1.5543122344752192e-15 | 144/144/144 |
| 6 | 1 | PASS | HOLD | False | 3.1086244689504383e-15 | 328/328/328 |
| 6 | 2 | PASS | HOLD | False | 5.684341886080802e-14 | 29/29/29 |
| 6 | 3 | PASS | HOLD | False | 1.5987211554602254e-14 | 2/2/2 |
| 6 | 4 | PASS | HOLD | False | 2.6645352591003757e-14 | 0/0/0 |
| 6 | 5 | PASS | HOLD | False | 1.4210854715202004e-14 | 1/1/1 |

## Joint noninterference

Architecture 3: HOLD; observed exact=False; error=6.146194664324867e-13; p exact=True.
Architecture 6: HOLD; observed exact=False; error=1.9895196601282805e-13; p exact=True.

## Firewalls and reproducibility

Invalid synthetic replications: 0
REAL_OUTCOME_VALUES_READ=FALSE; REAL_R3_EXECUTED=FALSE; REAL_BOOTSTRAP_REPLICATIONS_EXECUTED=0.
No result-specific branches. No real coefficient values or p-values copied. No real Holm.
Future real R3 remains B=9999, seed=20260903, district-clustered, with the complete frozen physical-anomaly model.
Any invalid draw means HOLD; no dropping, replacement, redraw or effective-B correction.
R3/R4/R5/R6 execution is NOT_AUTHORIZED. Primary ER1 is not replaced.
Two independent synthetic validation processes: PASS.
Input identities and all three rendered output bytes must agree. No timestamps or local paths.

## Methodological references

The frozen full-design CR2 path is retained. General CR2 background: https://jepusto.com/posts/Pusto-Tipton-2018-Theorem-2-redux/
Restricted wild-bootstrap background: https://journals.sagepub.com/doi/abs/10.1177/1536867X19830877
These references do not replace or amend the frozen ED1 implementation.

NEXT_ACTION=RETURN_TO_SCIENTIFIC_DIRECTOR_FOR_R3A_FREEZE_DECISION_IF_PASS
