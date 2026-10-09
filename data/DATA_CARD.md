# Data card

| Field | Value |
| --- | --- |
| Name | Nobel stream translation corpus |
| Submission date | 9 October 2026, Asia/Taipei |
| Stream date and video URL | Unknown; stored as null |
| Reported translator | Karl-Lin-sys |
| Reported speaker | Sopia and/or chat; identity and attribution not independently verified |
| Collection | Submitter-selected timestamped English chat translations |
| Original audio/Japanese | Not provided |
| Rows | 47 |
| Distinct normalised original texts | 46 |
| Exact repeated utterance | 46:50 and 50:09 |
| Editorial changes | 8; original and edited text both retained |
| Editorial target | Canadian English (`en-CA`); not a verified regional-dialect annotation |
| Reported streams | 1 |
| Approved translation pairs | 0 |
| Model training/evaluation | None |
| Split | Every row is `unassigned` |
| Data licence | Not specified; no new third-party reuse grant is asserted |

## Composition

| Assistant triage topic | Rows |
| --- | ---: |
| General conversation | 14 |
| Chemistry | 13 |
| Medicine | 2 |
| Physics | 18 |

| Assistant triage genre | Rows |
| --- | ---: |
| Stream chat | 21 |
| Science explanation | 19 |
| Award claim | 6 |
| Mixed speaker dialogue | 1 |

Labels are manual assistant triage, not human gold labels or model predictions. Topic labels describe the text in the submitted line. They do not certify scientific truth. Claim flags overlap; their counts must not be added together to count unique rows.

## Provenance and editing

The same translation block appeared repeatedly in the request. It was ingested once. Inside that block, all 47 timestamped rows remain, including the repeated physics award line. Outer trailing spaces were omitted during serialisation; original words and punctuation remain in `text_en_original` and `source_line`.

The eight edited timestamps are **4:45, 11:43, 31:51, 35:57, 50:47, 55:32, 1:04:24, and 1:05:33**. Edits address English grammar, an abbreviation, or spacing. Canadian spellings such as **honour** and **metres** are retained. The actual Japanese meaning cannot be checked from the English alone.

Each row has a stable stream/time identifier, source line number, raw input checksum, and normalised original/edited text checksums. These hashes detect particular byte/content changes; they do not prove authorship, factual accuracy, or freedom from semantic overlap.

`near_duplicate_group` records conservative manual content/context groups. Some are paraphrases and some merely share a topic or antecedent. They deliberately over-group for future splitting. This is not a general semantic duplicate detector. Previously unseen paraphrases can escape it.

## Intended uses and limits

Useful now: inspecting timestamped translations, demonstrating JSONL preparation, reviewing terminology, reproducing editorial changes, and adding genuine source alignments later.

The current English-only archive is not a parallel multilingual corpus, a verified scientific knowledge dataset, a representative sample of Canadian English, or an independent translation benchmark. One selected stream and one reported translator create selection and style bias. Visual references, surrounding Japanese context, and separate speaker turns are missing.

The text identifies Nobel Prizes. No source establishes an Ig Nobel stream or the proposed Ig Nobel examples. Scientific claims, prize descriptions, relative dates, quantities, depth, cost, and causal explanations remain triaged but unverified. ML papers cannot settle those scientific or prize-specific facts.

Permissions and scientific verification are separate from the user's instruction to publish the submitted materials. This repository records missing reuse documentation and requires reviewer attestations before training export. No automatic legal or factual verification is claimed.

All reported statistics are descriptive counts of this submission. None is a model performance score. Overfitting cannot be diagnosed without a trained model and a genuinely held-out evaluation.
