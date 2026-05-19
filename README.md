# Chimborazo Playground Priorities Survey

Public data and analysis for the May 2026 community survey at
Chimborazo Playground (Richmond, VA, Church Hill neighborhood).

The survey was launched after construction of new pétanque courts began
without public notice. The intent was to gather a broader picture of what
playground users want, share that picture with Council Member Cynthia
Newbille and Parks & Recreation Director Christopher Frelke at the
Church Hill Association meeting on May 19, 2026, and make the underlying
work auditable.

## What's here

- `code_survey.py` — the deterministic coding script. Single file, no
  third-party dependencies, Python 3.9+.
- `data/priorities-responses.csv` — the priorities survey, 251 raw rows,
  with the email column replaced by a stable hash (`respondent_id`).
- `data/petition-responses.csv` — the pause-construction petition, with
  email and name columns dropped and replaced by `respondent_id`.

The `respondent_id` is `"anon_" + sha256(lowercased_email)[:10]`. Same
person across both files gets the same id, so you can join the two
without ever seeing an email.

## Reproducing the numbers

```bash
python code_survey.py
python code_survey.py --dump-q2   # print every Q2 response with its assigned code
```

The script:

1. Dedupes by `respondent_id`. Six respondents submitted the priorities
   survey more than once (251 raw rows → 245 unique respondents). The
   latest non-blank Q2 submission per respondent is kept. The full
   dedupe trace prints on every run.
2. Codes each Q2 response into one of 15 documented buckets — six
   radio-button options plus nine write-in patterns (see `WRITEIN_RULES`
   in the script). Every rule is a substring match against the
   lowercased response; ordering of the rule list matters because
   bridge/mixed rules fire before simpler continue/reverse rules.
3. Tags Q3 (multi-select priorities) by substring against the standard
   option strings.
4. Tags Q1 and Q4 (free-text) themes by lowercased substring against
   the trigger lists at the bottom of the script.

Every count in the May 19 community-presentation synthesis comes
directly from one of these passes. If you disagree with a coding
judgment — for example, whether a particular write-in is "continue +
fix process" (B5) or just "continue" (B4) — the rule is editable in
one place and rerunning reproduces every downstream number.

## Survey instrument

Q1: *What do you want to say to Council Member Newbille and Director Frelke?*
(free text)

Q2: *How would you like the situation resolved now that construction is paused?*
(one of six radio options, or write-in "Other")

Q3: *What are your priorities for park improvements going forward?*
(pick up to three)

Q4: *Anything else you want the City or neighbors to know?*
(free text)

## Known limits of the coding

- Single-code-per-Q2-response: hybrid write-ins are forced into one
  bucket. The B5 bucket explicitly captures "continue + improve
  process" because it appeared often enough; other hybrids were
  assigned to the family that most strongly characterized the
  requested action.
- Theme tagging is substring matching: catches surface mentions, misses
  paraphrase, cannot detect sarcasm. Trigger lists are author judgment
  calls. They're all in the script and editable.
- The Q2 radio options did not originally include "complete the courts
  as planned"; that wording was added later as a write-in pattern
  (B4_WRITEIN_CONTINUE) but never as a radio button. Two respondents
  flagged the omission directly.

## Contact

communityforchimboplayground@gmail.com
