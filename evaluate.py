"""Summarise complete human reviews on genuinely held-out translation data.

This is an original diagnostic rubric, not BLEU, COMET, a classifier metric,
or an implementation of Paloma/ConStat. It does not claim that bias is removed.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

from corpus import (TOPICS, GENRES, alignment_blockers, audit_corpus, encode_json,
                    file_sha256, load_index, read_jsonl, write_json)


def check_disjoint(training: Path, testing: Path) -> dict:
    audit_corpus(training)
    audit_corpus(testing)
    train_streams, train_keys = set(), set()
    for item in read_jsonl(training):
        if item["split"] != "train":
            raise ValueError("training manifest contains a non-train row")
        train_streams.add(item["stream_id"])
        train_keys.update((("text", item["exact_text_sha256"]),
                           ("text", item["edited_text_sha256"])))
        if item.get("near_duplicate_group"):
            train_keys.add(("near", item["near_duplicate_group"]))
    test_streams = set()
    for item in read_jsonl(testing):
        if item["split"] != "test":
            raise ValueError("test manifest contains a non-test row")
        if item["stream_id"] in train_streams:
            raise ValueError("train/test stream overlap")
        keys = [("text", item["exact_text_sha256"]),
                ("text", item["edited_text_sha256"])]
        if item.get("near_duplicate_group"):
            keys.append(("near", item["near_duplicate_group"]))
        if any(key in train_keys for key in keys):
            raise ValueError("train/test exact or curated near-duplicate overlap")
        test_streams.add(item["stream_id"])
    return {"training_streams": len(train_streams), "test_streams": len(test_streams),
            "checked_overlap": "stream, normalised original/edited text, curated near group",
            "pretraining_contamination": "unknown"}


def summarise(rows: list[dict]) -> dict:
    count = len(rows)
    adequacy_sum = adequate = term_n = term_correct = 0
    for row in rows:
        adequacy_sum += row["adequacy"]
        adequate += row["adequacy"] >= 3
        if row["terminology_correct"] is not None:
            term_n += 1
            term_correct += row["terminology_correct"]
    return {"n": count,
            "mean_adequacy_0_to_4": adequacy_sum / count if count else None,
            "adequate_rate_threshold_3": adequate / count if count else None,
            "terminology_n": term_n,
            "terminology_correct_rate": term_correct / term_n if term_n else None}


def score_human_reviews(training: Path, testing: Path,
                       alignments_path: Path, judgements_path: Path) -> dict:
    checks = check_disjoint(training, testing)
    alignments = load_index(alignments_path, "id")
    judgements = load_index(judgements_path, "id")
    all_rows = []
    by_topic, by_genre, by_stream = defaultdict(list), defaultdict(list), defaultdict(list)
    ids = set()
    for item in read_jsonl(testing):
        identity = item["id"]
        ids.add(identity)
        if identity not in alignments or alignment_blockers(item, alignments[identity]):
            raise ValueError(f"unreviewed test source/reference: {identity}")
        if identity not in judgements:
            raise ValueError(f"missing judgement: {identity}; denominator cannot shrink")
        row = judgements[identity]
        if type(row.get("adequacy")) is not int or not 0 <= row["adequacy"] <= 4:
            raise ValueError("adequacy must be an integer from 0 to 4")
        if "terminology_correct" not in row or (row["terminology_correct"] is not None
                                                and type(row["terminology_correct"]) is not bool):
            raise ValueError("terminology_correct must be true, false, or null")
        for field in ("reviewer", "prediction_en_ca"):
            if not isinstance(row.get(field), str) or not row[field].strip():
                raise ValueError(f"missing {field} in human judgement")
        if row.get("reviewed_against_source") is not True:
            raise ValueError("human judgement must be reviewed against the Japanese source")
        all_rows.append(row)
        by_topic[item["topic"]].append(row)
        by_genre[item["genre"]].append(row)
        by_stream[item["stream_id"]].append(row)
    if set(judgements) != ids or set(alignments) != ids:
        raise ValueError("test judgements and test alignments must match every test id exactly")
    topic_stats = {topic: summarise(by_topic[topic]) for topic in sorted(TOPICS)}
    genre_stats = {genre: summarise(by_genre[genre]) for genre in sorted(GENRES)}
    stream_stats = {stream: summarise(rows) for stream, rows in sorted(by_stream.items())}
    present = [stats["mean_adequacy_0_to_4"] for stats in topic_stats.values() if stats["n"]]
    return {"checks": checks, "micro": summarise(all_rows), "by_topic": topic_stats,
            "by_genre": genre_stats, "by_stream": stream_stats,
            "macro_topic_mean_adequacy_observed_topics": sum(present) / len(present),
            "macro_stream_mean_adequacy": sum(stats["mean_adequacy_0_to_4"]
                for stats in stream_stats.values()) / len(stream_stats),
            "missing_topics": [topic for topic, stats in topic_stats.items() if not stats["n"]],
            "confidence_interval": None, "bias_eliminated": False,
            "limitations": ["An ordinal human rubric is not a calibrated semantic metric.",
                            "Reviewer error and selection bias can remain.",
                            "Macro averages cover observed groups only.",
                            "No claim about unseen domains or base-model contamination."],
            "input_sha256": {"train": file_sha256(training), "test": file_sha256(testing),
                "alignments": file_sha256(alignments_path),
                "judgements": file_sha256(judgements_path)}}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", type=Path, required=True)
    parser.add_argument("--test", type=Path, required=True)
    parser.add_argument("--alignments", type=Path, required=True)
    parser.add_argument("--judgements", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = score_human_reviews(args.train, args.test, args.alignments, args.judgements)
        write_json(args.output, result)
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(2, f"Error: {error}\n")
    print(encode_json(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
