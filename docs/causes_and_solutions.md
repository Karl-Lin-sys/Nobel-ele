# Three workflow causes and implemented solutions

The proposed workflow promises a multilingual fine-tuning dataset immediately after saving English chat translations. The observed input supports a smaller claim: a traceable English corpus preparation prototype. The following are diagnosed **data-workflow defects**. No model failure, overfitting measurement, or software memory leak was supplied.

## 1. Missing source and task mismatch

**Observed cause:** every supplied utterance is English. There is no Japanese transcript, video URL, or verified stream date. A made-up question about a scientific term would turn a translation into invented question answering. Several award and scientific claims are unverified, and the Ig Nobel examples are absent.

**Implemented solution:** `make_records` preserves original/edited English and stores missing sources as null. `alignment_blockers` and `export_sft` require a real source, source location and times, explicit alignment/target review, and reviewer attestations. Rows with substantive fact flags also require a documented evidence review. Training export emits no rows from the untouched template.

**Why this helps:** a supervised example has to represent the task it is intended to teach. DataComp-LM supports deliberate dataset design; it does not validate fabricated source/target pairs. The no-invented-source rule is an original engineering safeguard, not an experimental result from that paper.

**Remaining limit:** a program can validate fields and attestations, but cannot prove that a reviewer transcribed the right audio, translated correctly, or supplied sound scientific evidence. Genuine Japanese alignment and human review remain external inputs.

## 2. Repetition and correlated examples

**Observed cause:** 46:50 and 50:09 repeat the same English utterance. Several other lines paraphrase shared content or require the same conversation context. All 47 rows are reported to come from one stream. Random row splitting would test familiar context and style.

**Implemented solution:** the archive keeps all timestamped occurrences. Normalised hashes flag exact repetition; curated content groups record known shared material. `split_corpus` joins streams linked by raw/edited duplicate text or curated groups, then assigns whole connected components. It refuses fewer than three independent components. `check_disjoint` checks train/test overlap again. `export_sft` removes repeated source/target pairs within an export.

**Why this helps:** a train/test overlap violates the intended separation between learning and evaluation. ConStat shows why benchmark inflation matters and why performance generalisation is a stronger concern than simple membership alone. Our grouping is a structural prevention step; it is not the paper's statistical detector.

**Remaining limit:** unseen paraphrases, shared speakers across streams, common facts, and earlier base-model training can still overlap. Three components is only a minimum to form three non-empty partitions. Meaningful evaluation needs substantially more representative independent data.

## 3. Selective sampling and an average dominated by frequent content

**Observed cause:** this is one selected stream and one reported translator. Topic counts are general 14, chemistry 13, medicine 2, and physics 18. There are no model predictions or human gold references. A pooled result could conceal errors on medicine or mixed speaker dialogue.

**Implemented solution:** `audit_corpus` reports counts without manufacturing scores. For future reviewed held-out data, `score_human_reviews` requires a judgement for every test row and disjoint training/test manifests. It reports micro summaries and separate topic, genre, and stream summaries, plus equal-weight topic/stream summaries. Missing groups and terminology denominators remain visible.

**Why this helps:** Paloma motivates inspection across distributions. An equal-weight group mean prevents the largest observed topic from setting all the weight in that particular summary. It does not correct who was sampled. Our thresholds and human rubric are original project choices, not validated Paloma translation scores.

**Remaining limit:** collect genuine source/target pairs across streams, speakers, translators, topics, and dates using a recorded sampling plan. Independent reviewers should assess adequacy, terminology, and regional phrasing without seeing which model produced the translation. Keep a final test set separate from tuning. Report uncertainty at the stream level when there are enough independent streams; no confidence interval is invented for this collection.

## Performance and memory decisions

The converter reads one bounded line at a time and closes files deterministically. Outputs are written to a temporary file and replaced only on successful completion. It makes no model API calls, retains no tensors or computation graphs, creates no loader workers, and performs no quadratic all-pairs text similarity search. Annotation and duplicate indexes still grow with the number of records; memory is not constant for the full pipeline. See [complexity.md](complexity.md).

The tests check failed-write rollback, oversized lines, Unicode, invalid JSON, transitive duplicate grouping, missing-source export refusal, and biased denominator handling. Passing those checks supports the implemented behaviours. It does not prove that every future data error or memory issue is impossible.
