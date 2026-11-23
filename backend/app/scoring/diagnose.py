#!/usr/bin/env python3
"""
Terminal diagnostic narrowing.

Scoring layer = Bernoulli naive Bayes over a (condition x feature) table of
P(feature present | condition), with the next question chosen by expected
information gain (entropy reduction) over the current posterior.

Usage:  python diagnose.py table.csv

CSV format:
    condition,fever,eschar,rash,...,prior     <- 'prior' column is optional
    Malaria,0.95,0.01,0.05,...,0.2
    Dengue,0.9,0.0,0.5,...,0.2
Cells are P(feature present | condition) in [0, 1]. Without a 'prior'
column, priors are uniform.

Decision-support demo only, not a medical diagnosis tool.
"""
import csv
import difflib
import math
import sys

EPS = 0.02        # clip probabilities so one answer can never zero out a condition
STOP_P = 0.85     # stop when the top posterior reaches this
MAX_Q = 22        # question budget (skips count toward it)
MIN_GAIN = 0.01   # stop if the best remaining question gains fewer bits than this

# Features that can't sensibly be asked up front (outcome/course). They are still used
# if the user types them in the opening symptom list.
EXCLUDE = {"self_limited"}

# Lay wording for the questions. Edit freely; unknown features fall back to the column name.
QUESTIONS = {
    "fever_cyclical": "Does the fever come in cycles (spikes with fever-free gaps in between)?",
    "fever_continuous": "Is the fever continuous, without fever-free gaps?",
    "fever_prolonged": "Has the fever lasted unusually long (weeks rather than days)?",
    "rash_maculopapular": "Is there a red rash made of flat and raised spots?",
    "arthralgia_poly": "Pain in several joints at once?",
    "arthritis_migratory": "Joint pain/swelling that moves from one joint to another?",
    "sore_throat_preceding": "Was there a sore throat before the illness started?",
    "hemorrhagic_signs": "Any bleeding signs (gum/nose bleeding, bruising, petechiae, blood in stool/urine)?",
    "eschar": "Is there a dark scab-like lesion (eschar), e.g. a bite site with a black center?",
    "lymphadenopathy_reg": "Swollen lymph nodes in one region of the body?",
    "conjunctival_suffusion": "Red eyes without pus/discharge?",
    "myalgia_severe": "Severe muscle pain?",
    "jaundice": "Yellowing of the eyes or skin?",
    "gi_symptoms": "GI symptoms (nausea, vomiting, abdominal pain, diarrhea)?",
    "splenomegaly": "Enlarged spleen on examination?",
    "cough": "Cough?",
    "weight_loss": "Unintentional weight loss?",
    "night_sweats": "Night sweats?",
    "travel_endemic_hx": "Recent travel to, or residence in, an endemic area?",
    "water_exposure_hx": "Recent exposure to floodwater / freshwater / contaminated water?",
    "localizing_signs": "Any symptoms or signs pointing to one organ (chest, urinary tract, abdomen)?",
}


# ---------- data ----------
def load_table(path):
    conds, P, prior = [], [], []
    with open(path, newline="", encoding="utf-8-sig") as f:
        r = csv.DictReader(f)
        feats = [c for c in r.fieldnames if c.strip().lower() not in ("condition", "prior")]
        for row in r:
            conds.append(row["condition"].strip())
            P.append([min(max(float(row[ft]), EPS), 1 - EPS) for ft in feats])
            pr = (row.get("prior") or "").strip()
            prior.append(float(pr) if pr else 1.0)
    z = sum(prior)
    return conds, feats, P, [p / z for p in prior]


# ---------- scoring layer ----------
def entropy(dist):
    return -sum(p * math.log2(p) for p in dist if p > 0)


def update(post, P, j, present):
    """Bayes update after learning feature j is present/absent."""
    new = [post[i] * (P[i][j] if present else 1 - P[i][j]) for i in range(len(post))]
    z = sum(new)
    return [x / z for x in new]


