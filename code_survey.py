#!/usr/bin/env python3
"""Deterministic coding of the Chimborazo Playground Priorities Survey.

Pipeline:
  1. Load priorities-responses.csv
  2. Dedupe by lowercased email. Latest submission (by Timestamp) wins.
     Justification: 6 emails (out of 251 rows) have multiple submissions.
     In every observed dupe, either (a) the later submission was blank
     (the form's confirmation re-submit), (b) the responses were identical,
     or (c) the respondent revised their answer; in case (c) treating the
     final response as authoritative is the standard interpretation.
  3. Code Q2 with a single primary code drawn from a fixed 15-bucket scheme.
     Standard radio options map to their own codes; write-ins are matched
     against an explicit keyword/keyphrase list (printed below in --verbose).
  4. Tag Q3 priorities by exact-substring match against the standard option
     phrases (each respondent can pick up to 3, so percentages sum >100%).
  5. Tag Q1/Q4 themes by lowercased-substring keyword matching against
     trigger lists. The same response can carry multiple tags.

Output: counts + percentages for Q1 themes, Q2 codes, Q3 priorities, Q4 themes.
Use --dump-q2 to print every Q2 response with its assigned code (for review).

Run from chimbo/:
    python scripts/code_survey.py
    python scripts/code_survey.py --dump-q2
"""

import argparse
import csv
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CSV_PATH = ROOT / "data" / "priorities-responses.csv"

Q1 = "What do you want to say to Council Member Newbille and Director Frelke?"
Q2 = "How would you like the situation resolved now that construction is paused?"
Q3 = "What are your priorities for park improvements going forward? (Choose up to three)"
Q4 = "Anything else you want the City or neighbors to know?"

# Q2 standard radio options (exact strings).
A1_RADIO = "Reverse construction on the new petanque courts, and redirect resources to other improvements."
A2_RADIO = "Address maintenance, health and safety needs in the park before any space is expanded or developed."
A3_RADIO = "Share full plans and invite public review and input before adopting any changes."
B1_RADIO = "Build the new petanque courts as planned only after sharing full plans for public review and notice."
B2_RADIO = "Find a way to build the new petanque courts, and remove the old ones for other park use."
B3_RADIO = "Finish building the new courts and proceed with the other playground improvements as planned."

RADIO_CODE = {
    A1_RADIO: "A1_REVERSE",
    A2_RADIO: "A2_MAINTENANCE_FIRST",
    A3_RADIO: "A3_SHARE_PLANS",
    B1_RADIO: "B1_CONDITIONAL_CONTINUE",
    B2_RADIO: "B2_BUILD_NEW_REMOVE_OLD",
    B3_RADIO: "B3_FINISH_AS_PLANNED",
}

