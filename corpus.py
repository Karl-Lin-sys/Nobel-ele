"""Build and audit a small, traceable text corpus. Python 3.10+, no dependencies.

No speech recognition, translation, fact verification, or model training occurs.
See docs/complexity.md for the cost of every production function.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from contextlib import ExitStack, contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Iterator
import unicodedata


MAX_LINE_BYTES = 1_048_576
STAMP = re.compile(r"(?:[0-9]{1,3}:)?[0-9]{1,3}:[0-9]{2}\Z")
TOPICS = {"general", "chemistry", "medicine", "physics"}
GENRES = {"stream_chat", "award_claim", "science_explanation", "mixed_dialogue"}
PARTITIONS = {"unassigned", "train", "validation", "test"}
FACT_FLAGS = {"award_claim_unverified", "award_description_unverified",
              "award_schedule_unverified", "scientific_claim_unverified",
              "quantity_requires_scope", "cost_currency_year_unverified",
              "absolute_wording_requires_review", "causal_oversimplification_possible"}


def bounded_lines(path: Path) -> Iterator[tuple[int, str]]:
    """Read UTF-8 lines with a hard per-line memory bound; reject blank lines."""
    with path.open("rb") as handle:
        number = 0
        while True:
            raw = handle.readline(MAX_LINE_BYTES + 1)
            if not raw:
                break
            number += 1
            if len(raw) > MAX_LINE_BYTES:
                raise ValueError(f"{path}:{number}: line exceeds {MAX_LINE_BYTES} bytes")
            line = raw.decode("utf-8").rstrip("\r\n")
            if not line.strip():
                raise ValueError(f"{path}:{number}: blank line")
            yield number, line


def unique_object(pairs: list[tuple[str, object]]) -> dict:
    """Reject duplicate JSON keys instead of silently accepting the last one."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant: {value}")


def read_jsonl(path: Path) -> Iterator[dict]:
    for number, line in bounded_lines(path):
        try:
            item = json.loads(line, object_pairs_hook=unique_object,
                              parse_constant=reject_constant)
            if not isinstance(item, dict):
                raise ValueError("each line must be an object")
        except (ValueError, RecursionError) as error:
            raise ValueError(f"{path}:{number}: {error}") from error
        yield item


def encode_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False,
                      separators=(",", ":"))


