# Evidence-ledger process for one condition (give this whole file to your AI)

You are helping one person rebuild the evidence behind ONE row of a feature table (one condition x 22 features) for an acute undifferentiated febrile illness (AUFI) diagnosis project. Every number must be traceable to a paper. Follow this document exactly. If a rule is unclear or two rules conflict, STOP and ask the human; do not improvise.

## 0. What you must be given (the human supplies these; if any is missing, ask)
1. This document.
2. `feature_dictionary.csv` (what each of the 22 features means and what wording is accepted).
3. `ledger_protocol.md` (pooling rules; you do not pool, but you must know them).
4. The FULL TEXT of one paper at a time (PDF or pasted text, tables included).
5. The condition name, copied EXACTLY from this list: Malaria (P. vivax/falciparum) | Dengue (incl. hemorrhagic) | Typhoid fever | Scrub/murine typhus | Leptospirosis | Chikungunya | Viral ILI | Hepatitis A/E | Occult bacteremia (pneumonia/UTI-pyelo/intra-abdominal) | Rheumatic fever | TB (prolonged fever)
6. The list of papers for that condition (from the v3 script references, plus the data person's sources).

## 1. Absolute rules
- Use ONLY the paper text you were given. Do not use memory, general knowledge, other websites, or your own estimates for any number. If the paper does not report a feature, write nothing for that feature. "Not reported" is a correct answer.
- Never compute, average or pool across papers. One row = one condition x feature x paper (x component for composite features). Pooling is done later by a script.
- Never look at, ask about, or run the evaluation (`evaluate.py`), the vignettes, or any accuracy numbers. If you see them, tell the coordinator. Nobody who builds the ledger may adjust a number to make results look better.
- Never invent a source. Every row needs a citation you can point to (DOI or PMID) and the exact location of the numbers (Table 2 p.4, Results paragraph 2, abstract).
- Textbooks, StatPearls, Medscape, CDC, WHO fact sheets, Wikipedia and unnamed websites are NOT data sources. If the data person used one, record it as `secondary_web` or `textbook`, poolable N, with its URL. They can be used only as a sanity check.
- A number that is only a percentage (no count) is allowed only if you can back-calculate k from n; mark it `DERIVED` in notes and set poolable N. Never pool a derived k.
- Copy numbers exactly. If a paper's own percentages and counts disagree, record the COUNT, fill `reported_pct` with the printed percentage, and write the discrepancy in notes.

## 2. Step-by-step
**Step A. Describe the study once.** For each paper, write these down before extracting any feature: citation (authors, journal, year), PMID or DOI, country and city, setting (tertiary hospital, teaching hospital, community), cohort type (ALL confirmed cases of the condition, or a subset such as severe-only / CNS-only / ICU-only), age group (adult >=18, paediatric <18, mixed, not_stated), the case definition (which test, which cutoff), selection criteria (for example "fever >5 days required"), time period, and the total number of confirmed cases.

**Step B. Decide whether the paper can be pooled.** Poolable = Y only if ALL are true: it is a primary study; it reports counts or enough to get k for the full confirmed cohort; the denominator n is the whole cohort; it is not a subset-only cohort; the condition was confirmed by a defined test or criteria. A paper that compares severe vs non-severe patients WITHIN a full cohort is fine; use the total column. Reviews and meta-analyses are poolable N (they are recorded as `meta_pooled`; only the coordinator can mark one as a cell-value override).

**Step C. For each of the 22 features, look in the paper's tables, results text and abstract.** Use `feature_dictionary.csv` to decide the mapping:
- `exact`: the paper reports what the feature means.
- `proxy`: the paper reports a looser version listed under "proxy accepted" in the dictionary (for example any rash for rash_maculopapular). Flag it.
- `component`: the paper reports one part of a composite feature (gi_symptoms, hemorrhagic_signs). Fill `component` (for example vomiting, abdominal_pain, diarrhoea) and set poolable C (or N if the paper is not poolable). Never put a component into the composite itself as exact.
- If the wording is under "never accept", do not record it as a pooled row. You may record it with poolable N and a note so a human can decide.
- If the feature is not reported, no row.

**Step D. Fill one row per reported feature** using the columns below. Leave a column blank only where stated.

**Step E. Run the validator** (`python validate_ledger.py your_file.csv`). Fix every ERROR. Read every WARNING: either fix the row or explain it in notes.

**Step F. Hand over** `ledger_<condition>.csv`, `sources_<condition>.csv` (one line per paper: citation, link, access status = full text / abstract only / not obtained, flags), and `issues_<condition>.txt` (anything odd: typos in the paper, overlapping cohorts, papers you could not obtain, features you were unsure how to map).

## 3. Row columns (CSV header must match exactly)
`row_id` (prefix by condition: MAL-001, DEN-001, TYP-001, LEP-001, CHI-001, ILI-001, HEP-001, OCC-001, RF-001, TB-001) | `condition` | `feature` | `mapping` (exact / proxy / component) | `component` | `source_script_ref` (the [n] number from the v3 script, or not_in_script, or data_person) | `source_citation` | `estimate_type` (primary_k_n / meta_pooled / meta_raw / secondary_web / textbook) | `k` | `n` | `reported_pct` (printed percentage, or NA) | `pooled_value`, `ci_low`, `ci_high` (only for meta rows) | `age_group` | `country` | `setting_type` | `cohort_type` | `location_in_source` | `extraction_status` (verified_full_text / verified_abstract_only / verified_snippet_only / unverified) | `poolable` (Y / N / C) | `use_as_cell_value` (blank; coordinator only) | `notes`.
Primary rows: k and n must be whole numbers with 0 <= k <= n.

## 4. Traps already found in this project (look for them every time)
- Printed percentages that do not match the counts (typo in the paper). Record the count.
- A table header total that differs from the text total (546 vs 506): use the one that matches the sums, say so in notes.
- "Severe scrub typhus" titles that are actually full cohorts split into severe and non-severe. Read the methods; do not judge by title.
- Selection by inclusion criteria (fever >5 days required; pyrexia-of-unknown-origin cohorts; malaria and typhoid screened out first): put it in `cohort_type` and notes, especially for fever duration.
- Different case definitions (IgM ELISA cutoff 0.14 vs 0.5; Weil-Felix; PCR). Record the test and cutoff in cohort_type or notes.
- "Any" vs specific symptoms (rash vs maculopapular rash; lymphadenopathy vs regional; myalgia vs severe myalgia).
- Combined items ("nausea and vomiting", "hepatosplenomegaly"): record as the nearest component or poolable N, never as a clean single feature.
- Overlapping cohorts: same hospital and period, or one paper reanalysing another. Flag `possible_overlap_with <row_id>` and set the later one poolable N until the coordinator decides.
- Paediatric-only, adult-only and mixed cohorts: always set `age_group`.
- Meta-analyses: record their pooled value and CI as `meta_pooled`, poolable N, even if they look authoritative.

## 5. Quality control (the human reviewer, not the author, does this)
1. Validator has zero errors.
2. Reviewer opens the original paper and re-checks a random sample of the larger of 5 rows or 20% of rows (k, n, location, mapping, age_group, cohort type), plus every row that produced a validator warning.
3. Pass: every sampled row matches. If any sampled row is wrong, double the sample. If two or more are wrong, redo that paper.
4. The coordinator merges files (`validate_ledger.py a.csv b.csv --merge evidence_ledger_all.csv`) and runs the pooling script. Teammates do not edit the pooling script, the protocol or other conditions' files.

## 6. Finding papers (only after the listed ones are done)
- India-first: India case series and Indian meta-analyses give the target population. A cell is best supported by 3 or more India studies.
- A human must open every paper and confirm the title, authors and numbers. Do not rely on an AI's description of a paper it has not been given.
- Prefer open-access full text. For each paper you cannot obtain, list it in sources_<condition>.csv as "not obtained"; do not fill its numbers from memory or from a secondary source.

## 7. The data person's earlier edits
The current table contains values changed by a teammate from web sources. `table_diff_v3_vs_current.csv` lists every changed cell. For each changed cell of your condition, find his source, then enter it as ledger rows by the same rules. If the source is a website or textbook, record it as secondary_web or textbook, poolable N. If no source can be found, write that in issues_<condition>.txt.

## 8. When to stop and ask the coordinator
Any rule conflict; any mapping not covered by the dictionary; a paper that seems to reuse another paper's cohort; a paper whose numbers cannot be reconciled; any request, from anyone, to look at evaluation results.
