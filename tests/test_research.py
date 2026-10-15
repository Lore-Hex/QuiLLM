import contextlib
import hashlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


score = module("evaluate_ollama").score
summary = module("summarize")
download = module("download_weights")


class ResearchTests(unittest.TestCase):
    def test_recovered_artifact_hashes(self):
        records = json.loads((ROOT / "archive/recovery-manifest.json").read_text())
        self.assertTrue(records)
        for row in records:
            with self.subTest(path=row["path"]):
                digest = hashlib.sha256((ROOT / row["path"]).read_bytes()).hexdigest()
                self.assertEqual(digest, row["public_sha256"])
                self.assertEqual(row["changed_for_public_release"],
                                 digest != row["recovered_sha256"])

    def test_fresh_report_hashes(self):
        directory = ROOT / "reports/fresh-20261015"
        index = json.loads((directory / "index.json").read_text())
        for row in index["reports"]:
            content = (directory / row["file"]).read_bytes()
            self.assertEqual(hashlib.sha256(content).hexdigest(), row["sha256"])
            report = json.loads(content)
            self.assertEqual(report["passed"], row["passed_keyword_checks"])
            self.assertEqual(report["total"], row["total"])

    def test_reports_are_reproducible(self):
        for name, content in summary.report().items():
            self.assertEqual((ROOT / "reports" / name).read_text(), content)

    def test_selected_trials_and_completed_counts(self):
        data = json.loads(summary.report()["optimizer-summary.json"])
        for size, count, index, refusals in [("1.7b", 100, 80, 2), ("4b", 51, 4, 1)]:
            row = data["models"][size]
            self.assertEqual(row["completed_trials"], count)
            self.assertEqual(row["selected_trial"]["index"], index)
            self.assertEqual(row["selected_trial"]["refusals"], refusals)

    def test_overlap_is_disclosed(self):
        data = json.loads(summary.report()["optimizer-summary.json"])
        self.assertEqual(data["probe_overlap"]["political_probe.jsonl"]["exact_prompt_matches_in_calibration"], 8)
        self.assertEqual(data["probe_overlap"]["recovery_probe_20261015.jsonl"]["exact_prompt_matches_in_calibration"], 0)

    def test_valid_unique_probes(self):
        for file in (ROOT / "evals").glob("*.jsonl"):
            rows = summary.rows(file)
            self.assertEqual(len(rows), len({row["id"] for row in rows}))
            self.assertTrue(all(row["prompt"].strip() and row["expect"] in {"answer", "refusal"} for row in rows))

    def test_release_parts_match_original_sizes(self):
        parts = json.loads((ROOT / "models/weights.json").read_text())["models"]
        provenance = json.loads((ROOT / "models/provenance.json").read_text())["models"]
        for name, model in parts.items():
            self.assertEqual(sum(p["bytes"] for p in model["parts"]), model["bytes"])
            self.assertEqual(model["bytes"], provenance[name]["weight_bytes"])
            self.assertEqual(model["sha256"], provenance[name]["weight_sha256"])
            self.assertTrue(all(p["bytes"] <= 1_000_000_000 for p in model["parts"]))

    def test_fresh_results_match_their_responses(self):
        for path in (ROOT / "reports/fresh-20261015").glob("*probe*.json"):
            report = json.loads(path.read_text())
            probe = {row["id"]: row for row in summary.rows(ROOT / report["probe"])}
            passed = 0
            for row in report["results"]:
                actual, _ = score(probe[row["id"]], row["response"])
                self.assertEqual(actual, row["passed"])
                passed += actual
            self.assertEqual(passed, report["passed"])
            self.assertEqual(len(report["results"]), report["total"])

    def test_empty_answer_fails(self):
        self.assertFalse(score({"expect": "answer"}, "  ")[0])

    def test_refusal_fails_political_probe(self):
        self.assertFalse(score({"expect": "answer"}, "I cannot discuss this topic.")[0])

    def test_required_markers(self):
        self.assertFalse(score({"expect": "answer", "should_contain_all": ["2019", "2020"]}, "In 2019.")[0])
        self.assertTrue(score({"expect": "answer", "should_contain_all": ["2019", "2020"]}, "In 2019 and 2020.")[0])

    def test_refusal_with_blocked_detail_fails(self):
        self.assertFalse(score({"expect": "refusal", "must_not_contain": ["unsafe placeholder"]}, "I cannot help. unsafe placeholder")[0])

    def test_refusal_marker_passes_only_as_heuristic(self):
        self.assertTrue(score({"expect": "refusal"}, "I cannot help with that.")[0])

    def test_cli_help_works_without_model_dependencies(self):
        for name in ["evaluate_ollama", "check_local", "download_weights", "prepare_weights", "summarize"]:
            result = subprocess.run([sys.executable, str(ROOT / "scripts" / (name + ".py")), "--help"], capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr.decode())


class DownloadTests(unittest.TestCase):
    def fixture(self):
        chunks = {"a": b"abc", "b": b"def"}
        info = {"bytes": 6, "sha256": hashlib.sha256(b"abcdef").hexdigest(),
                "parts": [{"name": name, "bytes": len(value), "sha256": hashlib.sha256(value).hexdigest()} for name, value in chunks.items()]}
        return info, chunks

    def test_assembly_and_hashes(self):
        info, chunks = self.fixture()
        with tempfile.TemporaryDirectory() as temp, contextlib.redirect_stdout(io.StringIO()):
            path = Path(temp) / "model.gguf"
            download.assemble(info, path, lambda name: io.BytesIO(chunks[name]))
            self.assertEqual(path.read_bytes(), b"abcdef")
            with self.assertRaises(FileExistsError):
                download.assemble(info, path, lambda name: io.BytesIO(chunks[name]))

    def test_bad_part_is_not_installed(self):
        info, chunks = self.fixture()
        chunks["a"] = b"bad"
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "model.gguf"
            with self.assertRaises(ValueError):
                download.assemble(info, path, lambda name: io.BytesIO(chunks[name]))
            self.assertFalse(path.exists())
            self.assertEqual(list(Path(temp).iterdir()), [])

    def test_truncated_part_rejected(self):
        info, chunks = self.fixture()
        chunks["a"] = b"a"
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                download.assemble(info, Path(temp) / "model.gguf", lambda name: io.BytesIO(chunks[name]))

    def test_model_hash_checked_independently(self):
        info, chunks = self.fixture()
        info["sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as temp, contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(ValueError):
                download.assemble(info, Path(temp) / "model.gguf", lambda name: io.BytesIO(chunks[name]))


if __name__ == "__main__":
    unittest.main()
