# Phase 10 — Pilot validation

## Purpose

Decide whether Document Copilot is good enough for Driftwood to keep using. The client brief defines done as: **five senior analysts use it for a week and each reports at least three hours saved.**

That is not a code task. Nobody can check this box by reading the repository. It needs the deployed app from Phase 9 and five people who actually cover these companies.

## What "good" means on a single answer

For every question below, the answer fails if any of these are false:

- Each factual claim has a citation the UI can open (filing and page or section).
- Clicking the citation shows the passage, and that passage is actually in the filing.
- The bot does not invent a number, a trend, or a cause that the passage does not support.
- When the filings are silent, it says the corpus does not support the claim.
- It does not recommend buying or selling.
- After a reload, the thread is still in that user's list.

A fluent answer with a missing or mismatched citation is a failure.

## The ten questions

Ask these in the deployed app, signed in as a real user. One thread per question keeps the notes easier to compare.

1. Across Apple's 2021–2025 10-Ks, how did the revenue mix between iPhone, Services, Mac, iPad, and Wearables change, and which category appears to have contributed most to any mix shift?
2. For Amazon, compare AWS operating income and margin against North America and International from 2021–2025. In which years did AWS appear to fund losses or weaker profitability elsewhere?
3. How did NVIDIA describe demand drivers, customer concentration, and supply constraints for its Data Center business from fiscal 2021 through fiscal 2025?
4. Across Microsoft's 2021–2025 filings, what changed in the way the company describes Azure, AI infrastructure, and cloud capacity constraints?
5. For Alphabet, how did Google Search, YouTube ads, Google Network, subscriptions/platforms/devices, and Google Cloud revenue trends differ across the available 10-Ks?
6. Which of the five companies added, removed, or materially changed risk-factor language related to AI, cloud infrastructure, export controls, supply chain concentration, or regulation between 2021 and 2025?
7. For Apple and NVIDIA, what do the filings say about supplier concentration or dependence on third-party manufacturing, and did the wording become more or less urgent over time?
8. Compare capital expenditures and purchase commitments for Microsoft, Alphabet, Amazon, and NVIDIA. What do the filings imply about the scale and timing of AI/cloud infrastructure investment?
9. For each company, summarize the most important geographic revenue exposures disclosed in the latest 10-K, then identify any year-over-year changes that could matter to an analyst.
10. If an analyst asks whether the filings prove that generative AI improved margins for any of these companies, what evidence exists in the corpus, and where should the bot refuse to infer beyond the filings?

Question 10 is the refusal test. A pass is an answer that separates what the filings state from what they do not prove.

## Score sheet

Copy this and fill it while you read. `Pass` only if the acceptance rules above all hold.

| Q | Cited | Passage matches | No invented facts | Refuses when thin | Persists on reload | Pass |
| - | ----- | --------------- | ----------------- | ----------------- | ------------------ | ---- |
| 1 | | | | | | |
| 2 | | | | | | |
| 3 | | | | | | |
| 4 | | | | | | |
| 5 | | | | | | |
| 6 | | | | | | |
| 7 | | | | | | |
| 8 | | | | | | |
| 9 | | | | | | |
| 10 | | | | | | |

## The week with analysts

After the ten questions look acceptable to you:

1. Create five accounts with the emails those analysts will use (or let them sign up).
2. Give them the frontend Railway URL and the ten questions as examples, not as a script they must stick to.
3. Ask each person, at the end of the week, how many hours of filing intake the tool actually replaced.
4. Roll out further only if all five report at least three hours saved. That bar is the client's, from [client-brief.md](../../client-brief.md).

## Out of scope while you do this

Do not add trading recommendations, news, extra companies, billing, or a mobile app to "make the pilot more impressive." The brief forbids those.

## Status

The questionnaire and the bar are defined. The pilot has not been run. It cannot be run until Phase 9's public URL works.
