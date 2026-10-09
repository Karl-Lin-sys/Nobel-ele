# Nobel-ele: understanding the translation collection

*A plain-language guide in Canadian English. No background in programming, science, or artificial intelligence is needed.*

This project organises **47 timestamped English translations** from one reported online conversation about Nobel Prizes. It keeps the submitted wording, records small edits, and makes missing information visible.

Its main purpose is to prepare material for careful review. It is not yet a working translation system or a verified guide to Nobel Prize discoveries.

## What is in the collection?

The attachment, `Nobel-Corpus-Package.zip`, contains text, computer programs, and explanatory documents. A collection of text used for study is often called a **corpus**. Here, you can think of it as a small, organised archive.

Each entry contains an English sentence or passage and a time label. For example, `4:21` means four minutes and 21 seconds into the reported conversation. This helps locate a passage if the original recording becomes available; the recording itself was not supplied.

The entries cover these topics:

| Topic label | Entries | What the label means here |
| --- | ---: | --- |
| General conversation | 14 | Greetings, reactions, jokes, and plans for another chat. |
| Chemistry | 13 | Discussion of molecules, mirror-image forms, and making a desired form. |
| Medicine | 2 | Discussion of light and nerve cells. |
| Physics | 18 | Discussion of neutrinos and the IceCube observatory in Antarctica. |

These labels describe what the submitted text discusses. They do not confirm its scientific or prize-related claims.

## What has been changed?

Eight entries received small English edits, such as grammar or spacing corrections. The original and edited versions are both saved, along with notes explaining the changes. Readers can therefore see exactly what was changed.

Canadian spellings already in the material, such as **honour** and **metres**, are retained. The requested editing style is Canadian English; this does not establish that the speaker or translator is Canadian.

The collection has 47 entries but only 46 distinct original texts after minor differences in formatting and capitalisation are ignored. The same passage appears at **46:50** and **50:09**. Both occurrences remain because they have different time labels.

## Why is the Japanese source important?

A checked Japanese-to-English translation needs both the original Japanese and the matching English. This package contains the English side only. The original Japanese transcript, video address, and stream date are missing.

Without the Japanese, a reviewer cannot confirm whether an English passage accurately conveys what was said. Good English grammar alone does not prove that a translation is correct. The program leaves missing source fields empty instead of inventing Japanese sentences.

As a result, there are **zero approved Japanese–English pairs** ready for the package's training export. The recorded submission date, 9 October 2026, is not evidence of when the stream took place or which prize year it discussed.

## What do the programs do?

The main program, `corpus.py`, turns the submitted lines and editing notes into organised records. It checks time labels, reports repeated text, counts topics, and records items that still need review.

The records use a format called **JSONL**: each line holds one complete entry with named fields. For example, the words, time, topic, and review status are stored separately, so another program can find them reliably.

The package also includes tools for later stages:

- **Preparing translation examples:** once real Japanese sources and the required reviews are supplied, an export tool can produce matching source-and-translation pairs. It refuses the current unreviewed template.
- **Separating practice from testing:** with a larger collection, a grouping tool keeps connected conversations and known repeated material together. It refuses to divide this single reported stream into supposedly independent groups.
- **Summarising human reviews:** `evaluate.py` can calculate summaries of reviewers' judgements for future test material. It does not judge translation quality by itself.

No AI model has been trained or evaluated in this collection. These programs organise data and check certain conditions; they do not automatically establish truth.

## Why are these checks useful?

**Keep an editing trail.** Saving both versions makes changes visible and lets reviewers return to the submitted wording.

**Test on unfamiliar material.** A system may seem impressive if its test closely resembles what it practised on. Using genuinely separate conversations helps assess whether it handles new material. Keeping known repetitions together reduces one source of misleading results.

**Look beyond one overall score.** Physics has 18 entries, while medicine has only two. A single combined score could hide poor results in the smaller group. Future review summaries therefore show results by group and how many examples each contains. This does not make the collection representative of all conversations.

## What can you use it for today?

You can read the submitted English, inspect the edits, explore how a text archive is organised, and use it as a starting point for source review.

It is not yet a verified scientific reference, a complete Japanese–English dataset, or evidence that a translation model performs well. The prize attributions and scientific statements in the submitted text still need independent checking. The attachment's research discussions and software-version snapshots are preserved as supplied, rather than newly verified for this publication.

To develop the project further, obtain the original recording and Japanese transcript, match each passage to its English translation, and have people review meaning, factual claims, and reuse permissions. Then collect genuinely different conversations before attempting a meaningful training and testing exercise.

## Find your way around

| File or guide | Why open it? |
| --- | --- |
| [Submitted English](data/raw/translations.txt) | Read all 47 original timestamped entries. |
| [Data card](data/DATA_CARD.md) | See the collection's origins, counts, edits, and limitations. |
| [Editorial notes](data/editorial_review.jsonl) | Inspect the recorded editing and labelling decisions. |
| [Organised records](data/processed/corpus.jsonl) | Explore the computer-readable version. |
| [Original project guide](ORIGINAL_README.md) | Find detailed commands and links to all technical documents. |
| [Checks for this publication](docs/publication_checks.md) | See what was actually checked for this upload. |

All 20 files from the attachment are preserved. Its README is saved as `ORIGINAL_README.md`; this page is the new general-reader introduction.

## Optional: run the checks yourself

Reading the explanation does not require installing anything. To run the programs, use Python 3.10 or later. No extra Python packages or special graphics card are needed.

From this repository's folder, run:

```sh
python corpus.py audit data/processed/corpus.jsonl
python -m unittest discover -s tests -v
```

Use `python3` instead if that is the Python command on your computer. The first command reports the collection's contents. The second checks the program's expected behaviour; passing those tests does not verify the submitted scientific claims.
