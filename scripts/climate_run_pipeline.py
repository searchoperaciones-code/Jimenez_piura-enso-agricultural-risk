from __future__ import annotations

from climate_v1_1_pipeline import QA_CLIMATE, main


if __name__ == "__main__":
    try:
        exit_code = main()
    except Exception:
        (QA_CLIMATE / "climate_pipeline_exit_code.txt").write_text("1\n", encoding="utf-8")
        raise
    (QA_CLIMATE / "climate_pipeline_exit_code.txt").write_text(f"{exit_code}\n", encoding="utf-8")
    raise SystemExit(exit_code)