# Q2 write-in classification. Each entry is (substring_trigger, code).
# Triggers are lowercased-substring matches. First matching trigger wins,
# so order matters — bridge/mixed rules are evaluated BEFORE simpler rules.
#
# Codes:
#   B5_CONTINUE_PLUS_PROCESS — explicitly continues AND improves the
#     city's communication / public-input process going forward.
#   M_MIXED_OR_DEPENDS — endorses multiple radio options or conditions
#     answer on factors not in the form ("it depends", "options 1, 2, 3").
#   A_WRITEIN_REVERSE — write-in calling to undo / lawn / remove courts.
#   A_WRITEIN_MAINTENANCE — write-in calling to fix bathrooms etc.
#   A_WRITEIN_SHARE_PLANS — write-in calling for share-plans-first
#     (often combined with A2 maintenance).
#   B4_WRITEIN_CONTINUE — write-in that just says continue / finish /
#     build / resume / unpause as planned.
#   Z1_BLANK / Z2_JUNK / Z3_FEATURE_REQUEST — unusable.
WRITEIN_RULES = [
    # B5 — explicit continue + fix process for next time
    ("be more transparent in future", "B5_CONTINUE_PLUS_PROCESS"),
    ("better communication", "B5_CONTINUE_PLUS_PROCESS"),
    ("better about public notice", "B5_CONTINUE_PLUS_PROCESS"),
    ("correct the identified communications gap", "B5_CONTINUE_PLUS_PROCESS"),
    ("learn how to engage folks", "B5_CONTINUE_PLUS_PROCESS"),
    ("shares a clear phased improvement plan", "B5_CONTINUE_PLUS_PROCESS"),
    ("park should always communicate changes going forward", "B5_CONTINUE_PLUS_PROCESS"),
    ("if you want to fix the process for your future requests", "B5_CONTINUE_PLUS_PROCESS"),
    # M — explicit it-depends / multi-option
    ("it depends", "M_MIXED_OR_DEPENDS"),
    ("options 1, 2", "M_MIXED_OR_DEPENDS"),
    ("options 1,2", "M_MIXED_OR_DEPENDS"),
    ("ok w/options", "M_MIXED_OR_DEPENDS"),
    ("ok w/ options", "M_MIXED_OR_DEPENDS"),
    ("all of these are options", "M_MIXED_OR_DEPENDS"),
    ("continue the expansion as planned and also address maintenance", "M_MIXED_OR_DEPENDS"),
    # Z — junk / not-an-answer
    ("see above", "Z2_JUNK"),  # "Please see above comment" / "See above."
    ("we want pickleball", "Z3_FEATURE_REQUEST"),
    # B4 — pure continue / build / finish / resume / unpause / proceed
    ("build the petanque courts", "B4_WRITEIN_CONTINUE"),
    ("build the pétanque courts", "B4_WRITEIN_CONTINUE"),
    ("build petanque courts", "B4_WRITEIN_CONTINUE"),
    ("build the courts", "B4_WRITEIN_CONTINUE"),
    ("build as planned", "B4_WRITEIN_CONTINUE"),
    ("continue building", "B4_WRITEIN_CONTINUE"),
    ("continue with the improvement", "B4_WRITEIN_CONTINUE"),
    ("continue as planned", "B4_WRITEIN_CONTINUE"),
    ("continue with construction as planned", "B4_WRITEIN_CONTINUE"),
    ("continue to build", "B4_WRITEIN_CONTINUE"),
    ("by unpausing", "B4_WRITEIN_CONTINUE"),
    ("unpause the new courts", "B4_WRITEIN_CONTINUE"),
    ("finish the construction", "B4_WRITEIN_CONTINUE"),
    ("finish the courts", "B4_WRITEIN_CONTINUE"),
    ("finish new courts", "B4_WRITEIN_CONTINUE"),
    ("finish the new courts", "B4_WRITEIN_CONTINUE"),
    ("finish building the new", "B4_WRITEIN_CONTINUE"),
    ("finish the plans for the new petanque", "B4_WRITEIN_CONTINUE"),
    ("finish the pétanque courts as part of a park improvement", "B4_WRITEIN_CONTINUE"),
    ("go ahead and finish", "B4_WRITEIN_CONTINUE"),
    ("just fininish", "B4_WRITEIN_CONTINUE"),
    ("just finish", "B4_WRITEIN_CONTINUE"),
    ("resume construction", "B4_WRITEIN_CONTINUE"),
    ("resume the project", "B4_WRITEIN_CONTINUE"),
    ("follow the current plan", "B4_WRITEIN_CONTINUE"),
    ("please complete the courts", "B4_WRITEIN_CONTINUE"),
    ("the current plan should be completed", "B4_WRITEIN_CONTINUE"),
    ("courts were approved and construction has begun", "B4_WRITEIN_CONTINUE"),
    ("omitted the most logical answer", "B4_WRITEIN_CONTINUE"),
    ("courts as planned", "B4_WRITEIN_CONTINUE"),
    ("add the new courts", "B4_WRITEIN_CONTINUE"),
    ("to keep existing pétanque courts along with the construction", "B4_WRITEIN_CONTINUE"),
    ("to keep existing petanque courts along with the construction", "B4_WRITEIN_CONTINUE"),
    # A1 — reverse / lawn / remove / preserve green space
    ("reverse construction", "A_WRITEIN_REVERSE"),
    ("restore the lawn", "A_WRITEIN_REVERSE"),
    ("put it to grass", "A_WRITEIN_REVERSE"),
    ("put in grass", "A_WRITEIN_REVERSE"),
    ("remove the pentanque", "A_WRITEIN_REVERSE"),
    ("preserve the green space", "A_WRITEIN_REVERSE"),
    ("99.5% of the community that does not play", "A_WRITEIN_REVERSE"),
    ("re-sod", "A_WRITEIN_REVERSE"),
    ("reconfigure existing courts", "A_WRITEIN_REVERSE"),
    ("no new pétanque courts", "A_WRITEIN_REVERSE"),
    # A2 — bathrooms / maintenance only
    ("fix the bathrooms", "A_WRITEIN_MAINTENANCE"),
    # A3 — share plans / public review first / start over
    ("share full plans", "A_WRITEIN_SHARE_PLANS"),
    ("share plans and invite public review", "A_WRITEIN_SHARE_PLANS"),
    ("ideally, the city would address maintenance and health/safety concerns while sharing full plans", "A_WRITEIN_SHARE_PLANS"),
    ("start over", "A_WRITEIN_SHARE_PLANS"),
    ("fix the process first", "A_WRITEIN_SHARE_PLANS"),
    ("legitimate master plan", "A_WRITEIN_SHARE_PLANS"),
    ("do a real master plan", "A_WRITEIN_SHARE_PLANS"),
    ("master plan for chimborazo", "A_WRITEIN_SHARE_PLANS"),
    ("addressing maintenance, health and safety should be done first", "A2_MAINTENANCE_FIRST"),
]

