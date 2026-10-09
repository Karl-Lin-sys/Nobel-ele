# Future evaluation procedure

The present corpus has no model scores. `evaluate.py` is a tool for a later, genuinely reviewed held-out collection. It uses an original human rubric and reports its limits explicitly.

## Prepare the inputs

1. Collect independent streams with real Japanese transcripts, aligned English references, source URLs/times, and reviewer attestations. Keep stream identifiers unique across the collection.
2. Use `corpus.py split` on the combined canonical corpus. Review the group assignments and topic counts. Preserve the final test manifest before changing training or model settings.
3. Train on approved training pairs only. Use validation data to choose model settings. Generate predictions on the frozen test set once the model choice is settled.
4. Have reviewers read the Japanese source/context and the prediction without a model label. Provide exactly one consolidated judgement per test ID. For multiple raters, retain their separate records and document how disagreements were resolved before this summary.

The alignment file passed to the scorer must contain **exactly the test IDs**, with the same source/translation checks used by the exporter. URLs and review checkboxes are attestations, not automatic fact verification.

## Original human-review rubric

| Adequacy grade | Meaning |
| --- | --- |
| 0 | The intended meaning is absent or seriously wrong. |
| 1 | Most important meaning is missing or wrong. |
| 2 | Some meaning is correct, but important errors remain. |
| 3 | Main meaning is correct, with minor errors. |
| 4 | Meaning is faithful and wording is clear in the supplied context. |

This ordinal scale is a project convention. Its arithmetic mean is a descriptive summary, not a calibrated interval-scale measurement. The displayed “adequate rate” uses the declared threshold **grade ≥ 3**.

`terminology_correct` is `true` or `false` if the reviewer assessed applicable terminology. It is `null` when there is no applicable terminology assessment. The report always shows the number assessed; null does not count as success. A topic can have high adequacy and still have a low terminology rate. Regional Canadian English quality needs its own documented review; the language tag alone is not a score.

A judgement line has these fields:

```json
{"id":"ACTUAL_TEST_ID","prediction_en_ca":"ACTUAL_MODEL_PREDICTION","adequacy":3,"terminology_correct":true,"reviewer":"ACTUAL_REVIEWER_ID","reviewed_against_source":true}
```

This is a schema illustration, not a judgement about the submitted stream. Do not copy the placeholder values into real results.

```sh
python3 evaluate.py \
  --train build/splits/train.jsonl \
  --test build/splits/test.jsonl \
  --alignments private/test_alignments.jsonl \
  --judgements private/test_judgements.jsonl \
  --output build/evaluation.json
```

## Read the report

- **Micro:** every reviewed test row has equal weight. Frequent topics therefore receive more total weight.
- **By topic, genre, and stream:** inspect each score together with its row count and terminology denominator.
- **Macro topic:** each observed topic receives equal weight. Topics absent from the test set are listed, not silently counted as correct.
- **Macro stream:** each observed test stream receives equal weight. This reduces domination of that summary by a long stream.

These are group summaries, not classifier accuracy, F1, BLEU, COMET, or Paloma perplexity. This task is translation, and the triage topics are not class predictions. Their frequency imbalance is shown instead of manufacturing a classification benchmark.

The scorer rejects missing judgements, extra IDs, unreviewed references, non-test rows, and known train/test stream or duplicate overlap. A selective subset cannot silently shrink the test denominator.

For example, the regression test uses **synthetic fixtures** with nine physics reviews graded 4 and one medicine review graded 0. The micro mean is 3.6; the equal-weight topic mean is 2.0. Those numbers demonstrate the weighting difference only. They are not corpus or model results.

## Limits to state with any future result

Known overlap checks cannot prove that a model's pretraining data were uncontaminated. Stream selection, shared speakers, reviewer judgement, weak topic labels, missing topics, and rare terminology can still bias results. Compare models on the same frozen test rows and disclose training/validation history. Use multiple independent streams before estimating uncertainty; a row-level confidence interval would misrepresent correlated conversation data. This implementation reports `confidence_interval: null` and never claims that all bias is eliminated.
