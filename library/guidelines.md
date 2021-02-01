# schema
- name: short name (e.g. 'generic ad hominem', 'quotation')
- description: concise description
- formalization: the logical formula
- examples: list of positive examples
- counter-examples: list of examples with according pattern
- notes: list of further comments
# pattern 0
- examples:
  - 'I told you'
- counter-examples:
  - URLs
  - 'sb. shouted "Britain First"' NOT p0 but normative statement (p3)
  - 'I'm like "… blurb …"' NOT p0 but belief (p10)
  - threats / warnings (p38)
- notes:
  - negations
  - nested quotations 
# pattern 1
- notes:
  - causality
  - facts
# pattern 2
- notes:
  - counterfactual reasoning
  - frequently reasoning about past / future
  - speculations
  - premise sufficient
  - often in combination with p5
# pattern 3
-notes:
 - the pattern matches tweets that contain expressions of:
   - desire (*want*, *wish*) of a particular outcome or event,
   - affiliation (*support*, *back*),
   - conscious decision or reasoning (Johnson's *reason* to remain, her *case* for leave),
   - change in reasoning (he was leave, but has *switched* to remain)
 - the entity making the statement should be explicitly marked - an exception applies for ellipsis (i.e. when the subject is not realised in the surface form)
 - pattern 3 is **not** assigned if:
  - the 'wanter' is implicit in a non-elliptical sentence (*democracy should be protected* pattern 4)
  - the desire can only be inferred from a particular action taken by an entity (he *voted* remain might be interpreted as him /remain/ to be made true, but we do not consider such actions a sufficiently clear expression of desire)
  - somebody expresses desire towards an item etc.; where we would have to infer that what they actually want is to *obtain* the item
# pattern 13
- notes:
  - refers to named points in time (e.g. during "WWII"
  - context-dependent variants (next Friday) may be annotated, but cannot be formalized
# pattern 15

# pattern 16
- notes:
 - the entity can be left implicit if it is clear who made the statement (*It is better to leave than to remain*: user who posted the tweet prefers leaving over remaining)
 - a portion of the hits will overlap with pattern 3, as often statements that something should be realised go along with a preference of one outcome over another.
 - in addition, 'pure' preference statements that do not indicate a necessary desire for either formula (*direct democracy is better than representative democracy*)
 - pattern 16 is *not* assigned if:
  - one of the options is implicit (*I prefer brexit*)
  - the 'formula' part is realised by an entity reference (*I trust men who X, not men who Y*)
# pattern 23
- notes:
  - no causal implication (in dubio pattern 2)
  - necessity
# pattern 26
