# Nobel stream translation corpus

A small, traceable collection of **47 timestamped English translations** supplied by Karl-Lin-sys. The requested editorial language is **Canadian English**. Eight lines received light grammar or spacing edits. Every original line is kept alongside its edited version.

Think of each JSONL line as a little index card. Its labels say **when the words appeared**, **what the words were**, and **what still needs checking**. JSONL puts one complete card on each line, so another program can read it easily.

**Current status:** a corpus preparation prototype. There are **46 distinct normalised original texts**, **one reported stream**, and **zero approved Japanese–English training pairs**. The Japanese source, video URL, and stream date were not supplied. Those fields stay empty. Submission on 9 October 2026 does not establish the date or year of the stream.

The supplied lines discuss **Nobel Prizes**. They do not contain the proposed Ig Nobel examples, 3D necroprinting, or cockroach milk crystals. Those examples were not invented or added. Award and scientific claims remain unverified quotations from the submitted translations.

## Start here

Python **3.10 or later** is enough. There are no third-party packages to install and no GPU is needed. Open a terminal in this repository and run:

```sh
python3 corpus.py build
python3 corpus.py audit data/processed/corpus.jsonl
python3 -m unittest discover -s tests -v
```

On a computer where the command is named `python`, use `python` in place of `python3`.

| File | What it does |
| --- | --- |
| [Original lines](data/raw/translations.txt) | Keeps all 47 timestamped submissions. |
| [Corpus](data/processed/corpus.jsonl) | Stores original and edited English, timestamps, topic labels, and review flags. |
| [Audit](data/processed/audit.json) | Counts rows, repeated text, topics, genres, and unresolved claims. |
| [Editorial decisions](data/editorial_review.jsonl) | Makes all eight text changes and manual grouping decisions reproducible. |
| [Provenance](data/provenance.json) | Records what was supplied and what is unknown. |
| [Alignment template](data/processed/alignment_template.jsonl) | Provides empty Japanese-source fields for a future human review. |
| [Python pipeline](corpus.py) | Builds, audits, groups streams, and exports reviewed translation pairs. |
| [Human-review scorer](evaluate.py) | Reports future held-out reviews by topic, genre, and stream. |

## Why the checks matter

1. **Keep real pairs.** A translation example needs the real Japanese words and their English translation. An English line and a made-up Japanese question would teach a different task. The exporter requires reviewed source alignment and target text.
2. **Keep the test separate.** Testing on another line from the same conversation can make a model look better than it is. Whole streams and connected duplicate groups stay together. This one-stream collection cannot make three independent partitions.
3. **Look at small groups too.** Physics has 18 lines, while medicine has two. A single average can hide a weak topic. The scorer reports every topic and its count, as well as equal-weight averages over the groups actually present.

These checks reduce specific errors. They cannot promise that all leakage, overfitting, reviewer error, or selection bias has been removed. No model has been trained or scored here. The reviewed papers do not establish that companies want or will pay for this particular corpus.

## Build future translation examples

Copy `data/processed/alignment_template.jsonl` to a separate working file, such as `private/alignments.jsonl`. Keep that working copy separate: `build` regenerates the template.

For each approved row, a reviewer supplies the **actual Japanese transcript**, the **actual video URL**, the **start and end times**, and their reviewer identifier. The reviewer checks alignment, English translation, and applicable reuse permissions. Award/scientific claims also need an explicit evidence review before this conservative exporter admits them. A checked box or URL is a human attestation; the program cannot prove the content is true.

```sh
python3 corpus.py export data/processed/corpus.jsonl \
  --alignments private/alignments.jsonl \
  --output build/reviewed_pairs.jsonl \
  --format prompt-completion --partition unassigned
```

The output contains exactly `prompt` and `completion` fields. `--format messages` produces a system/user/assistant message format instead. A trainer may impose additional schema requirements. An unassigned export is a development example collection, with **no generalisation claim**.

Running this command with the untouched template deliberately fails: there are no reviewed source pairs. It leaves no empty or partial training file.

For a larger collection, build each genuinely different stream with its own provenance and `stream_id`, then concatenate those **canonical** JSONL files. Run:

```sh
python3 corpus.py split build/multiple_streams.jsonl --output build/splits
```

This requires at least three independent stream/duplicate components. That is a structural minimum, not a statistically sufficient sample. The split report shows assignments and topic counts; topic balance is not guaranteed. Use `--partition train` when exporting the generated training manifest. Keep future evaluation references, predictions, and reviews private until scoring is complete.

## Read more

- [Simple Canadian English explanation](docs/simple_explanation.md)
- [Technology comparison and primary sources](docs/technology_and_evidence.md)
- [Three workflow causes and implemented solutions](docs/causes_and_solutions.md)
- [Function-by-function Big-O explanation](docs/complexity.md)
- [Data card](data/DATA_CARD.md)
- [Evaluation procedure and human-review rubric](docs/evaluation.md)
- [Verification record](docs/verification.json)

The implementation is original project code. Research claims use three peer-reviewed **NeurIPS 2024** papers; framework comparisons use official documentation, release metadata, and reference source. No personal blog or unofficial forum is used as evidence.