# Q3 standard option strings.
Q3_OPTIONS = [
    ("Restrooms and water fountain access", "PRI_RESTROOMS_WATER"),
    ("Additional landscaping", "PRI_LANDSCAPING"),
    ("Improvements to existing courts", "PRI_EXISTING_COURTS"),
    ("Water feature", "PRI_WATER_FEATURE"),
    ("Mulch", "PRI_MULCH"),
    ("Expand one or more existing uses", "PRI_EXPAND_USES"),
    ("Renovate park house", "PRI_PARK_HOUSE"),
    ("New spaces", "PRI_NEW_SPACES"),
    ("Fenced area for dogs", "PRI_FENCED_DOGS"),
]

# Q1 / Q4 free-text theme triggers (lowercased substring match).
Q1_THEMES = {
    "PROCESS_TRANSPARENCY": ["transparen", "process", "public input", "notice", "inform", "communicat", "involve", "engage", "public comment", "represent"],
    "GRATITUDE": ["thank you", "thank", "appreciate", "grateful", "gratitude"],
    "TAX_SPENDING": ["tax", "dollars", "funds", "budget", "spend", "money"],
    "BROADER_OVER_NICHE": ["niche", "small group", "minorit", "majority", "whole community", "broader", "everyone", "most users", "45 ", "few", "select "],
    "KIDS_FAMILIES": ["kid", "children", "famil", "play equip", "toddler", "preschool", "young"],
    "GREEN_SPACE": ["green", "lawn", "grass", "open space", "field", "turf"],
    "PETANQUE_SUPPORTIVE": ["pétanque court", "petanque court", "petanque player", "pétanque player", "continue", "finish"],
    "BATHROOMS_MAINTENANCE": ["bathroom", "restroom", "water fountain", "maintenance"],
    "FOCP_REPRESENTATION": ["focp", "friends of", "represent", "who decides", "committee"],
}

Q4_THEMES = {
    "TRANSPARENCY_PROCESS": ["transparen", "process", "public input", "notice", "inform", "communicat", "represent", "engage"],
    "GRATITUDE": ["thank", "appreciate", "grateful"],
    "TAX_SPENDING": ["tax", "dollars", "funds", "budget", "spend", "money"],
    "KIDS_FAMILIES": ["kid", "children", "famil", "play equip", "toddler", "preschool", "young"],
    "GREEN_SPACE": ["green", "lawn", "grass", "open space", "field", "turf"],
    "INCLUSIVITY_FORUM": ["inclusive", "forum", "voice", "access", "diverse"],
    "BATHROOMS_MAINTENANCE": ["bathroom", "restroom", "water fountain", "maintenance"],
    "HISTORICAL_DECISION_CHAIN": ["who decided", "who said", "how did this", "apolog", "historical", "4th baptist", "2012"],
    "OPPOSITION_DEFEND_PROJECT": ["don't need", "just fininish", "just finish", "wasted", "dumb", "projects built", "we want pickle"],
}


def parse_ts(s: str) -> datetime:
    return datetime.strptime(s, "%d/%m/%Y %H:%M:%S")


