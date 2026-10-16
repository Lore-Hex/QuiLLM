import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("bench_runner", ROOT / "scripts/freedombench_ollama.py")
bench = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bench)


class FreedomBenchTests(unittest.TestCase):
    def test_all_questions_unique_and_prompt_contains_options(self):
        rows = bench.question_rows()
        self.assertEqual(len(rows), 60)
        self.assertEqual(len({r["id"] for r in rows}), 60)
        self.assertEqual(len({r["topic"] for r in rows}), 12)
        for row in rows:
            for letter, text in row["options"].items():
                self.assertIn(f"{letter}) {text}", row["prompt"])

    def test_wrong_answers_are_never_retried(self):
        calls = []
        q = bench.question_rows()[0]
        wrong = next(c for c in "ABCD" if c != q["correct"])
        def call(*args):
            calls.append(args)
            return {"done": True, "response": f"ANSWER: {wrong}", "done_reason": "stop"}
        row = bench.run_one("local", "model", q, call=call)
        self.assertEqual(len(calls), 1)
        self.assertEqual(row["empty_attempts"], 0)
        self.assertTrue(calls[0][2]["raw"])
        self.assertNotIn("correct", calls[0][2])

    def test_empty_answers_have_five_saved_attempts(self):
        row = bench.run_one("local", "model", bench.question_rows()[0],
            call=lambda *a: {"done": True, "response": "", "done_reason": "length"})
        self.assertEqual(len(row["attempts"]), 5)
        self.assertEqual(row["truncated_attempts"], 5)

    def test_infrastructure_errors_are_not_refusals(self):
        def call(*args):
            raise TimeoutError("private endpoint")
        q = bench.question_rows()[0]
        row = bench.run_one("local", "model", q, call=call)
        result = bench.summarize({"questions": [q], "responses": [row]})
        self.assertEqual(result["errors"], 1)
        self.assertEqual(result["refused"], 0)
        self.assertIsNone(result["score_percent"])
        self.assertNotIn("private", json.dumps(row))

    def test_missing_rows_do_not_receive_full_score(self):
        result = bench.summarize({"questions": bench.question_rows(), "responses": []})
        self.assertFalse(result["complete"])
        self.assertIsNone(result["score_percent"])

    def test_no_verbatim_question_overlap_with_archived_training(self):
        normalize = lambda value: re.sub(r"\s+", " ", value).strip().casefold()
        strings = set()
        for path in (ROOT / "datasets").rglob("*.jsonl"):
            for line in path.read_text().splitlines():
                if not line.strip():
                    continue
                for value in json.loads(line).values():
                    if isinstance(value, str):
                        strings.add(normalize(value))
        for row in bench.question_rows():
            self.assertNotIn(normalize(row["question"]), strings)

    def test_duplicate_and_unknown_answers_are_rejected(self):
        q = bench.question_rows()[0]
        row = {"model": "m", "question_id": q["id"], "output": "ANSWER: A"}
        with self.assertRaises(ValueError):
            bench.summarize({"questions": [q], "responses": [row, row]})
        with self.assertRaises(ValueError):
            bench.summarize({"questions": [q], "responses": [{**row, "question_id": "unknown"}]})

    def test_generated_tables_match_all_four_runs(self):
        result = subprocess.run([sys.executable, str(ROOT / "scripts/report_freedombench.py"), "--check"], capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr.decode())

    def test_published_results_rescore_and_match_sources(self):
        expected_hashes = {
            "quillm-4b.json": "337ea93b7c8a99cebd818e8e80d1dcc39473b97a09164e2fa55c1b9cc0db4b8d",
            "quillm-1.7b.json": "a64125577d135a27c83e1f48e99516ffb13e0f3c3d2f330b950a0b5364dc22ed",
            "qwen3-4b.json": "163553aea1b1de62de7c5eb2ef5afb756b4b3133308d9ae7e42e951d8d696ef5",
            "qwen3-1.7b.json": "4287aca1b231f27dbd20012c4bf9693c89b6c849dc02b7027096da54564d4037",
        }
        for path in (ROOT / "reports/freedombench").rglob("*.json"):
            report = json.loads(path.read_text())
            self.assertEqual(report["model_identity"]["weight_sha256"], expected_hashes[path.name])
            self.assertEqual(report["runner_sha256"], bench.sha256_file(ROOT / "scripts/freedombench_ollama.py"))
            self.assertEqual(bench.summarize(report), report["summary"])
            if "mac-interrupted" not in path.parts:
                self.assertTrue(report["summary"]["complete"])
            self.assertEqual(report["questions"], bench.question_rows())
            self.assertEqual(report["options"], bench.OPTIONS)
            for name, digest in report["source_hashes"].items():
                self.assertEqual(bench.sha256_file(bench.VENDOR / name), digest)


if __name__ == "__main__":
    unittest.main()
