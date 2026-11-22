---
version: 1.1.0
name: neurodaily-topic-profile
description: Guide a user step by step to build a validated NeuroDaily search profile for a research TOPIC or field (for example drug delivery), using synonyms, subtopics, exclusions, sources and journals, then export and validate one portable neurodaily.profile JSON. Use when the user wants a field/topic monitor rather than a profile of one named scholar or lab.
---

# NeuroDaily Topic Profile

Build a **topic/field-driven** NeuroDaily profile. This is different from
`neurodaily-scholar-profile`:

| Skill | Subject |
|---|---|
| `neurodaily-scholar-profile` | one researcher, lab or team |
| `neurodaily-topic-profile` | a topic/field, e.g. drug delivery |

## When to use

Use when the user says things like:

- "I want to monitor drug delivery"
- "build me a NeuroDaily config for mRNA vaccines"
- "I care about CAR-T, not one particular PI"
- "make a field profile with journals and preprints"

Do **not** use it to infer an individual's interests from their publication list;
use the scholar-profile skill for that.

## Guided interview

Ask one short question at a time. Do not dump the whole questionnaire at once.
Keep a draft `topic.json` after each answer.

### 1. Scope

1. What is the topic in one sentence?
2. Which subtopics or methods are in scope?
3. Which nearby areas are explicitly out of scope?
4. Is the focus basic science, clinical/translational, industry/regulatory, or all?

### 2. Vocabulary

Ask for:

- synonyms and spelling variants
- acronyms and expansions
- MeSH/Emtree terms if known
- materials, mechanisms, delivery routes, disease contexts
- model systems or technologies that should count

Build a boolean query from quoted phrases. Prefer specific terms over generic words
such as "delivery" alone.

### 3. Sources

Ask which sources matter:

- PubMed / Europe PMC
- journal RSS
- bioRxiv / medRxiv / arXiv / SSRN
- ClinicalTrials.gov / WHO ICTRP
- FDA / EMA / policy feeds
- patents, funding, datasets, software

If the user is unsure, propose a conservative default and explain the tradeoff.

### 4. Journals

Ask for 5–15 field journals or accept a shortlist. Do not invent impact factors or
JCR/CAS values.

### 5. Optional scholar tracking

Ask whether the user wants to track named scholars alongside the topic. Use the
scholar's ORCID/affiliation to disambiguate common names.

```json
"scholars": ["Nolan Williams"],
"author_mode": "intersect"
```

- `intersect`: only works matching both topic and scholar
- `track`: all new works by the scholar, plus topic results

### 6. Windows

Confirm daily and manual lookback windows. Default: daily 36h, manual 240h,
trials 36h, funding 168h, news 36h.

## Build

Write the interview result as `topic.json`:

```json
{
  "topic": "drug delivery",
  "aliases": ["drug delivery systems", "controlled release"],
  "subtopics": ["nanoparticles", "liposomes", "mRNA delivery"],
  "scholars": [],
  "author_mode": "intersect",
  "mesh_terms": ["Drug Delivery Systems"],
  "exclude": ["veterinary"],
  "sources": {
    "journal": {"enabled": true, "max_results": 200, "lookback_days": 2},
    "pubmed": {"enabled": true, "max_results": 500, "lookback_days": 2},
    "biorxiv": {"enabled": true, "max_results": 200, "lookback_days": 2},
    "arxiv": {"enabled": false},
    "trials": {"enabled": true, "max_results": 100, "lookback_days": 2},
    "conferences": {"enabled": true, "max_results": 50, "lookback_days": 365},
    "google_news_zh": {"enabled": true, "max_results": 100, "lookback_days": 2},
    "policy": {"enabled": true, "max_results": 100, "lookback_days": 2}
  },
  "journals": [
    {"name": "Journal of Controlled Release"},
    {"name": "Advanced Drug Delivery Reviews"},
    {"name": "Biomaterials"}
  ],
  "policy_feeds": []
}
```

Then:

```bash
python scripts/build_topic_profile.py topic.json --out neurodaily-topic.json
python scripts/validate.py neurodaily-topic.json
```

If NeuroDaily is installed:

```bash
neurodaily profile validate neurodaily-topic.json
neurodaily profile doctor neurodaily-topic.json
```

## Quality rules

- Never fabricate publications, journal names, metrics or MeSH terms.
- Do not use generic "drug delivery" as the only query term; add specific subtopics.
- Keep excluded terms explicit and review them with the user.
- A topic profile is a **draft**: ask the user to inspect the journals and query.
- Report which sources are enabled/disabled and why.
- If the topic is ambiguous, ask a clarifying question rather than guessing.

## Files

- `scripts/build_topic_profile.py` — topic.json → portable profile
- `scripts/validate.py` — strict JSON/schema/type/URL validation with field paths
- `references/topic-discovery.md` — interview and vocabulary discovery guide
- `references/profile-contract.md` — generated NeuroDaily profile shape
- `examples/drug-delivery/` — worked example
