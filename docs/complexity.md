# Function-by-function Big-O

**Big-O means how the amount of work grows when the input grows.** Reading twice as much text usually means roughly twice as much reading. A program that compares every line with every other line can grow much faster. This pipeline does not perform that all-pairs comparison.

These costs are derived from the actual original code. They are mathematical implementation analysis, not performance claims borrowed from papers. A 47-row sample cannot demonstrate training speed, memory-leak freedom, or a general ML accuracy improvement.

## Symbols and assumptions

- **B:** total bytes/characters of the text files being processed, including emitted record text where relevant.
- **N:** number of canonical rows; **A:** number of annotation/alignment rows; **R:** bytes retained in their index.
- **L:** largest single record/line size. The input reader rejects lines over 1,048,576 bytes; actual submitted lines are much smaller.
- **G:** number of streams/components or unique input digests, as appropriate.
- **P:** number of eligible source/target pairs exported.
- **K:** number of object fields; **S(V):** total `k log k` over dictionaries inside value V when JSON keys are sorted.
- **J:** bytes retained in the judgement index; **T:** bytes retained in the test-alignment index.
- **α(G):** the very slowly growing inverse Ackermann factor for union-find.

Dictionary/set lookup costs below are **expected amortised** costs with ordinary Python hashing. They are not unconditional worst-case constant-time guarantees. Path names and fixed schema keys have bounded size; if identifiers or seeds are made arbitrarily long, include their character lengths in B. Unicode normalisation can expand text by a bounded factor for the fixed Unicode database in a Python build.

Memory is **additional working memory**, excluding caller-owned inputs where explicitly stated. Disk output size is separate. A generator's streaming memory does not make an annotation or duplicate index constant-size.

## `corpus.py`

| Function | Time | Additional memory | Reason |
| --- | --- | --- | --- |
| `bounded_lines` | O(B) per full iteration | O(L), with a hard line bound | Reads and decodes one limited-size line at a time. |
| `unique_object` | Expected O(K) | O(K) | Checks each JSON object key once. Called for nested objects too. |
| `reject_constant` | O(1) | O(1) | Raises immediately for NaN/Infinity tokens. |
| `read_jsonl` | Expected O(B) for fixed-depth/fixed-schema rows | O(L) | Parses one object at a time and releases it on iterator advance. |
| `encode_json` | O(size(V) + S(V)) | O(size(V)) | Serialises V with sorted dictionary keys. Fixed-schema rows have constant K, so the cost is linear in their text size. |
| `atomic_text` | O(1) bookkeeping, plus O(W) output I/O | O(1) buffers; O(W) temporary disk space | Closes, flushes, syncs, and atomically replaces one W-byte file. OS flush/rename wall time is environment-dependent. |
| `write_json` | O(size(V) + S(V)) plus output I/O | O(size(V)) | Encodes one report, then writes it through `atomic_text`. |
| `file_sha256` | O(B) | O(C), C = 65,536 bytes | Hashes fixed-size chunks; its inline reader lambda costs O(C) per call. |
| `normalise_text` | O(L) | O(L) | Normalises Unicode/apostrophes, case-folds, and collapses whitespace. It does not alter the stored original. |
| `text_sha256` | O(L) | O(L) | Normalises, encodes, and hashes one text. |
| `timestamp_seconds` | O(1) under the bounded timestamp grammar | O(1) | Parses at most three bounded integer fields and checks their ranges. |
| `parse_line` | O(L) | O(L) | Finds the fixed separator and extracts the text. |
| `load_index` | Expected O(B + A) | O(R) | Reads once and retains every annotation/alignment, keyed by ID or timestamp. |
| `make_records` | Expected O(B + A + N) for a full iteration | O(N + L) beyond the supplied review index | One checksum pass, one transcript pass, fixed-field construction, and seen-timestamp checks. |
| `validate_record` | O(L) for this fixed schema | O(L) | Validates fields and recalculates two text hashes. |
| `audit_corpus` | Expected O(B + N + G log G) | O(N + G + L) | Keeps ID/hash/group indexes and row IDs, not all utterance strings; sorts unique input digests. |
| `build_corpus` | Expected O(B + A + N + G log G + S(report)) | O(R + N + L) | Reads annotation index, writes corpus, audits it, then streams the alignment template. B includes all input/output passes. |
| `find_root` | Amortised O(α(G)) within the union sequence | O(1) | Iterative path compression; one individual call can traverse the current tree height. |
| `union_streams` | Amortised O(α(G)) | O(1) | Two root lookups and union by component size. |
| `split_corpus` | Expected O(B + N α(G) + G log G + S(report)) | O(N + G + L) | Audits, stores text/group-to-stream ownership, unions streams, sorts components, then streams output. It stores indexes, not a full text matrix. |
| `alignment_blockers` | O(L + E) | O(1) for a fixed number of flags | Checks fixed review fields, URL strings, target equality, and E total evidence-URL characters. Checks do not fetch or validate evidence content. |
| `export_sft` | Expected O(B + N + A + S(report)) | O(R + N + P + L) | Loads alignments, audits, streams candidates, and retains only ID/pair-hash sets plus the alignment index. Repeated eligible pairs are skipped. |
| `main` | Selected command cost plus report serialisation | Selected command memory plus report text | CLI dispatch has fixed option structure; work is in the selected function. |

