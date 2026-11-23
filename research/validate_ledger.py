"""Validate evidence-ledger CSV file(s) against the project schema and rules.
Usage:  python validate_ledger.py ledger_dengue.csv [more.csv ...] [--merge merged.csv]
ERRORs block (exit code 1). WARNINGs need a human look. --merge writes the combined file only if there are no errors."""
import sys
import numpy as np, pandas as pd

CONDS = ["Malaria (P. vivax/falciparum)", "Dengue (incl. hemorrhagic)", "Typhoid fever", "Scrub/murine typhus", "Leptospirosis", "Chikungunya",
         "Viral ILI", "Hepatitis A/E", "Occult bacteremia (pneumonia/UTI-pyelo/intra-abdominal)", "Rheumatic fever", "TB (prolonged fever)"]
FEATS = ["fever_cyclical","fever_continuous","fever_prolonged","rash_maculopapular","arthralgia_poly","arthritis_migratory","sore_throat_preceding",
         "hemorrhagic_signs","eschar","lymphadenopathy_reg","conjunctival_suffusion","myalgia_severe","jaundice","gi_symptoms","splenomegaly","cough",
         "weight_loss","night_sweats","travel_endemic_hx","water_exposure_hx","localizing_signs","self_limited"]
COMPOSITE = {"gi_symptoms", "hemorrhagic_signs"}
REQ = ["row_id","condition","feature","mapping","component","source_script_ref","source_citation","estimate_type","k","n","reported_pct","pooled_value","ci_low","ci_high",
       "age_group","country","setting_type","cohort_type","location_in_source","extraction_status","poolable","use_as_cell_value","notes"]
ESTIMATE = {"primary_k_n","meta_pooled","meta_raw","secondary_web","textbook"}
AGE = {"adult","paediatric","mixed","not_stated"}
STATUS = {"verified_full_text","verified_abstract_only","verified_snippet_only","unverified"}
SUBSET_WORDS = ("severe-only","severe only","cns-only","cns only","subset only","meningitis-only")

def num(x):
    try: return float(x)
    except (TypeError, ValueError): return np.nan

def check(df, name):
    E, W = [], []
    miss = [c for c in REQ if c not in df.columns]
    if miss: return [f"{name}: missing columns {miss}"], []
    seen = set()
    for _, r in df.iterrows():
        rid = str(r.row_id); e = lambda m: E.append(f"{name} {rid}: {m}"); w = lambda m: W.append(f"{name} {rid}: {m}")
        if rid in seen or rid in ("", "nan"): e("row_id empty or duplicated")
        seen.add(rid)
        if r.condition not in CONDS: e(f"condition {r.condition!r} not one of the 11 table names (copy it exactly)")
        if r.feature not in FEATS: e(f"feature {r.feature!r} not in the 22-feature list")
        if r.mapping not in ("exact","proxy","component"): e("mapping must be exact / proxy / component")
        if r.estimate_type not in ESTIMATE: e(f"estimate_type must be one of {sorted(ESTIMATE)}")
        if r.age_group not in AGE: e(f"age_group must be one of {sorted(AGE)}")
        if r.extraction_status not in STATUS: e(f"extraction_status must be one of {sorted(STATUS)}")
        if r.poolable not in ("Y","N","C"): e("poolable must be Y, N or C")
        for c in ("source_citation","location_in_source","country","cohort_type"):
            if str(r[c]).strip() in ("", "nan"): e(f"{c} is empty")
        k, n = num(r.k), num(r.n); notes = str(r.notes); cohort = str(r.cohort_type).lower()
        if r.mapping == "component":
            if r.feature not in COMPOSITE: e("component rows only allowed for composite features (gi_symptoms, hemorrhagic_signs)")
            if str(r.component).strip() in ("", "nan"): e("component name missing")
            if r.poolable not in ("C","N"): e("component rows must be poolable C or N")
        elif r.poolable == "C": e("poolable C is only for mapping=component rows")
        if r.estimate_type == "primary_k_n":
            if np.isnan(k) or np.isnan(n): e("k and n are required for primary_k_n rows")
            else:
                if k != int(k) or n != int(n): e("k and n must be whole numbers")
                if k < 0 or k > n: e(f"k={k:g} must be between 0 and n={n:g}")
                rp = str(r.reported_pct).strip()
                if rp in ("", "nan"): e("reported_pct required (the percentage printed in the paper, or NA if the paper gives only a count)")
                elif rp.upper() != "NA":
                    d = abs(100 * k / n - num(rp))
                    if d > 0.2: w(f"k/n = {100*k/n:.1f}% but the paper prints {rp}%: re-check, and if the paper itself is inconsistent say so in notes")
            if "DERIVED" in notes.upper() and r.poolable != "N": e("derived k (back-calculated from a percentage) must be poolable N")
        else:
            if r.poolable != "N" and str(r.use_as_cell_value) != "Y": e("non-primary rows (meta, web, textbook) must be poolable N")
        if r.poolable in ("Y","C"):
            if r.extraction_status not in ("verified_full_text","verified_abstract_only"): e("pooled rows need verified full text or abstract with explicit counts")
            if r.poolable == "Y" and r.mapping == "component": e("component rows cannot be poolable Y")
            if any(s in cohort or s in notes.lower() for s in SUBSET_WORDS): w("looks like a subset cohort (severe-only / CNS-only): poolable should be N")
        if str(r.use_as_cell_value) == "Y":
            if r.estimate_type != "meta_pooled" or any(np.isnan(num(r[c])) for c in ("pooled_value","ci_low","ci_high")): e("use_as_cell_value=Y needs a meta_pooled row with pooled_value and CI")
        if r.estimate_type in ("secondary_web","textbook") and "http" not in str(r.source_citation).lower() and "doi" not in str(r.source_citation).lower():
            w("web/textbook rows need a URL or DOI in source_citation")
    pr = df[(df.estimate_type == "primary_k_n") & df.poolable.isin(["Y"])]
    dup = df[df.duplicated(["condition","feature","source_citation","component"], keep=False) & (df.estimate_type == "primary_k_n")]
    for _, r in dup.iterrows(): E.append(f"{name} {r.row_id}: duplicate of another row (same condition, feature, paper, component)")
    for src, g in pr.groupby("source_citation"):
        if g.n.nunique() > 1: W.append(f"{name}: '{str(src)[:50]}' has different n across Y rows ({sorted(g.n.unique())}); fine if features were assessed in subsets, otherwise check")
    return E, W

if __name__ == "__main__":
    args = [a for a in sys.argv[1:]]
    out = args[args.index("--merge") + 1] if "--merge" in args else None
    files = [a for a in args if a.endswith(".csv") and a != out]
    if not files: sys.exit(__doc__)
    frames, E, W = [], [], []
    for f in files:
        df = pd.read_csv(f, dtype=str, keep_default_na=False); e, w = check(df, f); E += e; W += w; frames.append(df)
    if len(frames) > 1:
        allr = pd.concat(frames); d = allr[allr.duplicated("row_id", keep=False)]
        E += [f"row_id {i} used in more than one file" for i in d.row_id.unique()]
    print(f"{sum(len(f) for f in frames)} rows in {len(files)} file(s): {len(E)} error(s), {len(W)} warning(s)")
    for m in E: print("ERROR  ", m)
    for m in W: print("WARNING", m)
    if out and not E: pd.concat(frames).to_csv(out, index=False); print(f"merged -> {out}")
    sys.exit(1 if E else 0)
