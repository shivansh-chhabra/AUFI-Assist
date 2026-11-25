"""Render app/protocols/test_protocols.json as a readable review document.

    python scripts/render_protocols_md.py        # writes docs/TEST_PROTOCOLS.md

The JSON is the single source of truth: edit it, then re-run this, so the two never disagree.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D = json.loads((ROOT / "app/protocols/test_protocols.json").read_text(encoding="utf-8"))
T, S = D["tests"], D["sources"]


def cite(refs):
    return "; ".join(f"{r.partition(':')[0]} {r.partition(':')[2]}" for r in refs)


def row(e):
    w = e.get("when", {}).get("text") or ""
    n = T[e["test"]]
    return f"| {n['name']} | {n['specimen']} | {w} | {e['why']} | {cite(e['src'])} |"


out = [f"# {D['meta']['title']}", "", f"**Status:** {D['meta']['status']}  ", f"**Version:** {D['meta']['version']}  ",
       f"**Scope:** {D['meta']['scope']}", "", D["meta"]["how_to_read"], "", "## Sources", "",
       "| Id | Document | Issuer | Year | Read |", "|---|---|---|---|---|"]
out += [f"| {k} | {v['title']} | {v['issuer']} | {v['year']} | {v['read']} |" for k, v in S.items()]
out += ["", "## Baseline work-up by day of fever (all conditions)", ""]
out += [f"- **{s['id'].replace('_', ' ')}**: {s['text']} ({cite(s['src'])})" for s in D["common_workup"]]
head = "| Test | Specimen | When valid | Why | Source |\n|---|---|---|---|---|"
for cid, c in D["conditions"].items():
    out += ["", f"## {cid.replace('_', ' ').title()}", ""]
    for key, label in (("first_line", "First-line tests"), ("conditional", "Only if"), ("also", "Also useful"),
                       ("if_severe", "If severe"), ("not_recommended", "Not recommended")):
        items = c.get(key, [])
        if not items:
            continue
        out += [f"**{label}**", ""]
        if key == "conditional":
            out += [f"- If {e['if_']}: {T[e['test']]['name']}. {e['why']} ({cite(e['src'])})" for e in items]
        else:
            out += [head] + [row(e) for e in items]
        out.append("")
    for n in c.get("notes", []):
        out.append(f"> {n['text']} ({cite(n['src'])})")
out += ["", "## When the leading conditions are close", "",
        f"Rule for pairs without an entry below: {D['default_pair_rule']}", ""]
for p in D["pair_differentiators"]:
    a, b = (x.replace("_", " ").title() for x in p["pair"])
    out += [f"### {a} vs {b}", "", "Send: " + "; ".join(T[t]["name"] for t in p["tests"]) + ".", "",
            f"{p['contrast']} ({cite(p['src'])})", ""]
out += ["## Where the guidelines disagree", ""] + [f"- {x}" for x in D["conflicts"]]
out += ["", "## Open items before clinical use", ""] + [f"- {x}" for x in D["open_items"]]
(ROOT / "docs").mkdir(exist_ok=True)
(ROOT / "docs/TEST_PROTOCOLS.md").write_text("\n".join(out) + "\n", encoding="utf-8")
print("wrote docs/TEST_PROTOCOLS.md")
