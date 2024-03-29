# Guidelines for the annotation of BREXIT tweets
- in general, we only annotate *clear* positives that don't need additional inference steps
- every slot has to be realised; any exceptions are given in the specifications for respective patterns
  + as a general exception, ENTITY slots that are not present because of syntactic ellipsis count as filled iff the entity can safely be assumed to be the author of the tweet
- we *do* annotate patterns embedded within questions, negations, relative phrases etc. as positives

# 0 Quotation #
- **ENTITY** says **FORMULA**
- according to **ENTITY**: **FORMULA**

## examples ##
- **I** told you **that this is important**
- **the #UN** says that **most of them are NOT ' refugees ' at all**
- **Donald Trump is coming to the UK on June 25th** according to this **New York Times** story
- **Man** yelled '**Britain first!**'

## counterexamples ##
- URLs: Cameron confirmed on Monday that [URL]
- We talked about this in depth
  + indicates conversation and broad topic, but not what was said about it by whom
- a key Brexit supporter claims that ...
  + the entity is not specific enough

## confusions ##
- #10: I'm like "… blurb …"

# 2 Causal Implication #
- if **FORMULA0**, then **FORMULA1**
- **FORMULA0** would cause **FORMULA1**
- **FORMULA0** is the reason for **FORMULA1**
- counterfactual reasoning
- frequently reasoning about consequences of past events or future results of things
- speculations
- premise sufficient
- often in combination with #5
- basically any implication where there is a reason (not necessarily given) why truth of the antecedent (**FORMULA1**) is causing and not just correlating with truth of the consequent (**FORMULA2**)

## examples ##
- **brexit** and **we'll have a great relationship with the US**
- **Zach's relentless negative campaigning** brought out the **London vote**
- **Brits will never control our country again** if **we vote IN**

## counterexamples ##
- if ever you needed confirmation for Brexit, these three provide it
  + no causal relationship
  
## specifications ##
- #23 + causal relationship

# 3 Desire #
- **ENTITY** wants **FORMULA**
- **FORMULA** cannot be just an **ENTITY**:
  + "**ENTITY** backs **cameron**" != "**ENTITY** desires **cameron**"
- the entity should be explicitly marked
- an exception applies for ellipses (i.e. when the subject is not realised in the surface form)
  + here, the entity is the author of the message

## cues ##
- verbs of desire (*want*, *wish*) of a particular outcome or event
- verbs of affiliation (*support*, *back*, *say yes to*)

## examples ##
- ... says **The Times**, endorsing **Brexit**
- **George** is for **Brexit**
- Hoping for **a successful outcome**
- **I** am interested in **participating**
- **We** are really looking forward to **this**
- **they** endorse **Brexit**

## counterexamples ##
- silent majority for brexit
  + entity is undefined subset
- the pro brexit campaigners are using this strategy
  + desire defines membership
- a person supporting brexit / many people supporting brexit say ... 
  + not specified who the entities are
- he is *against* it
  + #55
- SF have issues with EU but *see it as better* for NI to remain
  + one-sided preference without explicit marking of desire
  + here: because they might not actually want to remain, despite seeing this as the rationally best decision
- democracy should be protected
  + #4
  + the 'wanter' is implicit in a non-elliptical sentence
- he *voted* remain 
  + might be interpreted as him wanting *remain* to be made true, but we do not consider such actions a sufficiently clear expression of desire
  + the desire can only be inferred from an action
- it would be nice if ..
- ... the figures were REMAIN 45% ...
  + figures do not desire anything
- you want to talk misleading?
  + rhetorical questions and idiomatic expressions
- he's got Brexit as his next agenda item
- Johnson's *reason* to remain, her *case* for leave
  + the desire can only be inferred from an expression of conscious decision or reasoning
- you seem to like that
  + positive regard without desire
- the technocrats in the EU fighting for Britain to remain
  + effort does not necessarily equal desire
- I believe in votes at 16 and no GRP for transgender people
- I'm endorsing my point from yesterday 
  + the point is being reinforced, not desired

# 4 Ought #
- ... should / ought ...
- imperatives
- situational oughts (entity should win ...)

## examples ##
- give him enough robe
- @jajyjay1 should be sent straight back and boats destroyed
- we need more fire in our bellies
- our money should all be mini union flags
- it is important to brexit
- entity should win the medal

## counterexamples ##
- entity should practice harder

## confusions ##
- #3

# 5 Possibility #
- ... could / would ...

## examples ##
- **he** could well **be the leader of the country**
- **#indyref2** could **change that**
- **any one of them** potentially **an EU voter for in**