def load_and_dedupe(path: Path) -> tuple[list[dict], dict]:
    """Return (deduped rows, dedupe stats). Latest submission per respondent wins.

    Accepts either the private CSV (column "Email address") or the public CSV
    (column "respondent_id" with hashed values) - both are stable identifiers
    that group multiple submissions from the same person.
    """
    with path.open() as f:
        rows = list(csv.DictReader(f))

    id_col = "respondent_id" if "respondent_id" in rows[0] else "Email address"
    by_id: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        key = r[id_col].strip().lower()
        if not key:
            continue
        by_id[key].append(r)

    stats = {
        "raw_rows": len(rows),
        "unique_respondents": len(by_id),
        "dupe_respondents": sum(1 for v in by_id.values() if len(v) > 1),
        "extra_dupe_rows": sum(len(v) - 1 for v in by_id.values() if len(v) > 1),
        "dupe_resolutions": [],
        "id_col": id_col,
    }

    deduped = []
    for key, subs in by_id.items():
        subs_sorted = sorted(subs, key=lambda r: parse_ts(r["Timestamp"]))
        kept = subs_sorted[-1]
        if len(subs) > 1:
            if not kept[Q2].strip():
                for s in reversed(subs_sorted[:-1]):
                    if s[Q2].strip():
                        kept = s
                        break
            stats["dupe_resolutions"].append({
                "respondent": key,
                "n_subs": len(subs),
                "kept_ts": kept["Timestamp"],
                "all_q2": [s[Q2][:60] for s in subs_sorted],
            })
        deduped.append(kept)

    return deduped, stats


def code_q2(response: str) -> str:
    v = response.strip()
    if not v:
        return "Z1_BLANK"
    if v in RADIO_CODE:
        return RADIO_CODE[v]
    lv = v.lower()
    for trigger, code in WRITEIN_RULES:
        if trigger.lower() in lv:
            return code
    # Heuristic fallback: a response that is only a 1-3 word name-shaped
    # token with no action verb is Z2_JUNK. Catches both "Alexander Lyons"
    # and "phillip perrow"-style entries (case-insensitive).
    action_words = {
        "build", "finish", "add", "keep", "remove", "fix", "complete",
        "stop", "pause", "continue", "resume", "reverse", "share", "find",
        "grass", "petanque", "pétanque", "courts", "court", "lawn",
        "preserve", "restore", "redirect", "expand",
    }
    if (1 <= len(v.split()) <= 3
            and v.replace(" ", "").replace("-", "").replace("'", "").isalpha()
            and not any(w.lower() in action_words for w in v.split())):
        return "Z2_JUNK"
    return "UNCLASSIFIED"


def tag_q3(response: str) -> list[str]:
    tags = []
    for needle, code in Q3_OPTIONS:
        if needle in response:
            tags.append(code)
    return tags


