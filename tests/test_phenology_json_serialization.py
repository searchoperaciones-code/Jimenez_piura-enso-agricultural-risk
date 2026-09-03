from __future__ import annotations

import hashlib
import inspect
import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import audit_phenology_stage_a  # noqa: E402
import phenology_stage_a  # noqa: E402


Writer = Callable[[Path, dict[str, Any]], None]
WRITERS: tuple[tuple[str, Writer], ...] = (
    ("phenology_stage_a", phenology_stage_a.write_json),
    ("audit_phenology_stage_a", audit_phenology_stage_a.write_json),
)
CANONICAL_QA_FILES = (
    "outputs/phenology/qa/evidence_gate_report.json",
    "outputs/phenology/qa/no_outcome_snooping_audit.json",
    "outputs/phenology/qa/phenology_stage_a_reproducibility_report.json",
    "outputs/phenology/qa/stage_a_gate_report.json",
    "outputs/phenology/qa/stage_a_schema.json",
    "outputs/phenology/qa/temporal_source_integrity_report.json",
    "outputs/phenology/qa/upstream_integrity_report.json",
)


def serialized_bytes(writer: Writer, payload: dict[str, Any], name: str = "result.json") -> bytes:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / name
        writer(path, payload)
        return path.read_bytes()


class PhenologyJsonSerializationTests(unittest.TestCase):
    def test_01_simple_payload_has_exact_bytes(self) -> None:
        payload = {"z": 2, "a": 1}
        expected = b'{\n  "a": 1,\n  "z": 2\n}\n'
        for name, writer in WRITERS:
            with self.subTest(writer=name):
                self.assertEqual(serialized_bytes(writer, payload), expected)

    def test_02_serialization_is_lf_only_with_one_final_lf(self) -> None:
        for name, writer in WRITERS:
            with self.subTest(writer=name):
                content = serialized_bytes(writer, {"line": "value"})
                self.assertNotIn(b"\r\n", content)
                self.assertNotIn(b"\r", content)
                self.assertTrue(content.endswith(b"\n"))
                self.assertFalse(content.endswith(b"\n\n"))

    def test_03_non_ascii_payload_preserves_default_json_escaping(self) -> None:
        payload = {
            "crops": ["Ma\u00edz", "Lim\u00f3n"],
            "event": "El Ni\u00f1o",
            "place": "Piura",
        }
        expected = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
        for name, writer in WRITERS:
            with self.subTest(writer=name):
                content = serialized_bytes(writer, payload)
                self.assertEqual(content, expected)
                self.assertIn(b"Ma\\u00edz", content)
                self.assertIn(b"Lim\\u00f3n", content)
                self.assertIn(b"El Ni\\u00f1o", content)

    def test_04_sorted_key_order_is_stable(self) -> None:
        payload = {"middle": 2, "last": 3, "first": 1}
        for name, writer in WRITERS:
            with self.subTest(writer=name):
                content = serialized_bytes(writer, payload)
                self.assertLess(content.index(b'"first"'), content.index(b'"last"'))
                self.assertLess(content.index(b'"last"'), content.index(b'"middle"'))

    def test_05_both_writers_emit_identical_bytes(self) -> None:
        payload = {"nested": {"b": 2, "a": 1}, "status": "PASS"}
        outputs = [serialized_bytes(writer, payload) for _, writer in WRITERS]
        self.assertEqual(outputs[0], outputs[1])

    def test_06_all_frozen_json_objects_round_trip_to_canonical_bytes(self) -> None:
        for relative in CANONICAL_QA_FILES:
            canonical = (ROOT / relative).read_bytes()
            payload = json.loads(canonical.decode("utf-8"))
            for name, writer in WRITERS:
                with self.subTest(path=relative, writer=name):
                    self.assertEqual(serialized_bytes(writer, payload), canonical)

    def test_07_repeated_writes_have_identical_sha256(self) -> None:
        payload = {"repeatability": True, "values": [3, 2, 1]}
        for name, writer in WRITERS:
            with self.subTest(writer=name):
                first = serialized_bytes(writer, payload, "first.json")
                second = serialized_bytes(writer, payload, "second.json")
                self.assertEqual(hashlib.sha256(first).hexdigest(), hashlib.sha256(second).hexdigest())

    def test_08_writers_use_explicit_bytes_not_platform_newlines(self) -> None:
        for name, writer in WRITERS:
            with self.subTest(writer=name):
                source = inspect.getsource(writer)
                self.assertIn(".write_bytes(", source)
                self.assertNotIn(".write_text(", source)
                self.assertNotIn("os.linesep", source)


if __name__ == "__main__":
    unittest.main()
