# Drug delivery topic profile

```bash
python scripts/build_topic_profile.py examples/drug-delivery/topic.json \
  --out examples/drug-delivery/profile.json
python scripts/validate.py examples/drug-delivery/profile.json
```

Result:

```text
drug-delivery: 8 terms, 7 journals
OK: profile is valid
```

The generated query includes aliases/subtopics and excludes veterinary/animal-feed
results. Journals and sources are user-reviewable; no metrics are invented.