def tag_themes(text: str, themes: dict[str, list[str]]) -> list[str]:
    lv = text.lower()
    return [name for name, triggers in themes.items() if any(t in lv for t in triggers)]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump-q2", action="store_true",
                    help="Print every Q2 response with its assigned code.")
    ap.add_argument("--csv", default=str(CSV_PATH))
    args = ap.parse_args()

    rows, dedupe = load_and_dedupe(Path(args.csv))
    n = len(rows)
    print("=" * 70)
    print("CHIMBORAZO PLAYGROUND PRIORITIES SURVEY — DETERMINISTIC CODING")
    print("=" * 70)
    print(f"Raw rows in CSV:                {dedupe['raw_rows']}")
    print(f"Unique respondents (deduped):     {dedupe['unique_respondents']}")
    print(f"Respondents with multiple subs:   {dedupe['dupe_respondents']}")
    print(f"Extra rows removed via dedupe:    {dedupe['extra_dupe_rows']}")
    print()
    print("Dedupe resolutions (latest non-blank Q2 per respondent is kept):")
    for r in dedupe["dupe_resolutions"]:
        print(f"  {r['respondent']}  ({r['n_subs']} subs, kept ts={r['kept_ts']})")
        for i, q2 in enumerate(r["all_q2"]):
            print(f"     [{i+1}] {q2!r}")
    print()

    # Q2
    print("-" * 70)
    print(f"Q2 — single primary code per response (n={n})")
    print("-" * 70)
    q2_codes = Counter()
    unclass = []
    rows_with_code = []
    for r in rows:
        c = code_q2(r[Q2])
        q2_codes[c] += 1
        rows_with_code.append((r, c))
        if c == "UNCLASSIFIED":
            unclass.append(r[Q2])

    code_order = [
        "A1_REVERSE", "A2_MAINTENANCE_FIRST", "A3_SHARE_PLANS",
        "A_WRITEIN_REVERSE", "A_WRITEIN_MAINTENANCE", "A_WRITEIN_SHARE_PLANS",
        "B1_CONDITIONAL_CONTINUE", "B2_BUILD_NEW_REMOVE_OLD", "B3_FINISH_AS_PLANNED",
        "B4_WRITEIN_CONTINUE", "B5_CONTINUE_PLUS_PROCESS",
        "M_MIXED_OR_DEPENDS",
        "Z1_BLANK", "Z2_JUNK", "Z3_FEATURE_REQUEST",
        "UNCLASSIFIED",
    ]
    total_check = 0
    for code in code_order:
        c = q2_codes[code]
        total_check += c
        if c or code != "UNCLASSIFIED":
            print(f"  {c:>4}  ({c/n:>5.1%})  {code}")
    print(f"  {'-' * 4}")
    print(f"  {total_check:>4}  total")
    if unclass:
        print("\nUNCLASSIFIED responses (need new rule):")
        for u in unclass:
            print(f"  {u!r}")

    # Family roll-ups
    print()
    a_pure = q2_codes["A1_REVERSE"] + q2_codes["A_WRITEIN_REVERSE"]
    a_pause = (q2_codes["A2_MAINTENANCE_FIRST"] + q2_codes["A3_SHARE_PLANS"]
               + q2_codes["A_WRITEIN_MAINTENANCE"] + q2_codes["A_WRITEIN_SHARE_PLANS"])
    b_continue = (q2_codes["B1_CONDITIONAL_CONTINUE"] + q2_codes["B2_BUILD_NEW_REMOVE_OLD"]
                  + q2_codes["B3_FINISH_AS_PLANNED"] + q2_codes["B4_WRITEIN_CONTINUE"]
                  + q2_codes["B5_CONTINUE_PLUS_PROCESS"])
    m = q2_codes["M_MIXED_OR_DEPENDS"]
    z = q2_codes["Z1_BLANK"] + q2_codes["Z2_JUNK"] + q2_codes["Z3_FEATURE_REQUEST"]
    print("Three-way family roll-up:")
    print(f"  REVERSE (A1 + writein-reverse):       {a_pure:>4} ({a_pure/n:>5.1%})")
    print(f"  PAUSE for process (A2 + A3 + variants): {a_pause:>4} ({a_pause/n:>5.1%})")
    print(f"  CONTINUE (all B family inc. B5):      {b_continue:>4} ({b_continue/n:>5.1%})")
    print(f"  Mixed:                                 {m:>4} ({m/n:>5.1%})")
    print(f"  Unusable:                              {z:>4} ({z/n:>5.1%})")
    print()
    # Bridge sub-counts
    print(f"  ... of CONTINUE, pure: {b_continue - q2_codes['B5_CONTINUE_PLUS_PROCESS']:>4}")
    print(f"  ... of CONTINUE, bridge (B5): {q2_codes['B5_CONTINUE_PLUS_PROCESS']:>4}")

    # Q3
    print()
    print("-" * 70)
    print(f"Q3 — multi-select priorities (n={n})")
    print("-" * 70)
    q3 = Counter()
    for r in rows:
        for tag in tag_q3(r[Q3]):
            q3[tag] += 1
    for _, code in Q3_OPTIONS:
        c = q3[code]
        print(f"  {c:>4}  ({c/n:>5.1%})  {code}")

    # Q1 / Q4 themes
    for label, qcol, themes in [("Q1", Q1, Q1_THEMES), ("Q4", Q4, Q4_THEMES)]:
        nonblank = [r for r in rows if r[qcol].strip()]
        nn = len(nonblank)
        print()
        print("-" * 70)
        print(f"{label} — free-text themes (out of {nn} non-blank responses)")
        print("-" * 70)
        counts = Counter()
        for r in nonblank:
            for t in tag_themes(r[qcol], themes):
                counts[t] += 1
        for theme, c in counts.most_common():
            print(f"  {c:>4}  ({c/nn:>5.1%})  {theme}")

    if args.dump_q2:
        print()
        print("=" * 70)
        print("FULL Q2 DUMP")
        print("=" * 70)
        for r, c in rows_with_code:
            print(f"\n[{c}] {r[dedupe['id_col']]}")
            print(f"  {r[Q2]!r}")


if __name__ == "__main__":
    main()