## confusions ##
- #11
- #36

# 6 Bad for Concept #
- **FORMULA** is / would be bad for **CONCEPT**
- **CONCEPT** can be an entity (e.g. person) or system (e.g. economy, environment)

## examples ##
- I'm not saying **it** would break **us** but *pain* would be at least medium term not short
- #RemainCosThePoorAreGonnaBeHitTheHardest
- **pensionists** stand to *lose* from **Brexit**
- **Brexit** may seem like the **West's** biggest *problem*
- **Brexit** is *bad* for **us**

## counterexamples ##
- Johnson is a bad person
  + #21
- if we Brexit, the rest of the world will view us as racist, bigoted and narrow- minded
  + too implicit — while being viewed as racist etc. is a bad thing, the speaker has not stated that they care what people think
- @UKIP can take votes from Labour 
  + too implicit — taking votes is damaging according to world knowledge, but taking something away is not unambiguously bad
- its illegal immigrants that are entering through the EU on false documents or nothing at all that worries me.
  + being worried is unpleasant, but not necessarily damaging

# 8 Good for Concept #
- **FORMULA** is / would be good for **CONCEPT**
- **CONCEPT** can be entity (e.g. person) or system (e.g. economy, environment)

## examples ##
- the **UK** will be *better of* **out of the EU**
- **Brexit** might have a *positive effect* on **the EU**
- **Brexit** will only *improve* things for **the minority**
- **I** am ... *enjoying* **following your comments on brexit**
- **vote #remain** to keep **Greece** *safe*!

## counterexamples ##
- Johnson is a good person
- @Nissan is the biggest private sector employer in the North East - massive investor in Britain, job + car creator
  + too implicit — investing / employing not inherently positive

