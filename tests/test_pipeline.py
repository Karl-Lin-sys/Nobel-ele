"""Safety and leakage regressions. Japanese strings here are synthetic fixtures."""

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

import corpus
import evaluate


ROOT = Path(__file__).resolve().parents[1]
BASE = next(corpus.read_jsonl(ROOT / "data/processed/corpus.jsonl"))


def fixture(stream, seconds, text, topic="general", near=None, split="unassigned"):
    item = deepcopy(BASE)
    stamp = f"{seconds // 60}:{seconds % 60:02d}"
    item.update(id=f"{stream}:{seconds:06d}", stream_id=stream, timestamp=stamp,
                start_seconds=seconds, text_en_original=text, text_en_ca=text,
                source_line=f"{stamp} [EN] {text}", topic=topic, genre="stream_chat",
                claim_flags=[], near_duplicate_group=near, split=split,
                exact_text_sha256=corpus.text_sha256(text),
                edited_text_sha256=corpus.text_sha256(text))
    return item


def alignment(item):
    return {"id": item["id"], "source_ja": "合成テスト用の文章です。",
            "source_url": "https://example.invalid/synthetic-fixture",
            "source_start_seconds": item["start_seconds"],
            "source_end_seconds": item["start_seconds"] + 1,
            "target_en_ca": item["text_en_ca"], "alignment_reviewed": True,
            "translation_reviewed": True, "rights_reviewed": True,
            "reviewer": "synthetic-test-reviewer", "fact_status": "unverified",
            "fact_evidence": []}


