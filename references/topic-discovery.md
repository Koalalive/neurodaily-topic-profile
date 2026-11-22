# Topic discovery and interview guide

## Start broad, then narrow

1. Name the topic.
2. Name the **outcome** the user cares about (mechanism, therapy, delivery,
   diagnostics, regulation, manufacturing).
3. Name the material/platform/method (lipid nanoparticle, AAV, hydrogel, TMS,
   biomarker, etc.).
4. Name the context (disease, population, model system, geography).
5. Name exclusions.

## Vocabulary sources

- PubMed MeSH and entry terms
- Emtree / Embase when available
- OpenAlex concepts and topic names
- Crossref titles and keywords
- Recent review titles and author keywords
- ClinicalTrials.gov conditions/interventions
- Patent CPC classifications for translational topics
- Society conference programs

Use exact phrases where possible. Add acronym + expansion.

## Boolean example

```text
("drug delivery" OR "controlled release" OR "nanoparticle delivery")
AND ("mRNA" OR "siRNA" OR "protein")
AND NOT (veterinary OR "animal feed")
```

## Source checklist

- [ ] biomedical papers: PubMed / Europe PMC
- [ ] preprints: bioRxiv / medRxiv / arXiv / SSRN
- [ ] trials: ClinicalTrials.gov
- [ ] regulatory / policy feeds
- [ ] field journals and RSS
- [ ] patents / funding / datasets only if relevant

## Review with the user

Show the final query, source toggles, journal shortlist, and exclusions. Ask whether
any subfield is missing before building.
