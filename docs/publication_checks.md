# Checks for the Nobel-ele publication

Checked on 9 October 2026.

## What was checked in this upload

- All 20 files from the supplied `Nobel-Corpus-Package.zip` match the extracted files byte for byte. The supplied README is preserved as `ORIGINAL_README.md` at the root, so its relative links still work.
- The new README explains the attachment in Canadian English for general readers without specialist knowledge.
- Python 3.12.4 on Windows: `python -m unittest discover -s tests -v` passed all 18 existing tests, with zero failures or errors. These include a byte-for-byte corpus rebuild, missing-source export refusal, duplicate handling, and review-summary checks.
- `python corpus.py audit data/processed/corpus.jsonl` completed successfully: 47 entries, 46 distinct normalised original texts, eight editorial changes, one reported stream, and zero approved translation pairs.
- All current Japanese-source fields remain empty and all records remain ineligible for training.
- All local file links in the new README resolve to files in this repository.

## What these results mean

These checks confirm preservation of the supplied files and the behaviours covered by the existing tests. They do not verify the scientific or Nobel Prize statements, translation accuracy against Japanese audio, or the attachment's research and software-version claims. No AI model was trained or evaluated.

The attachment's `docs/verification.json` is preserved as received. It describes an earlier reported run and is separate from the results above.

Source ZIP SHA-256: `359638178a2bff54a4c434e8ca5eec4330161c9019d0702b0bc05bdd8cbb811b`
