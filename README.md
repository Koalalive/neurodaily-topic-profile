# NeuroDaily Topic Profile v1.0.0

An Agent Skill for building a validated [NeuroDaily](https://github.com/Koalalive/neurodaily)
search profile for a **research topic/field**, not for one named scholar.

Examples: drug delivery, mRNA vaccines, CAR-T, neuroimmunology.

For one PI, lab or research team use
[`neurodaily-scholar-profile`](https://github.com/Koalalive/neurodaily-scholar-profile).

## What it does

- asks a short, guided sequence of questions
- turns synonyms, subtopics, exclusions and sources into a boolean query
- builds the NeuroDaily profile wrapper
- validates JSON syntax, schema, enums, URLs, sources and journals

## Use

```bash
python scripts/build_topic_profile.py topic.json --out neurodaily-topic.json
python scripts/validate.py neurodaily-topic.json
```

See [`SKILL.md`](SKILL.md), [`references/topic-discovery.md`](references/topic-discovery.md)
and [`examples/drug-delivery/`](examples/drug-delivery/).

## Install as a skill

```bash
git clone https://github.com/Koalalive/neurodaily-topic-profile.git \
  ~/.claude/skills/neurodaily-topic-profile
```

## License

Apache-2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