# 10 Belief #
- **ENTITY** believes / thinks that **FORMULA** is true
- **ENTITY** is sure that **FORMULA** is true
- Can be difficult to separate from knowledge (#34) based on cue words

## examples ##
- **I** don't think **people realise the severity of the consequences of voting to leave**
- **I** believe **they will**
- **i** agree **the sooner we leave the better**
- **I** believe in **votes at 16 and no GRP for transgender people**
  + (= I believe this ought to be made true)
- **I** think **this could work**

## counterexamples ##
- I agree with her about Brexit
  + there is reference to belief here, but it is unclear who believes what; we only learn that 'I' and 'her' believe different things w.r.t. Brexit
- I'm thinking of a solution
  + thinking as a general cognitive process vs. thinking as belief

## confusions ##
- #0
- #34: I know it's bad

# 11 Option #
- **ENTITY** can / is able to **ACTION**

## examples ##
- **we** could **lend you Gisela Stuart** if you like
- if we get out **we** can **decide**
- why would **we** no longer be able to **sell them**

## counterexamples ##
- the sheep can move to Islamabad and take their €€with them
  + hidden imperative
- Remain can't see it
  + they may be able to see it, but they don't want to

## confusions ##
- #36

# 12 Default Implication #
- if **FORMULA0**, then usually **FORMULA1**

## examples ##
- **" Every establishment figure " wanting you to vote for something** isn't usually a reason to **jump to it**
- when **people say this**, **they are usually right**

## confusions ##
- #23: when people say this, they are right

# 15 Similarity #
- **CONCEPT0** equals **CONCEPT1**

## examples ##
- **BREXIT**=**fREEDOM**
- **Brexit** equals **anxiety attack**
- **Boris Johnson**, another **Nigel Farage**
- **#EUref** feels similar to **Scottish Referendum**

## counterexamples ##
- there is a link between Brexit and mental illness
  + correlation

# 16 Expressed Better #
- **ENTITY** prefers **FORMULA0** over **FORMULA1**
- like in #3, the **ENTITY** can be left out by ellipsis

## examples ##
- **a lot fo tories** would gladly **trade Scotland** for **Brexit**
- it 's all **coulds and not woulds** , il take my chance with **coulds and brexit**
- we go for **quality** rather than **quantity**

## counterexamples ##
- direct democracy is better than representative democracy
  + "pure" evaluative comparison that does not indicate an **ENTITY**'s necessary desire for either **FORMULA**
  + #42
- I prefer brexit
  + one of the options is implicit
  + #3
- general preferability of a concept over another without ascribing the preference to any entity:
  + *It is better to leave than to remain*: user who posted the tweet prefers leaving over remaining
- he was leave, but has *switched* to remain
  + preference can only be inferred
  + "was leave" is treated as group membership (#24)
- it should be real ale, not some gassy lager
  + missing **ENTITY**; no explicit preference

## confusions ##
- #3: see above
- #43: Brexit would be better for the young folks than staying in the EU

# 19 Entity's Obligation #
- **ENTITY** should / has to **FORMULA**

## examples ##
- DAVE **YOU** SHOULD ALSO **" QUIT "**
- **you** should **get a job there**
- **the UK** should **stay in the EU**
- @nickhillman **You** have to **read the article**.

## confusions ##
- #3: John wants Trump to resign
- #4: A should win the medal

## specifications ##
- #3 + do-modality
- #4 + **ENTITY** who should make the **FORMULA** true

# 20 Lying #
- **ENTITY** lies about **FORMULA**
- **ENTITY** says **FORMULA** but believes **FORMULA** is not true
- an **ENTITY** is claimed to be lying (by the author of the text or someone referred to in the text) about a topic or the truth of a **FORMULA**; the lie can be about:
  + a topic (*And believe* **this man** *who told lies* **about Iraq**)
  + a particular claim (*For anyone who still believes the enduring* **Brexit** *lie* **that the EU is undemocratic**)
  + a claim that is not elaborated upon in the given message, but clearly concerns a particular lie (*@JunckerEU says* **Boris** **making up stories**)

## examples ##
- this lie that **young people can't travel**, it's another **stay** lie
- **David Cameron and George Osborne’s** ‘ lies ’ over **Brexit warnings**
- **@BBCr4today** running as its top story a **Brexit** lie

## counterexamples ##
- the **ENTITY** is accused of being generally dishonest, without specification of what they were lying about
- the **ENTITY** is accused of being unsincere in some other way, e.g. hypocritical, scaremongering...
- X is talking BS
  + the **ENTITY** is accused of saying something that is untrue — it has to be clear from the context that they are *deliberately* saying something incorrect

## confusions ##
- #21: more bullshit from the in camp , next they'll be claiming that Brexit ' could ' cause Mars to crash in to Venus lol

## specifications ##
- #21 + special accusation

# 21 Ad Hominem #
- **ENTITY** is (morally) bad

## examples ##
- **he** 's been paid off by Brussels to keep us in
- **#UK/#EU #PowerElite** manipulating/misleading #PublicOpinion on #EURef
- **Remain** puppets
- more bullshit from **the in camp** , next they'll be claiming that Brexit ' could ' cause Mars to crash in to Venus lol

## counterexamples ##
- cunt.
  + only disqualifying accusations are ad hominem

# 22 Necessary Condition #
- **FORMULA0** is necessary for **FORMULA1**
- **FORMULA1** cannot be done without **FORMULA0**

## examples ##
- **that** can only be the case if **Irish border is closed**
- **EU membership** the only possible way to **promote free trade over the long term**
- we need **brexit** to **stop unelected buffons interfering with our laws**

## confusions ##
- #35

# 23 Implication #
- if **FORMULA0**, then **FORMULA1**

## examples ##
- if ever **you needed confirmation for brexit**, **these three provide it**
- if **I was leaning towards BREXIT** , **their campaign being ran by Farage , Boris & The Sun will give me 2nd thoughts**

## counterexamples ##
- if you needed a list what happens if we brexit, it's simple: prices will rise

## confusions ##
- #2: here no causal implication (in dubio #2)

# 24 Membership #
- **ENTITY** is part of **ENTITY GROUP**
- for this pattern, the **ENTITY** has to have agency (e.g. people, organisations or states, but not abstract entities, objects or ideas)
- groups are defined widely, with prototypical cases including e.g. professions, parties/organisations or nationalities
- formal distinction at the blurry line between group and attribute: when in doubt, an adjective does not designate a group even if the corresponding noun does ("**she**'s **a German**": yes, "she's German": no)
- we also annotate ad hoc groups (cf. first example)
- #24 only covers statements about group memberships that go beyond purely characterising the entity. I.e. examples will often involve an entity and a verb phrase (e.g. "**A** is a member of **B**") or a genitive construction ("**XY**'s membership in **Z**"). Group statements that only specify the entity's background (e.g. via a modifying noun phrase) are annotated as #57.

## examples ##
- **The clintons** are **fat cats** who are owned by the multinationals
- **Jo** was **a politician**
- three parties that want to be in the EU but not in the UK
- **he's** **a leaver**
- "**Stuart Rose** has switched sides to **#Leave"**
- "**Brits** are too much **cowards** to vote" (24 + 25)
- **we're** on the side of **leave**
- **Scotland** should remain in **EU**
- **we** are all **stupid people**

## counterexamples ##
- Turkey's largely Muslim population
- the president is British
- he supports leave
  + #3
- a billionaire brexit supporter
  + **ENTITY** not specified
- They will stay in the EU
  + *stay* technically implies an existing membership, but in this case is read as an action rather than membership
- The UK will leave the EU
  + leaving = action resulting in end of membership rather than membership per se
- She joined the group
  + joining = action rather than membership
- we are all stupid
  + property rather than group definition
- Brexit will help other EU slave nations
  + group specification, but missing entity
- It is an unfortunate coincidence that this happened
  + **ENTITY** "it" has no agency
- the EU slave nations Germany and France
  + #57
- star economist Thomas Pickety
  + #57
- The Times' Jane Smith
  + #57

# 25 Universal Quantification [!] #
- **ENTITY** is / does something

## examples ##
- **The borg** don't **negotiate**
- **UKIP** are **a one trick pony**
- **we all** **love and support each other**

## counterexamples ##
- I don't like this at all

# 26 Position to Know #
- **ENTITY** is part of **ENTITY GROUP** that is qualified to know **FORMULA**

## examples ##
- **we** **European** knows **it** and see our culture disappearing

## counterexamples ##
- as an immigrant , son of immigrants and having been subject to racsim I am firmly for Brexit

# 27 Negation [!] #

## examples ##
- this is **false** / this is **not** true.
- **no**.
- most of them are **NOT** ' refugees ' at all

# 30 Action Execution #
- **ENTITY** has done **ACTION**

## examples ##
- **i**'ve **voted brexit**
- **Ted Heath** **promised our sovereinty is safe**
- **EU** **secured employment rights** on a number of occasions
- **someone** actually **done that**

## counterexamples ##
- I've been in Africa since 1980
  + stative verbs

# 32 Weak Universal Quantification [!] #

## examples ##
- **almost all its Units** were **renamed after Continental European scientists**
- **most of them** are **NOT ' refugees ' at all**

# 34 Knowledge #
- **ENTITY** knows **FORMULA** is true
- Knowledge is considered from the entity's point of view; i.e. regardless of whether **FORMULA** is *actually* true 

## examples ##
- **I** know that **Nigel Farage didn't murder that MP**
- Even **this Norwegian minister** knows that **this would not be good for UK**
- **The pro-EU campaign** knows that **people don't trust Dodgy Dave**
- **You** know **you're in** when Warren Buffet starts selling cherry coke
- **I**'m certain **it will break up or change dramatically**
- **The president** understands that **this is true**

## counterexamples ##
- You know, this was really a stupid idea
  + 'you know' as a discourse marker
- Cameron should know about Brexit
  + knowing about a *topic* != knowing the *truth* of a particular statement

## confusions ##
- #10: belief

# 35 Necessary Truth #
- **FORMULA** will always be the case

## examples ##
- Europe will always be there
- great ideas will always be funded

## confusions ##
- #22

# 36 Permission #

## examples ##
- I have the right to vote
- it's ok for the INs

# 37 Quotation of Entity's Obligation #

## examples ##
- **Billionaire Brexit supporter** says **UK** should **emulate Singapore**
- **Cypriot expat organization** in #UK calls on **its members** to **vote #Remain**

## specifications ##
- #19 + #0 + #25

# 38 Warning #
- **ENTITY** warns of **FORMULA** being generally bad (i.e. not just bad for any particular entity or group)
- the warning can be encoded in the speech act (e.g. warning), or in the quoted speech itself (e.g. saying that something would be terrible)
- this pattern differs from warnings of bad consequences (#41/49 depending on whether consequences are bad for some or in general)
- expressions not relating directly to damage/danger but to changes in size/amount are not considered here, but understood as (negative) consequences

## examples ##
- **Boris Johnson as PM** would be ‘ horror scenario , ’ warns **top Juncker aide**
- **Cameron** warns against **Brexit** in patriotic speech
- **Scientists** including Stephen Hawking say **a vote for Brexit in this month's EU referendum** would be a disaster

## counterexamples ##
- the IMF said that brexit will prolong austerity
  + neither the verb nor formula 1 have an unambiguously negative evaluation (e.g. austerity may be negative for many people, but not necessarily for everyone)
- Hilary Benn has warned that Britain 's exit from the EU would make the country ' poorer ' and ' less influential'
  + #49: bad consequences for some
- He predicted that Brexit would cause the pound to fall 
  + #41: bad consequences — decrease in value vs. explicit damage
- She has threatened to vote out 
  + threats are not considered general warnings

# 39 Some [!] #

## specifications ##
- #32 + #27

# 40 Nobody [!] #

## specifications ##
- #25 + #27

# 41 Warning of Bad Consequences #
- **ENTITY** says that **FORMULA0** will / would lead to bad **FORMULA1**
- indirect version of #38 where something is claimed to be bad by consequence
- bad consequences include changes in size/amount etc. that are considered bad by general consensus

## examples ##
- **Richard Haass**' claim that **Brexit** could 'trigger **NI violence**'
- **Experts** warn that **brexit** could cause the **pound to fall**

## counterexamples ##
- Brexit has brought out the bigots and racists
  + is matched by the logical formula = something has bad consequences, but is not a warning of bad consequences because warnings don't make sense for things that have already happened 

# 42 Better #
- **FORMULA0** is universally (=for all) better than **FORMULA1**

## examples ##
- **Brexit** is still better than **being in the EU**
- **We** are better than **this**

## counterexamples ##
- is there anything worse than a missed flight
  + pragmatically: #45
- it should be real ale, not some gassy lager
  + too implicit
- your guess is as good as mine
  + idiom = 'I don't know'
- Brexit -carefully managed by cool headed diplomats - cd be better but Remain can't see it
  + missing FORMULA2

# 43 Better for Concept #
- **FORMULA0** is better for **CONCEPT** than **FORMULA1**
- concept = entity / system

## examples ##
- **Brexit** would be better for **the young folks** than **staying in the EU**
- **fishermen** would profit more from **relaxed restrictions** than **worker right protection in the EU**
- **higher CO2 costs** would be more effective for **climate protection** than **general speed limits**

## counterexamples ##
- I see IndyScot as a chance to improve for the majority
  + #8
- 40+ years ago this country was in a poor state, we're nowhere near as bad now.
  + not clear enough what exactly was/ is better
-  Brexit might have a positive effect on the EU: discontents exit, resulting in a closer-knit and better-functioning EU-eurozone."
  + missing **FORMULA1**
- I feel ashamed of our Gov. Worse to have others feel sorry for us

# 44 Good #
- **FORMULA** is universally good (i.e. the scope is not explicitly limited to specific entities)

## examples ##
- **nation states** are good
- so the ideal will be **Indy in EU with rUK still a member**

## counterexamples ##
- Democracy is also often taken for granted

# 45 Bad #
- **FORMULA** is universally bad (i.e. the scope is not explicitly limited to specific entities)
- it is enough for the **FORMULA** to be bad in only some aspects, regardless of whether it has positive characteristics as well
- expressions not relating directly to damage/danger but to changes in size/amount are not considered here, but understood as (negative) consequences

## examples ##
- **nation states** are evil
- **Boris** is the worst prime minister ever
- the problem is that **he never complied**
- **the system** is flawed 
  + (= the system is bad, at least in some ways)
- **Leave's arguments** just don't add up.

## counterexamples ##
- the #UN - a unit of the globalist conspiracy
  + #21
- its illegal immigrants that are entering through the EU on false documents or nothing at all that worries me.
  + no explicit universal evaluation
- I feel that if we Brexit, the rest of the world will view us as racist, bigoted and narrow-minded"
- Bigoted bloody bunch
  + #21 because this is a negative evaluation of somebody's character rather than e.g. their overall 'suitability' as in the prime minister example

## problematic ##
- so what exactly is wrong with an EU army

# 46 Qualified Desire #
- **ENTITY** is part of **ENTITY GROUP** that desires **FORMULA**

## examples ##
- **as a son of immigrants** **I** am for **Brexit**
- **the Left T.U. in me** says **No to leave** but **the #Motorbikes side of me** says **Yes vote to leave**

# 48 Warning Some #
- **ENTITY** says that **FORMULA** is / will be / would be bad for **CONCEPT**

## examples ##
- Correspondents: **Brexit** will batter **the comedy industry**, says **Stephen Grant**
- **Brexit** would hit **poor** hardest, says **David Cameron**
- **She** points out that **Brexit** endangers **pensions**

# 49 Warning of Bad Consequences for Some #
- **ENTITY** says that **FORMULA0**  will / would lead to **FORMULA1** which would be bad for **CONCEPT**

## examples ##
- **Hilary Benn** has warned that **Britain 's exit from the EU** would make the **country** **' poorer ' and ' less influential'**
- **Brexit** could lead to **downgrades** for **other EU countries** -**Fitch**

# 53 Intention to Do #
- **ENTITY** intends to do **ACTION**
- usually, statements expressing a future action without referencing intentions, plans etc. are interpreted as intention iff subject = author:
  + "**I** will do **ACTION**" = #53 (intention)
  + "**She** will do **ACTION**" != #53 (prediction)
  + exception: "**He** will do **ACTION0** (in order) to do **ACTION1** -> **ACTION0** = prediction, but **ACTION1** = intention

## examples ##
- **1000 officials** travel to Strasbourg monthly to **vote** at a cost of €130m per annum
- **French** to **brick up channel tunnel** in event of #BREXIT!
  + read as: are set / committed to brick up the tunnel
- **Stuart Rose** has probably switched sides to #Leave but agreed to stay quite to **save his blushes**
- **I**'m **voting #Remain** with reservations, but pensioners stand to lose from #Brexit
- Why does Brexit say "that's rubbish" and "**we'll** **negotiate to keep**" every time @LabourRemain point out something we'll lose
- **Rich Audi drivers**, will **stay to avoid losing their 'richness'** 
  + this is not just a future prediction because it contains a reason why they will stay
- $DIA You know **Warren Buffet** will drink his daily Cherry $KO and pull out his shopping bag to **buy buy buy** following the Brexit vote. $SPY
  + drink his daily Cherry $KO: prediction; pull out his shopping bag to buy: intention to do
- "It's **this damn Brexit** tryin'a **lure us into an ambush**"
- Why do you think **Trump** chose to **visit UK day after the referendum**?
  + chose to -> deliberate action

## counterexamples ##
- things will go up in price EVERYTHING WILL COST MORE!
  + "EVERYTHING" has no agency and can't intend to do anything
- But Trump is no mug &amp; he will trade with the UK despite Cameron
  + prediction
- Brexit vote set to fuel more referendums 
  + prediction statement + no agency
- We're holding an English referendum next to decide whether we'll allow Scotland to stay 
  + exception to the speaker + future construction -> intention rule: here, 'we' is understood as the government, i.e. the speaker presumably has no agency in what is happening, so the statement does not reflect their intention

# 55 Opposition #
- **ENTITY** opposes the truth of **CONCEPT**
- Opposition is understood as the counterpart to desire (#3): **ENTITY** wants the negation of **CONCEPT** to be true
  + NB: this is different from negated desire (#3): "**They** don't want **a Brexit**" != "**They** are *(actively)* against **a Brexit**"

## examples ##
- **Junker** says no to **reform**. Germany say no tarrifs. #Brexit
- @bbclaurak to be fair if **the Almighty** came out against **#Brexit**, Leavers would say his ubiquity prevents him taking a national view. #Remain
- **Roxy** against **Brexit** watching the news nervously #DogsAgainstBrexit https://t.co/BrSp35RlnT

## counterexamples ##
- She doesn't want to come along
  + negated #3
- They voted against Brexit
  + voting = action -> opposition too implicit
- SCOTUS blocked the policy
  + banning = action (see above)

# 57 Concept Refinement #
- **ENTITY** is part of **ENTITY GROUP**, but this is not the claim of the overall statement
- this pattern will typically apply to cases where the group membership is expressed via a modifying noun phrase
- in contrast to #24 there will usually be no verb phrase expressing membership; instead membership is considered background information on **ENTITY**

## examples ##
- the **EU slave nations** **Germany and France**
- **star economist** **Thomas Pickety**
- **The Times'** **Jane Smith** 
- **Billionaire Brexit supporter** **Max Doe** 
- **#JoeCox** **MP**

## counterexamples ##
- Germany and France are slave nations
  + #24
- Thomas Pickety is one of the top economists
  + #24
- this ist a statement from Lord Ashton
  + titles are no refinements
- Andrew Neil is chair of @spectator
  + entity has a specific role, their membership is not the foregrounded statement

# 58 Desirer #
- group of entities desiring **FORMULA** to be true
- typical realisations: nouns tied to desire and relative phrases
- no need for a specific entity

## examples ##
- Trump is a **Brexit** supporter
  + #24 + #58
- **Stay** fans are right
- People who want **Brexit** keep saying that
- I'm **Brexit**/**Brexin**/**remain**/**leave**

## counterexamples ##
- Trump supports Brexit
  + #3
- I want to stay
  + #3
- Cameron supporter
  + we can't extract any meaningful information from this because we would need too much background knowledge

# 59 Believer #
- group of entities believing **FORMULA** to be true
- typical realisations: nouns tied to belief and relative phrases
- no need for a specific entity

## examples ##
- anyone who truly believes **that this is possible**

## counterexamples ##
- I believe this is possible
  + #10


# Categories #
- entities vs entity groups
- binders / operators / junctors
- necessary truth

## Binders ##
- 25, 27, 32, 39, 40

## Evaluation ##
- 3, 6, 8, 16, 42, 43, 44, 45, 46

## Implication ##
- 2, 12, 22, 23, 35

## Quotation ##
- 0, 3, 10, 16, 34

## Entities ##
- 19, 20, 21

<!-- # Inverse Lookup # -->
<!-- ![](https://mermaid.ink/svg/eyJjb2RlIjoiZ3JhcGggVERcbiAgICBGe0Zvcm11bGFlfSBcbiAgICBGIC0tPiBPbmVcbiAgICBGIC0tPiBUd29cbiAgICBPbmUgLS0-IE8oNDogT2JsaWdhdGlvbilcbiAgICBPbmUgLS0-IFAoMzY6IFBlcm1pc3Npb24pXG4gICAgT25lIC0tPiBEaWEoNTogUG9zc2liaWxpdHkpXG4gICAgT25lIC0tPiBCb3goMzU6IFVuaXZlcnNhbCBGYWN0cylcbiAgICBUd28gLS0-IEltcGwoMjM6IEltcGxpY2F0aW9uKVxuICAgIEltcGwgLS0-IENhdXMoMjogQ2F1c2F0aW9uKVxuICAgIEltcGwgLS0-IERlZigxMjogVXN1YWxseSBpbXBsaWVzKVxuICAgIE9uZSAtLT4gTmVnKDI3OiBOZWdhdGlvbilcbiAgICBDYXVzIC0tPiBOZWMoMjI6IE5lY2Vzc2FyeSBjb25kaXRpb24pXG5cbiAgICBUd28gLS0-IFNpbSgxNTogU2ltaWxhcml0eSlcbiAgICBFIC0tPiBTaW1cblxuICAgIEV7RW50aXRpZXN9XG5cbiAgICBGIC0tPiBMKDA6IExvY3V0aW9ucylcbiAgICBFIC0tPiBMXG4gICAgTCAtLT4gRCgzOiBEZXNpcmUgZXhwcmVzc2lvbilcbiAgICBMIC0tPiBiYWQoNjogQmFkbmVzcyBzdGF0ZW1lbnQpXG4gICAgYmFkIC0tPiBiYWRjb25zKDQxOiBCYWQgY29uc2VxdWVuY2VzIHN0YXRlbWVudClcbiAgICBDYXVzIC0tPiBiYWRjb25zXG4gICAgTCAtLT4gZ29vZCg4OiBHb29kbmVzcyBzdGF0ZW1lbnQpXG5cbiAgICBGIC0tPiBFRFtFcGlzdGVtaWMvRG94YXN0aWNdXG4gICAgRSAtLT4gRURcbiAgICBFRCAtLT4gQigxMDogQmVsaWVmKVxuICAgIEVEIC0tPiBLKDM0OiBLbm93bGVkZ2UpXG4gICAgTCAtLT4gUHJlZigxNjogUHJlZmVyZW5jZSBzdGF0ZW1lbnQpXG4gICAgTCAtLT4gUENhdXNlKDMzOiBQb3NzaWJsZSBjYXVzYXRpb24gc3RhdGVtZW50KVxuICAgIERpYSAtLT4gUENhdXNlXG4gICAgQ2F1cyAtLT4gUENhdXNlXG4gICAgRSAtLT4gR1tHcm91cHNdXG4gICAgRyAtLT4gSW4oMjQ6IFggaW4gZ3JvdXAgWSlcbiAgICBHIC0tPiBNZW1iZXJzXG4gICAgTWVtYmVycyAtLT4gQWxsKDI1OiBBbGwgbWVtYmVycyBoYXZlIHByb3BlcnR5KVxuICAgIEFsbCAtLT4gQWxsT2JsaWdhdGVkKDM3OiBBbGwgbWVtYmVycyBoYXZlIG9ibGlnYXRpb24gdG8uLi4pXG4gICAgT0QgLS0-IEFsbE9ibGlnYXRlZFxuICAgIEFsbCAtLT4gQWxsS25vdygyNjogQWxsIG1lbWJlcnMgaW5jbHVkaW5nIFgga25vdylcbiAgICBBbGwgLS0-IE1vc3QoMzI6IE1vc3QgbWVtYmVycyBoYXZlIHByb3BlcnR5KVxuICAgIEwgLS0-IEhvbmVzdHkoMjg6IFggaXMgaG9uZXN0IGFib3V0IFkpXG4gICAgTWVtYmVycyAtLT4gU29tZSgzOTogU29tZSBtZW1iZXJzIGhhdmUgcHJvcGVydHkpXG4gICAgTWVtYmVycyAtLT4gTm8oNDA6IE5vIG1lbWJlcnMgaGF2ZSBwcm9wZXJ0eSlcbiAgICBFIC0tPiBBdHRhY2tzXG4gICAgQXR0YWNrcyAtLT4gQWQoMjE6IEFkIEhvbWluZW0gY2F0Y2hhbGwpXG4gICAgQXR0YWNrcyAtLT4gTGkoMjA6IEVudGl0eSBsaWVzIGFib3V0IFgpXG4gICAgTyAtLT4gT0QoMTk6IFggaGFzIE9ibGlnYXRpb24pXG5cbiAgICBBe0FjdGlvbnN9XG5cbiAgICBFIC0tPiBBYmlsaXR5KDExOiBBYmlsaXR5KVxuICAgIEEgLS0-IEFiaWxpdHlcbiAgICBFIC0tPiBEaWQoMzA6IFggZGlkIFkpXG4gICAgQSAtLT4gRGlkXG5cbiAgICBPbmUgLS0-IFJlc3VsdCgyOTogRG9pbmcgWCB3b3VsZCBldmVudHVhbGx5IHJlc3VsdCBpbiBZKVxuICAgIEEgLS0-IFJlc3VsdFxuICAgIFJlc3VsdCAtLT4gU3RyZW5ndGgoMzE6IFBvd2VyIHRvIGVuZm9yY2UgWCkiLCJtZXJtYWlkIjp7InRoZW1lIjoiZGVmYXVsdCJ9LCJ1cGRhdGVFZGl0b3IiOmZhbHNlfQ) -->
<!-- ```mermaid -->
<!-- graph TD -->
<!--     F{Formulae}  -->
<!--     F -\-> One -->
<!--     F -\-> Two -->
<!--     One -\-> O(4: Obligation) -->
<!--     One -\-> P(36: Permission) -->
<!--     One -\-> Dia(5: Possibility) -->
<!--     One -\-> Box(35: Universal Facts) -->
<!--     Two -\-> Impl(23: Implication) -->
<!--     Impl -\-> Caus(2: Causation) -->
<!--     Impl -\-> Def(12: Usually implies) -->
<!--     One -\-> Neg(27: Negation) -->
<!--     Caus -\-> Nec(22: Necessary condition) -->

<!--     Two -\-> Sim(15: Similarity) -->
<!--     E -\-> Sim -->

<!--     E{Entities} -->

<!--     F -\-> L(0: Locutions) -->
<!--     E -\-> L -->
<!--     L -\-> D(3: Desire expression) -->
<!--     L -\-> bad(6: Badness statement) -->
<!--     bad -\-> badcons(41: Bad consequences statement) -->
<!--     Caus -\-> badcons -->
<!--     L -\-> good(8: Goodness statement) -->

<!--     F -\-> ED[Epistemic/Doxastic] -->
<!--     E -\-> ED -->
<!--     ED -\-> B(10: Belief) -->
<!--     ED -\-> K(34: Knowledge) -->
<!--     L -\-> Pref(16: Preference statement) -->
<!--     L -\-> PCause(33: Possible causation statement) -->
<!--     Dia -\-> PCause -->
<!--     Caus -\-> PCause -->
<!--     E -\-> G[Groups] -->
<!--     G -\-> In(24: X in group Y) -->
<!--     G -\-> Members -->
<!--     Members -\-> All(25: All members have property) -->
<!--     All -\-> AllObligated(37: All members have obligation to...) -->
<!--     OD -\-> AllObligated -->
<!--     All -\-> AllKnow(26: All members including X know) -->
<!--     All -\-> Most(32: Most members have property) -->
<!--     L -\-> Honesty(28: X is honest about Y) -->
<!--     Members -\-> Some(39: Some members have property) -->
<!--     Members -\-> No(40: No members have property) -->
<!--     E -\-> Attacks -->
<!--     Attacks -\-> Ad(21: Ad Hominem catchall) -->
<!--     Attacks -\-> Li(20: Entity lies about X) -->
<!--     O -\-> OD(19: X has Obligation) -->

<!--     A{Actions} -->

<!--     E -\-> Ability(11: Ability) -->
<!--     A -\-> Ability -->
<!--     E -\-> Did(30: X did Y) -->
<!--     A -\-> Did -->

<!--     One -\-> Result(29: Doing X would eventually result in Y) -->
<!--     A -\-> Result -->
<!--     Result -\-> Strength(31: Power to enforce X) -->
<!-- ``` -->