The sorting lambda in `split_corpus` hashes each component's sorted stream-member list once; across components its key construction is linear in total member text. Sorting the resulting fixed-size digest keys costs O(G log G). The union-find arrays/dictionaries store G streams, while the duplicate ownership map can have O(N) keys.

`build_corpus` regenerates three output files. Atomic replacement is **per file**, not a transaction over the whole directory. A process interruption between replacements can leave mixed generations; rebuild and compare checksums before consuming them. Filesystem-level atomic rename is not a promise about every storage device or crash recovery scenario.

## `evaluate.py`

| Function | Time | Additional memory | Reason |
| --- | --- | --- | --- |
| `check_disjoint` | Expected O(B_train + B_test + N_train + N_test + G log G) | O(N_train + N_test + L) | Audits both manifests and compares stream/hash/group sets. Exact/curated overlap is checked; model pretraining is unknown. |
| `summarise` | O(n) for n reviews in the group | O(1) | Uses counters for adequacy and terminology; no copied terminology list. |
| `score_human_reviews` | Expected O(B + N + A + G log G) plus output key sorting | O(J + T + N + L) | Retains alignment/judgement indexes and references to judgements grouped three ways. It does not load model weights or predictions as tensors. |
| `main` | Scoring cost plus report serialisation | Scoring memory plus report text | CLI dispatch and one output write. |

For an output report with many streams, sorted JSON dictionary keys add O(G log G); fixed topic and genre dictionaries add only constant overhead. Review mean calculations traverse each row a fixed number of times. They are linear, not quadratic.

## Test-only functions

The test suite uses fixed, explicitly synthetic fixtures. Their exact sizes do not grow with a production corpus, except for the real-input rebuild test.

| Test helper or method | Time and memory |
| --- | --- |
| `fixture` | O(L) time/memory to copy and adjust one fixed-schema record and hash its texts. |
| `alignment` | O(1) construction, sharing existing ID/text strings. |
| `judgement` | O(1) construction. |
| `PipelineTests.setUp` | O(1) bookkeeping plus filesystem operations. |
| `PipelineTests.rows` | O(B + S(values)) time and O(B) memory because the small test writer joins its fixture lines. This helper is intentionally not the production streaming writer. |
| `test_real_input_roundtrip_and_counts` | Build cost above, plus O(B) time/memory for byte comparison and raw/record lists. |
| All other `test_*` methods | O(1) relative to production N: each runs a fixed set of small fixtures. The oversize-line test allocates one fixed bound-sized buffer. Operations inside each fixture retain the corresponding production-function costs. |

## Practical limits

Preparation needs no GPU, tensor allocations, gradient tape, worker process, or model server. No inference-memory workaround is relevant here. Annotation, hash, and judgement indexes grow linearly; use a disk-backed design if those indexes no longer fit available memory. That would be a new implementation decision requiring its own validation, not a reason to claim the current prototype scales without limit.