@contextmanager
def atomic_text(path: Path):
    """Replace one complete output only after a successful write; clean up on error."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="\n",
                                         dir=path.parent, delete=False) as handle:
            temporary = Path(handle.name)
            yield handle
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def write_json(path: Path, value: object) -> None:
    with atomic_text(path) as handle:
        handle.write(encode_json(value) + "\n")


def file_sha256(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65_536), b""):
            result.update(chunk)
    return result.hexdigest()


def normalise_text(text: str) -> str:
    """Conservative duplicate key only; never use this as the displayed text."""
    text = unicodedata.normalize("NFKC", text).replace("’", "'")
    return " ".join(text.casefold().split())


def text_sha256(text: str) -> str:
    return hashlib.sha256(normalise_text(text).encode("utf-8")).hexdigest()


def timestamp_seconds(stamp: str) -> int:
    if not STAMP.fullmatch(stamp):
        raise ValueError(f"invalid timestamp: {stamp!r}")
    parts = [int(part) for part in stamp.split(":")]
    if parts[-1] >= 60 or (len(parts) == 3 and parts[-2] >= 60):
        raise ValueError(f"invalid timestamp: {stamp!r}")
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    return parts[0] * 3600 + parts[1] * 60 + parts[2]


def parse_line(line: str) -> tuple[str, int, str]:
    stamp, separator, text = line.partition(" [EN] ")
    if not separator or not text.strip():
        raise ValueError("expected TIMESTAMP [EN] non-empty English text")
    return stamp, timestamp_seconds(stamp), text


def load_index(path: Path, key: str) -> dict[str, dict]:
    result = {}
    for item in read_jsonl(path):
        identity = item.get(key)
        if not isinstance(identity, str) or not identity or identity in result:
            raise ValueError(f"{path}: missing or duplicate {key}: {identity!r}")
        result[identity] = item
    return result


def make_records(raw: Path, reviews: dict[str, dict], metadata: dict) -> Iterator[dict]:
    stream_id = metadata.get("stream_id")
    if not isinstance(stream_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", stream_id):
        raise ValueError("stream_id must be a non-empty simple identifier")
    raw_digest = file_sha256(raw)
    seen = set()
    previous = -1
    for number, line in bounded_lines(raw):
        stamp, seconds, original = parse_line(line)
        if seconds <= previous or stamp in seen:
            raise ValueError(f"{raw}:{number}: timestamps must strictly increase")
        previous = seconds
        seen.add(stamp)
        if stamp not in reviews:
            raise ValueError(f"no annotation for {stamp}")
        review = reviews[stamp]
        cleaned = review.get("text_en_ca", original)
        if not isinstance(cleaned, str) or not cleaned.strip():
            raise ValueError(f"invalid edited text for {stamp}")
        if review.get("topic") not in TOPICS or review.get("genre") not in GENRES:
            raise ValueError(f"invalid topic or genre for {stamp}")
        flags = review.get("claim_flags", [])
        near = review.get("near_duplicate_group")
        if not isinstance(flags, list) or any(not isinstance(x, str) for x in flags):
            raise ValueError(f"invalid claim flags for {stamp}")
        if near is not None and (not isinstance(near, str) or not near):
            raise ValueError(f"invalid near-duplicate group for {stamp}")
        yield {
            "schema_version": "1.0", "id": f"{stream_id}:{seconds:06d}",
            "stream_id": stream_id, "timestamp": stamp, "start_seconds": seconds,
            "end_seconds": None, "source_line_number": number, "source_line": line,
            "input_sha256": raw_digest, "source_url": metadata.get("source_url"),
            "stream_date": metadata.get("stream_date"),
            "text_en_original": original, "text_en_ca": cleaned,
            "editorial_changed": cleaned != original,
            "edit_note": review.get("edit_note", "No editorial change."),
            "language": "en-CA", "language_tag_basis": "requested_editorial_target",
            "japanese_source": None, "alignment_status": "missing_source",
            "topic": review["topic"], "genre": review["genre"],
            "annotation_origin": "assistant_manual_triage_not_human_gold",
            "claim_flags": flags, "fact_status": "unverified" if flags else "not_assessed",
            "language_review_status": "not_verified_against_source_audio",
            "rights_status": "not_documented", "training_eligible": False,
            "exact_text_sha256": text_sha256(original),
            "edited_text_sha256": text_sha256(cleaned),
            "near_duplicate_group": near, "split": "unassigned",
            "speaker_attribution": "Sopia and/or chat as reported by submitter",
            "speaker_identity_verified": False,
        }
    if not seen:
        raise ValueError("empty transcript")
    if seen != set(reviews):
        raise ValueError("annotations contain timestamps absent from the transcript")


def validate_record(item: dict) -> None:
    required = {"id", "stream_id", "timestamp", "start_seconds", "input_sha256", "text_en_original",
                "text_en_ca", "topic", "genre", "claim_flags", "split",
                "exact_text_sha256", "edited_text_sha256", "training_eligible"}
    if not required <= item.keys():
        raise ValueError("incomplete canonical record")
    for field in ("id", "stream_id", "text_en_original", "text_en_ca"):
        if not isinstance(item[field], str) or not item[field].strip():
            raise ValueError(f"invalid {field}")
    seconds = timestamp_seconds(item["timestamp"])
    if type(item["start_seconds"]) is not int or item["start_seconds"] != seconds:
        raise ValueError("timestamp and start_seconds disagree")
    if item["id"] != f"{item['stream_id']}:{seconds:06d}":
        raise ValueError("record id disagrees with stream/timestamp")
    if item["topic"] not in TOPICS or item["genre"] not in GENRES:
        raise ValueError("unknown topic or genre")
    if item["split"] not in PARTITIONS:
        raise ValueError("unknown partition")
    if item["exact_text_sha256"] != text_sha256(item["text_en_original"]):
        raise ValueError("original text checksum mismatch")
    if item["edited_text_sha256"] != text_sha256(item["text_en_ca"]):
        raise ValueError("edited text checksum mismatch")
    if item["training_eligible"] is not False:
        raise ValueError("canonical transcript must remain an unapproved archive")
    if not isinstance(item["claim_flags"], list) or any(
            not isinstance(flag, str) for flag in item["claim_flags"]):
        raise ValueError("claim_flags must be a list of strings")
    near = item.get("near_duplicate_group")
    if near is not None and (not isinstance(near, str) or not near):
        raise ValueError("invalid near-duplicate group")


def audit_corpus(path: Path) -> dict:
    ids, streams, digests = set(), set(), set()
    exact, near = defaultdict(list), defaultdict(list)
    topics, genres, claims = Counter(), Counter(), Counter()
    edits, last = 0, {}
    for item in read_jsonl(path):
        validate_record(item)
        if item["id"] in ids:
            raise ValueError(f"duplicate record id: {item['id']}")
        stream = item["stream_id"]
        if item["start_seconds"] <= last.get(stream, -1):
            raise ValueError(f"non-increasing timestamps in {stream}")
        last[stream] = item["start_seconds"]
        ids.add(item["id"])
        streams.add(stream)
        digests.add(item["input_sha256"])
        exact[item["exact_text_sha256"]].append(item["id"])
        if item.get("near_duplicate_group"):
            near[item["near_duplicate_group"]].append(item["id"])
        topics[item["topic"]] += 1
        genres[item["genre"]] += 1
        claims.update(item["claim_flags"])
        edits += item["text_en_original"] != item["text_en_ca"]
    if not ids:
        raise ValueError("empty corpus")
    return {
        "records": len(ids), "independent_streams": len(streams),
        "unique_normalised_original_texts": len(exact),
        "extra_exact_duplicate_rows": len(ids) - len(exact),
        "exact_duplicate_groups": [rows for rows in exact.values() if len(rows) > 1],
        "curated_near_duplicate_groups": {key: rows for key, rows in near.items()
                                           if len(rows) > 1},
        "topic_counts": dict(topics), "genre_counts": dict(genres),
        "claim_flag_counts": dict(claims), "editorial_edits": edits,
        "input_sha256": sorted(digests), "corpus_sha256": file_sha256(path),
        "approved_translation_pairs": 0, "model_training_performed": False,
        "model_metrics": None, "bias_eliminated": False,
        "split_policy": "hold out independent streams and shared duplicate components",
        "limitations": ["No Japanese source lines or audio were supplied.",
                        "No independent human quality review was supplied.",
                        "Scientific and award claims are not verified.",
                        "A single selected stream cannot estimate generalisation."],
    }


def build_corpus(raw: Path, reviews_path: Path, metadata_path: Path, output: Path) -> dict:
    reviews = load_index(reviews_path, "timestamp")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"),
                          object_pairs_hook=unique_object, parse_constant=reject_constant)
    output.mkdir(parents=True, exist_ok=True)
    corpus_path = output / "corpus.jsonl"
    with atomic_text(corpus_path) as handle:
        for item in make_records(raw, reviews, metadata):
            handle.write(encode_json(item) + "\n")
    report = audit_corpus(corpus_path)
    write_json(output / "audit.json", report)
    with atomic_text(output / "alignment_template.jsonl") as handle:
        for item in read_jsonl(corpus_path):
            row = {"id": item["id"], "source_ja": None, "source_url": None,
                   "source_start_seconds": item["start_seconds"],
                   "source_end_seconds": None, "target_en_ca": item["text_en_ca"],
                   "alignment_reviewed": False, "translation_reviewed": False,
                   "rights_reviewed": False, "reviewer": None,
                   "fact_status": "unverified", "fact_evidence": []}
            handle.write(encode_json(row) + "\n")
    return report


def find_root(parent: dict[str, str], key: str) -> str:
    root = key
    while parent[root] != root:
        root = parent[root]
    while parent[key] != key:
        next_key = parent[key]
        parent[key] = root
        key = next_key
    return root


def union_streams(parent: dict[str, str], sizes: dict[str, int], a: str, b: str) -> None:
    a, b = find_root(parent, a), find_root(parent, b)
    if a == b:
        return
    if sizes[a] < sizes[b]:
        a, b = b, a
    parent[b] = a
    sizes[a] += sizes[b]


def split_corpus(path: Path, output: Path, seed: str = "nobel-v1") -> dict:
    """Two-pass grouping; refuse fewer than three independent components."""
    audit_corpus(path)
    digest = file_sha256(path)
    parent, sizes, owners = {}, {}, {}
    for item in read_jsonl(path):
        stream = item["stream_id"]
        parent.setdefault(stream, stream)
        sizes.setdefault(stream, 1)
        keys = [("text", item["exact_text_sha256"]),
                ("text", item["edited_text_sha256"])]
        if item.get("near_duplicate_group"):
            keys.append(("near", item["near_duplicate_group"]))
        for key in keys:
            if key in owners:
                union_streams(parent, sizes, stream, owners[key])
            else:
                owners[key] = stream
    components = defaultdict(list)
    for stream in sorted(parent):
        components[find_root(parent, stream)].append(stream)
    ordered = sorted(components, key=lambda root: hashlib.sha256(
        (seed + "\0" + encode_json(components[root])).encode("utf-8")).hexdigest())
    if len(ordered) < 3:
        raise ValueError("need at least 3 independent stream/duplicate components; "
                         "do not split this single stream into pretend test data")
    held = max(1, len(ordered) // 10)
    by_root = {root: "test" if i < held else "validation" if i < 2 * held else "train"
               for i, root in enumerate(ordered)}
    assigned = {stream: by_root[find_root(parent, stream)] for stream in parent}
    counts = {name: Counter() for name in ("train", "validation", "test")}
    with ExitStack() as stack:
        handles = {name: stack.enter_context(atomic_text(output / f"{name}.jsonl"))
                   for name in counts}
        for item in read_jsonl(path):
            partition = assigned[item["stream_id"]]
            item["split"] = partition
            handles[partition].write(encode_json(item) + "\n")
            counts[partition][item["topic"]] += 1
        if file_sha256(path) != digest:
            raise ValueError("corpus changed while splitting")
    report = {"seed": seed, "input_sha256": digest,
              "independent_components": len(ordered), "stream_assignments": assigned,
              "topic_counts": {name: dict(count) for name, count in counts.items()},
              "balance_guaranteed": False, "pretraining_contamination_known": False}
    write_json(output / "split_report.json", report)
    return report


def alignment_blockers(item: dict, alignment: dict) -> list[str]:
    blockers = []
    for field in ("alignment_reviewed", "translation_reviewed", "rights_reviewed"):
        if alignment.get(field) is not True:
            blockers.append(field)
    for field in ("source_ja", "source_url", "reviewer"):
        if not isinstance(alignment.get(field), str) or not alignment[field].strip():
            blockers.append(field)
    if not isinstance(alignment.get("source_url"), str) or not re.match(
            r"https?://\S+\Z", alignment["source_url"]):
        blockers.append("source_url_format")
    start, end = alignment.get("source_start_seconds"), alignment.get("source_end_seconds")
    if type(start) is not int or start != item["start_seconds"]:
        blockers.append("source_start_seconds")
    if type(end) is not int or type(start) is not int or end <= start:
        blockers.append("source_end_seconds")
    if alignment.get("target_en_ca") != item["text_en_ca"]:
        blockers.append("target_mismatch")
    if FACT_FLAGS.intersection(item["claim_flags"]):
        evidence = alignment.get("fact_evidence")
        if alignment.get("fact_status") != "verified" or not isinstance(evidence, list) \
                or not evidence or any(not isinstance(x, str) or not re.match(
                    r"https?://\S+\Z", x) for x in evidence):
            blockers.append("scientific_claims_unverified")
    return blockers


def export_sft(corpus: Path, alignments_path: Path, output: Path,
               format_name: str = "prompt-completion", partition: str = "unassigned") -> dict:
    if format_name not in {"prompt-completion", "messages"} or partition not in PARTITIONS:
        raise ValueError("unknown export format or partition")
    if output.resolve() in {corpus.resolve(), alignments_path.resolve()}:
        raise ValueError("export output must not overwrite its inputs")
    audit_corpus(corpus)
    alignments = load_index(alignments_path, "id")
    seen_ids, seen_pairs = set(), set()
    skipped = Counter()
    emitted = 0
    with atomic_text(output) as handle:
        for item in read_jsonl(corpus):
            seen_ids.add(item["id"])
            if item["split"] != partition:
                skipped["different_partition"] += 1
                continue
            alignment = alignments.get(item["id"])
            if alignment is None:
                skipped["missing_alignment"] += 1
                continue
            blockers = alignment_blockers(item, alignment)
            if blockers:
                skipped.update(blockers)
                continue
            pair = hashlib.sha256(encode_json([normalise_text(alignment["source_ja"]),
                normalise_text(item["text_en_ca"])]).encode("utf-8")).hexdigest()
            if pair in seen_pairs:
                skipped["duplicate_pair"] += 1
                continue
            seen_pairs.add(pair)
            if format_name == "prompt-completion":
                row = {"prompt": "Translate this Japanese text into Canadian English:\n"
                       + alignment["source_ja"], "completion": item["text_en_ca"]}
            else:
                row = {"messages": [
                    {"role": "system", "content": "Translate Japanese into Canadian English."},
                    {"role": "user", "content": alignment["source_ja"]},
                    {"role": "assistant", "content": item["text_en_ca"]}]}
            handle.write(encode_json(row) + "\n")
            emitted += 1
        if set(alignments) - seen_ids:
            raise ValueError("alignment file contains ids absent from this corpus")
        if emitted == 0:
            raise ValueError("no reviewed translation pairs; export refused: "
                             + encode_json(dict(skipped)))
    report = {"exported_pairs": emitted, "format": format_name, "partition": partition,
              "skipped_reason_counts_nonexclusive": dict(skipped),
              "corpus_sha256": file_sha256(corpus),
              "alignments_sha256": file_sha256(alignments_path),
              "output_sha256": file_sha256(output),
              "review_basis": "human attestations, not automated proof",
              "generalisation_estimate": None}
    write_json(output.with_suffix(".report.json"), report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build")
    build.add_argument("--raw", type=Path, default=Path("data/raw/translations.txt"))
    build.add_argument("--reviews", type=Path, default=Path("data/editorial_review.jsonl"))
    build.add_argument("--metadata", type=Path, default=Path("data/provenance.json"))
    build.add_argument("--output", type=Path, default=Path("data/processed"))
    audit = commands.add_parser("audit")
    audit.add_argument("corpus", type=Path)
    split = commands.add_parser("split")
    split.add_argument("corpus", type=Path)
    split.add_argument("--output", type=Path, required=True)
    split.add_argument("--seed", default="nobel-v1")
    export = commands.add_parser("export")
    export.add_argument("corpus", type=Path)
    export.add_argument("--alignments", type=Path, required=True)
    export.add_argument("--output", type=Path, required=True)
    export.add_argument("--format", choices=["prompt-completion", "messages"],
                        default="prompt-completion")
    export.add_argument("--partition", choices=sorted(PARTITIONS), default="unassigned")
    args = parser.parse_args(argv)
    try:
        if args.command == "build":
            result = build_corpus(args.raw, args.reviews, args.metadata, args.output)
        elif args.command == "audit":
            result = audit_corpus(args.corpus)
        elif args.command == "split":
            result = split_corpus(args.corpus, args.output, args.seed)
        else:
            result = export_sft(args.corpus, args.alignments, args.output,
                                args.format, args.partition)
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(2, f"Error: {error}\n")
    print(encode_json(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
