# PISCO Access Audit

Status: NOT_REPRODUCIBLY_ACCESSIBLE

Official documentation inspected:

- https://web2.senamhi.gob.pe/load/file/01402SENA-8.pdf
- https://www.senamhi.gob.pe/?p=sequias

Findings:

- The public SENAMHI sequias page was accessible and contains 8 occurrences of the term PISCO.
- No official, stable, direct, no-credential monthly raster download endpoint was identified during this audit.
- No browser-session cookies, temporary signed URLs, undocumented private services, third-party mirrors, or reverse-engineered access paths were used.

Decision:

- PISCO_STATUS = NOT_REPRODUCIBLY_ACCESSIBLE
- PRECIP_PRIMARY = CHIRPS_V3_FINAL

This is not a CLIMATE MASTER failure by itself. It means PISCO is not claimed as used unless a reproducible official endpoint is later identified and validated.