def info_gain(post, P, j):
    """Expected entropy reduction (bits) from asking about feature j."""
    p_yes = sum(post[i] * P[i][j] for i in range(len(post)))
    h_after = (p_yes * entropy(update(post, P, j, True))
               + (1 - p_yes) * entropy(update(post, P, j, False)))
    return entropy(post) - h_after


def next_question(post, P, asked):
    cands = [(info_gain(post, P, j), j) for j in range(len(P[0])) if j not in asked]
    return max(cands) if cands else (0.0, None)


def ranked(post):
    return sorted(range(len(post)), key=lambda i: -post[i])


def shortlist(post, conds, mass=0.9, k=3):
    """Top conditions covering `mass` of the posterior (max k) -> feed these to RAG."""
    out, tot = [], 0.0
    for i in ranked(post):
        out.append(conds[i])
        tot += post[i]
        if tot >= mass or len(out) == k:
            break
    return out


# ---------- terminal I/O ----------
def norm(s):
    return s.lower().replace("_", " ").strip()


def parse_initial(line, feats):
    """'fever, no rash, -cough' -> {feature_idx: present?}; fuzzy-matches names."""
    keys = {norm(f): j for j, f in enumerate(feats)}
    found = {}
    for tok in line.split(","):
        tok = tok.strip()
        if not tok:
            continue
        present = True
        if tok.lower().startswith("no "):
            present, tok = False, tok[3:]
        elif tok.startswith("-"):
            present, tok = False, tok[1:]
        if norm(tok) == "fever":
            print("  ('fever' carries no information, every case is febrile; give the pattern, e.g. 'fever continuous')")
            continue
        sub = [k for k in keys if norm(tok) in k]          # 'travel' -> 'travel endemic hx'
        m = sub if len(sub) == 1 else difflib.get_close_matches(norm(tok), list(keys), n=1, cutoff=0.6)
        if m:
            found[keys[m[0]]] = present
        else:
            print(f"  (couldn't match '{tok.strip()}', type 'list' to see known symptoms)")
    return found


def show(post, conds, k=5):
    for i in ranked(post)[:k]:
        print(f"  {post[i]:6.1%}  {conds[i]}")


def main(path):
    conds, feats, P, post = load_table(path)
    asked = {feats.index(f) for f in EXCLUDE if f in feats}
    print("Decision-support demo, not a medical diagnosis.\n")

    while True:
        line = input("Presenting symptoms (comma-separated; 'no x' = absent; 'list' = show all): ").strip()
        if line.lower() == "list":
            print("  " + ", ".join(norm(f) for f in feats))
            continue
        break
    for j, present in parse_initial(line, feats).items():
        post = update(post, P, j, present)
        asked.add(j)
    print("\nAfter presenting symptoms:")
    show(post, conds)

    reason = "question budget reached"
    for q in range(1, MAX_Q + 1):
        if max(post) >= STOP_P:
            reason = "confident enough"
            break
        gain, j = next_question(post, P, asked)
        if j is None or gain < MIN_GAIN:
            reason = "no remaining question separates the candidates"
            break
        ans = None
        while ans not in ("y", "n", "s", "q"):
            text = QUESTIONS.get(feats[j], norm(feats[j]) + "?")
            ans = input(f"\n[{q}/{MAX_Q}] {text} [{feats[j]}]  (y/n/s=don't know/r=ranking/q=stop) ").strip().lower()
            if ans == "r":
                show(post, conds)
        asked.add(j)
        if ans == "q":
            reason = "stopped by user"
            break
        if ans in ("y", "n"):          # 's' just moves on; unknown is NOT treated as 'no'
            post = update(post, P, j, ans == "y")
        print()
        show(post, conds, k=3)

    print(f"\n=== Result ({reason}) ===")
    show(post, conds)
    print(f"\nTop guess: {conds[ranked(post)[0]]}")
    print(f"Shortlist for guideline retrieval: {shortlist(post, conds)}")
    return shortlist(post, conds)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python diagnose.py table.csv")
    main(sys.argv[1])