def judgement(item, adequacy):
    return {"id": item["id"], "adequacy": adequacy, "terminology_correct": None,
            "reviewer": "synthetic-test-reviewer", "prediction_en_ca": "Test prediction.",
            "reviewed_against_source": True}


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)

    def rows(self, name, items):
        path = self.directory / name
        path.write_text("".join(corpus.encode_json(x) + "\n" for x in items), encoding="utf-8")
        return path

    def test_real_input_roundtrip_and_counts(self):
        report = corpus.build_corpus(ROOT / "data/raw/translations.txt",
            ROOT / "data/editorial_review.jsonl", ROOT / "data/provenance.json",
            self.directory / "rebuilt")
        self.assertEqual((report["records"], report["unique_normalised_original_texts"]), (47, 46))
        rebuilt = self.directory / "rebuilt/corpus.jsonl"
        self.assertEqual(rebuilt.read_bytes(), (ROOT / "data/processed/corpus.jsonl").read_bytes())
        raw = [line for _, line in corpus.bounded_lines(ROOT / "data/raw/translations.txt")]
        records = list(corpus.read_jsonl(rebuilt))
        self.assertEqual([row["source_line"] for row in records], raw)
        self.assertTrue(all(row["japanese_source"] is None for row in records))

    def test_timestamp_validation_and_hour(self):
        self.assertEqual(corpus.timestamp_seconds("1:07:11"), 4031)
        for stamp in ("1:60:00", "4:60", "-1:05", "1:2", "00:00:01:02"):
            with self.subTest(stamp=stamp), self.assertRaises(ValueError):
                corpus.timestamp_seconds(stamp)

    def test_invalid_json_is_not_silently_accepted(self):
        for text in ('{"id":1,"id":2}\n', '{"value":NaN}\n', '[]\n', '\n'):
            path = self.directory / "bad.jsonl"
            path.write_text(text, encoding="utf-8")
            with self.subTest(text=text), self.assertRaises(ValueError):
                list(corpus.read_jsonl(path))

    def test_unicode_and_line_bound(self):
        path = self.rows("unicode.jsonl", [{"text": "honour — metres 日本語 👏"}])
        self.assertEqual(next(corpus.read_jsonl(path))["text"], "honour — metres 日本語 👏")
        path.write_bytes(b"x" * (corpus.MAX_LINE_BYTES + 1))
        with self.assertRaises(ValueError):
            list(corpus.bounded_lines(path))

    def test_failed_write_keeps_previous_output_and_removes_temporary_file(self):
        path = self.directory / "result.jsonl"
        path.write_text("previous output", encoding="utf-8")
        with self.assertRaises(ValueError):
            with corpus.atomic_text(path) as handle:
                handle.write("incomplete")
                raise ValueError("failure")
        self.assertEqual(path.read_text(), "previous output")
        self.assertEqual(list(self.directory.iterdir()), [path])

    def test_edited_text_tampering_is_detected(self):
        row = fixture("test", 1, "Original")
        row["text_en_ca"] = "Changed without updating the checksum"
        with self.assertRaises(ValueError):
            corpus.audit_corpus(self.rows("tampered.jsonl", [row]))

    def test_single_stream_split_is_refused(self):
        with self.assertRaisesRegex(ValueError, "3 independent"):
            corpus.split_corpus(ROOT / "data/processed/corpus.jsonl", self.directory / "split")
        self.assertFalse((self.directory / "split").exists())

    def test_duplicates_connect_separate_streams(self):
        rows = [fixture(f"stream{i}", 1, "Same sentence.") for i in range(3)]
        with self.assertRaisesRegex(ValueError, "3 independent"):
            corpus.split_corpus(self.rows("overlap.jsonl", rows), self.directory / "split")

    def test_transitive_groups_stay_together_and_splits_are_reproducible(self):
        rows = [fixture("a", 1, "Exact sentence"), fixture("b", 1, "EXACT sentence"),
                fixture("b", 2, "New words", near="shared-concept"),
                fixture("c", 1, "Different wording", near="shared-concept"),
                fixture("d", 1, "Independent d"), fixture("e", 1, "Independent e")]
        path = self.rows("multiple.jsonl", rows)
        one = corpus.split_corpus(path, self.directory / "split1")
        two = corpus.split_corpus(path, self.directory / "split2")
        self.assertEqual(one, two)
        assignments = one["stream_assignments"]
        self.assertEqual(assignments["a"], assignments["b"])
        self.assertEqual(assignments["b"], assignments["c"])
        self.assertEqual(set(assignments.values()), {"train", "test", "validation"})
        evaluate.check_disjoint(self.directory / "split1/train.jsonl",
                                self.directory / "split1/test.jsonl")

    def test_real_corpus_cannot_export_fake_training_pairs(self):
        output = self.directory / "sft.jsonl"
        with self.assertRaisesRegex(ValueError, "no reviewed"):
            corpus.export_sft(ROOT / "data/processed/corpus.jsonl",
                              ROOT / "data/processed/alignment_template.jsonl", output)
        self.assertFalse(output.exists())

    def test_unreviewed_source_or_target_blocks_export(self):
        row = fixture("fixture", 1, "Fixture sentence")
        path = self.rows("corpus.jsonl", [row])
        for field, value in (("source_ja", None), ("alignment_reviewed", False),
            ("rights_reviewed", False), ("target_en_ca", "Different target"),
            ("source_end_seconds", 0), ("source_start_seconds", True)):
            review = alignment(row)
            review[field] = value
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "no reviewed"):
                corpus.export_sft(path, self.rows("align.jsonl", [review]),
                                  self.directory / "out.jsonl")

    def test_scientific_claim_needs_explicit_evidence(self):
        row = fixture("fixture", 1, "Synthetic claim")
        row["claim_flags"] = ["scientific_claim_unverified"]
        path = self.rows("corpus.jsonl", [row])
        review = alignment(row)
        with self.assertRaisesRegex(ValueError, "scientific_claims_unverified"):
            corpus.export_sft(path, self.rows("align.jsonl", [review]), self.directory / "out.jsonl")
        review.update(fact_status="verified", fact_evidence=["https://example.invalid/evidence"])
        result = corpus.export_sft(path, self.rows("align.jsonl", [review]), self.directory / "out.jsonl")
        self.assertEqual(result["exported_pairs"], 1)

    def test_export_deduplicates_pairs_in_both_formats(self):
        rows = [fixture("fixture", 1, "Fixture sentence"), fixture("fixture", 2, "Fixture sentence")]
        path = self.rows("corpus.jsonl", rows)
        reviews = self.rows("align.jsonl", [alignment(row) for row in rows])
        for format_name in ("prompt-completion", "messages"):
            output = self.directory / f"{format_name}.jsonl"
            report = corpus.export_sft(path, reviews, output, format_name)
            self.assertEqual(report["exported_pairs"], 1)
            self.assertEqual(report["skipped_reason_counts_nonexclusive"]["duplicate_pair"], 1)
            record = next(corpus.read_jsonl(output))
            self.assertEqual(set(record), {"messages"} if format_name == "messages"
                             else {"prompt", "completion"})

    def test_unknown_alignment_id_rolls_back_successful_partial_export(self):
        row = fixture("fixture", 1, "Fixture sentence")
        output = self.directory / "existing.jsonl"
        output.write_text("previous output", encoding="utf-8")
        extra = alignment(fixture("unknown", 1, "Unknown"))
        with self.assertRaisesRegex(ValueError, "ids absent"):
            corpus.export_sft(self.rows("corpus.jsonl", [row]),
                self.rows("align.jsonl", [alignment(row), extra]), output)
        self.assertEqual(output.read_text(), "previous output")

    def test_export_cannot_overwrite_input(self):
        row = fixture("fixture", 1, "Fixture sentence")
        path = self.rows("corpus.jsonl", [row])
        with self.assertRaisesRegex(ValueError, "overwrite"):
            corpus.export_sft(path, self.rows("align.jsonl", [alignment(row)]), path)

    def test_test_data_overlapping_train_is_rejected(self):
        training = self.rows("train.jsonl", [fixture("train", 1, "Sentence", split="train")])
        for test in (fixture("train", 2, "New sentence", split="test"),
                     fixture("other", 1, "SENTENCE", split="test")):
            with self.subTest(test=test["id"]), self.assertRaisesRegex(ValueError, "overlap"):
                evaluate.check_disjoint(training, self.rows("test.jsonl", [test]))

    def test_macro_reports_minor_topic_instead_of_hiding_it(self):
        train = self.rows("train.jsonl", [fixture("train", 1, "Training only", split="train")])
        rows = [fixture("heldout", i, f"Test sentence {i}", "physics", split="test")
                for i in range(1, 10)] + [fixture("heldout", 10, "Rare topic", "medicine", split="test")]
        score = evaluate.score_human_reviews(train, self.rows("test.jsonl", rows),
            self.rows("align.jsonl", [alignment(row) for row in rows]),
            self.rows("judge.jsonl", [judgement(row, 4 if row["topic"] == "physics" else 0)
                                      for row in rows]))
        self.assertEqual(score["micro"]["mean_adequacy_0_to_4"], 3.6)
        self.assertEqual(score["macro_topic_mean_adequacy_observed_topics"], 2.0)
        self.assertEqual(score["by_topic"]["medicine"]["n"], 1)
        self.assertIn("chemistry", score["missing_topics"])
        self.assertFalse(score["bias_eliminated"])

    def test_missing_review_cannot_shrink_evaluation_denominator(self):
        train = self.rows("train.jsonl", [fixture("train", 1, "Training only", split="train")])
        rows = [fixture("heldout", 1, "Test 1", split="test"),
                fixture("heldout", 2, "Test 2", split="test")]
        with self.assertRaisesRegex(ValueError, "denominator"):
            evaluate.score_human_reviews(train, self.rows("test.jsonl", rows),
                self.rows("align.jsonl", [alignment(row) for row in rows]),
                self.rows("judge.jsonl", [judgement(rows[0], 4)]))


if __name__ == "__main__":
    unittest.main()
