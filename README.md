# Chimborazo Playground Priorities Survey

Anonymized data and the coding script behind the May 2026 community survey at
Chimborazo Playground (Richmond, VA, Church Hill neighborhood).

## Quick links

- **[Survey responses (CSV)](data/priorities-responses.csv)** — 273 raw submissions / 267 unique respondents after dedupe; emails hashed to `anon_xxxxxxxxxx` IDs.
- **[Petition signers (CSV)](data/petition-responses.csv)** — 250 signers. Names and emails removed; awareness Q&A preserved.
- **[Coding script](code_survey.py)** — single Python file, no dependencies, reproduces every count in the written synthesis.
- **[Saved coding output](coding-output.txt)** — what the script printed when run against this data. Skip running the script if you just want to read the numbers.
- **[Per-response Q2 dump](coding-output-dump.txt)** — every Q2 response with its assigned code, for spot-checking judgment calls.

## Voices from the survey

A small curated selection. Same `anon_` IDs as in the CSV, so you can find the
full record. The selection tries to represent the range of views, not just the
majority position.

### From parents and playground regulars

> "I am a Church Hill resident and frequent user of the playground as a mom with two small kids. I would have loved for more input. However, progress on parks takes forever. Reversing the work will cost more money and the park will not be better for it."
> *— anon_a5a3bdc266*

> "I've lived in this neighborhood for 12 years and our two children have been raised here. We love and used Chimborazo untold times. As my children have grown older the green spaces in the park are the most frequented: playing catch, throwing the lacrosse ball, running around and riding bikes."
> *— anon_110f81fd66*

> "Working restrooms for our kids and re-mulching or re-surfacing of the playground are our family's top priorities. There's nowhere for them to go to the bathroom while we're at the park, and within the existing mulch there is a cotton-like substance that comes up from the ground and the kids' feet get tangled in it. There are also exposed roots everywhere that they trip on."
> *— anon_56fa6db030*

> "It would be wonderful if we had an alternative to the mulch and dirt on the playground. I always have to give my child a bath after using the playground because she becomes filthy and covered in dirt every time."
> *— anon_a5c966188a*

> "My family spends 4–10 hours a week at the Chimborazo Playground, yet I never saw any information about the petanque expansion — or about other recent additions, like the soccer goal, basketball hoop, or climbing structure."
> *— anon_1eddc6ad65*

> "I'm a teacher at a local Church Hill school. The elementary students and myself are actually writing this survey together! They use the playground weekly for tennis and P.E. lessons. Students report falling on the gravel and would like more green space to be able to run and play games, like soccer."
> *— anon_2b85a78a13*

### On the communication gap

> "I believe much of the frustration surrounding the new petanque courts is the result of a communication and transparency failure from the City and Parks Department, not from the petanque community itself."
> *— anon_db98102d55*

> "Can any random park goer get fully up to speed at any time in 5 minutes or less? Can they do it without calling/emailing a department, searching 10 different social media accounts or attending a monthly meeting every month?"
> *— anon_b5187c4bba*

> "Communication from the City is often obscure and opaque. Even for those who're active and involved, it can be difficult to keep up or be aware of inbound changes in an area, much less be given the opportunity to provide feedback and comment. This seems to be a systemic problem and is only worse for the average resident who is often very busy."
> *— anon_ce99b4202e*

> "Just want our city officials to know that this community appreciates more transparency and inclusivity when it comes to decisions that shape our shared public resources."
> *— anon_64080c2998*

### For completing the courts

> "Thank goodness for the petanque club. It provides outdoor fun social connection for all ages. For senior citizens, it is a lifesaver for many. For college students, it can also be a break from social media and a face-to-face social connection. Kids can play. Everyone is welcome."
> *— anon_804fd3231b*

> "I think the courts are a fun unique use of the space. People use them, no question. The notice and comment period were not well handled by the city and you all could do better next time. But go ahead and finish the courts."
> *— anon_950e473e3a*

> "The earth movers took folks by surprise. The subsequent opposition to the Pétanque expansion is out of proportion to the lapse in communication that occurred."
> *— anon_93bbfdd8d7*

> "I feel it's unfairly punitive to the petanque community to pause/reverse construction on the new courts they'd worked to get approval on. Let construction continue, and redirect energy to pushing for more transparency from the city and more community involvement in future plans/decisions."
> *— anon_93aa64d1be*

### For pausing, reversing, or redirecting

> "I am happy that the pétanque players have courts in Church Hill. But I walk by the park almost daily, sometimes more than once a day, and while I rarely see the existing pétanque courts in use, there are always kids on the playground."
> *— anon_fae8ee84c6*

> "The Chimborazo Playground should serve the needs of the community around it. It's great that the pétanque group has been established for many years, but they are a niche group and should not monopolize the recreation space and public funds."
> *— anon_4d00c148d9*

> "This project should not move forward unless and until robust community feedback is sought, analyzed, and made public. From my perspective, additional Pétanque courts are not the highest priority need. All park users would benefit from functioning bathroom facilities and water access."
> *— anon_8683805c63*

> "It's so difficult to find a playground that caters to the younger toddlers and preschoolers. Chimbo playground is the only one on the hill that does this well. I want the petanque club to get their roses too, but [restroom and shelter] features would benefit EVERYONE who uses the park."
> *— anon_687a963f92*

### Looking forward

> "It is likely easier to tackle this if the petanque players can be transformed into allies rather than enemies, especially since they obviously already have ins with the City. This could be an opportunity to get much larger investments in Chimborazo if there's room in negotiations to say, 'This happened, but moving forward: here's our priorities for the most critical improvements.'"
> *— anon_ce99b4202e*

> "Continuing with the approved construction for the pétanque courts does not mean other improvements can not or will not happen. Several of the folks involved with the pétanque courts have also worked to make upgrades to the playground and will continue to advocate for a public park that benefits everyone."
> *— anon_cad71b092c*

> "When the City makes it easier for neighbors to participate in improving a park, they can make it easier for volunteers to feel inspired by the park's future and help out where they can. We can all do a little something to make this park a better place... so long as we're on the same page about what that 'better place' should look like?"
> *— anon_b5187c4bba*

## How the data is structured

`data/priorities-responses.csv` has one row per raw submission with these
columns:

- `Timestamp` — when the response was submitted (dd/mm/yyyy HH:MM:SS).
- `respondent_id` — `"anon_" + sha256(lowercased_email)[:10]`. Stable across both CSVs, so the same person gets the same ID in the survey and the petition file.
- Q1: *What do you want to say to Council Member Newbille and Director Frelke?* (free text)
- Q2: *How would you like the situation resolved now that construction is paused?* (one of six radio options, or write-in "Other")
- Q3: *What are your priorities for park improvements going forward?* (pick up to three)
- Q4: *Anything else you want the City or neighbors to know?* (free text)

## Reproducing the numbers

```bash
python code_survey.py
python code_survey.py --dump-q2   # print every Q2 response with its assigned code
```

The script dedupes by `respondent_id` (six respondents submitted more than
once; latest non-blank answer per respondent wins), codes each Q2 response
into one of fifteen documented buckets via a fixed list of substring rules,
tags Q3 by exact match against the standard option strings, and tags Q1/Q4
themes by lowercased keyword match. Every rule is editable in one place.

## Contact

communityforchimboplayground@gmail.com
