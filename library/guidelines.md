# schema
## name
short name (e.g. 'generic ad hominem', 'quotation')
## description
concise description
## formalization
the logical formula
## examples
list of positive examples
## counter-examples
list of examples with according pattern
## notes
list of further comments
# pattern 0
## examples
  - 'I told you'
## counter-examples:
  - URLs
  - 'sb. shouted "Britain First"' NOT p0 but normative statement (p3)
  - 'I'm like "… blurb …"' NOT p0 but belief (p10)
  - threats / warnings (p38)
## notes:
  - negations
  - nested quotations 
# pattern 2
## notes
  - counterfactual reasoning
  - frequently reasoning about past / future
  - speculations
  - premise sufficient
  - often in combination with p5
  - basically any implication where there is a reason (not necessarily given) why truth of the antecedent is causing and not just correlating with truth of the consequent

# pattern 3
## notes
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
## notes
  - refers to named points in time (e.g. during "WWII"
  - context-dependent variants (next Friday) may be annotated, but cannot be formalized

# pattern 15

# pattern 16
## notes
 - the entity can be left implicit if it is clear who made the statement (*It is better to leave than to remain*: user who posted the tweet prefers leaving over remaining)
 - a portion of the hits will overlap with pattern 3, as often statements that something should be realised go along with a preference of one outcome over another.
 - in addition, 'pure' preference statements that do not indicate a necessary desire for either formula (*direct democracy is better than representative democracy*)
 - pattern 16 is *not* assigned if:
   - one of the options is implicit (*I prefer brexit*)
   - the 'formula' part is realised by an entity reference (*I trust men who X, not men who Y*)
# pattern 23
## notes
  - no causal implication (in dubio pattern 2)
  - necessity

# pattern 20
## notes
  - the pattern matches instances where an entity is accused of lying about a topic or the truth of a proposition.
  - pattern 20 is *not* assigned if:
    - the entity is accused of being generally dishonest, without specification of what they were lying about
    - the entity is accused of being unsincere in some other way, e.g. hypocritical, scaremongering...
    - the entity is accused of saying something that is untrue -- it has to be clear from the context that they are deliberately saying something incorrect (e.g. *X is talking BS* is a negative example)

# pattern 38
## notes
  - the pattern matches instances of an entity 0 warning about formula 1 being bad.
  - negative connotations may be directly encoded in the verb, e.g. 'warn'
  - example: *Juncker warns about the outcome of Brexit*
  - alternatively, a more neutral communication verb (e.g. say) can be used if formula 1 is clearly inherently negative:
  - example: *He said that #brexit will wreck the job market*
- pattern 38 is *not* assigned if:
  - neither the verb nor formula 1 show an unambiguously negative evaluation (e.g. *the IMF said that brexit will prolong austerity*)
