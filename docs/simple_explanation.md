# A little box of translation cards

Imagine you have 47 little cards. Each card has some English words and a time, like **4:21**.

We put the cards in a neat box called a **dataset**. We keep the words you gave us. If we fix a small English mistake, we keep both versions. That way, you can see the change.

**JSONL** is the way we pack the box: one card on each line. It makes the cards easy for a computer to pick up.

But a neat box does not make every card correct. We still need to check the words.

## Three helpful rules

**Use real pairs.**

A Japanese-to-English translation needs two things: the real Japanese words and their English meaning. We only have English here. We leave the Japanese space empty. We do not make up the missing words.

**Practise and test with different conversations.**

If you practise a song, then sing the very same song in your test, you might look great. That does not tell us how well you can sing a new song. A translation model needs a test made from new conversations too.

**Check the small piles.**

Our physics pile has 18 cards. Our medicine pile has only two. If we count everything together, the big pile can hide trouble in the little pile. We check each pile and show its size.

## What the program does

It saves the cards, checks the times, notices repeated text, and shows which cards still need review. It uses a little bit of ordinary Python. You do not need a big graphics card.

## What you have today

You have a clear, reproducible **corpus preparation project**. You can show how you organise text and prevent a few common data mistakes.

There are no checked Japanese–English pairs yet. There is no trained model yet. The Nobel Prize and science statements have not been fact-checked. A company’s interest in this small collection is still unknown.

The next useful step is to add the real Japanese source and have a person review each pair. Then collect more genuinely different streams. Bigger claims should wait for proper tests.
