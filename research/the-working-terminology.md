# "The working" — terminology evidence for SymEval

Research question: how do the two tools that most inspired SymEval (handcalcs and
CalcPad) describe the multi-part rendering of a calculation — the (1) symbolic form,
(2) substituted form, (3) result — and is **"the working"** (British "show your
working"; Dutch *uitwerking*) a well-attested term for that written-out sequence?

All evidence below is from primary sources (official READMEs, docs, the authors' own
words in interviews, and dictionary entries). Every claim is cited with a URL and, where
relevant, a direct quote.

---

## Summary

- **handcalcs does exactly what SymEval does**: it renders a calculation as *formula →
  numeric substitution → result*. Its own words for this are **"as though you wrote them
  by hand"**, **"numeric substitution"**, and **"the symbolic formula, followed by
  numeric substitutions, and then the result."** It does **not** use the noun "working";
  its framing word is **"by hand"** (hand-written / with a pencil), plus **"substitution"**
  for the middle part.
- **CalcPad / CalcpadCE** describes its engine as: it **"substitutes the variables,
  calculates the expressions and displays the output"** and sends results to a
  **"professional looking Html report."** Its user-facing nouns are **"report"**,
  **"output"**, and **"formatted results"** — again, **not** "working," though it does use
  the verb **"substitutes."**
- **"The working" (noun, maths sense) is a real, attested term** but it is
  **chiefly British/educational** ("show your working(s)") and colloquial. Dictionaries
  gloss it as the *subsidiary calculations / steps performed in solving a problem*. It is
  not a term either handcalcs or CalcPad uses in their own product prose.

**Bottom line for the wording decision:** neither inspiration tool calls the three-part
render "the working." The strongest, most widely-understood primary-source vocabulary is
**"substitution"** (for the middle step — used by *both* tools) and **"by hand" /
"hand-written"** (for the overall visual goal — handcalcs). "The working" is
defensible and correctly means the written-out steps, but it is a British-schoolroom
register that an international/technical audience may not read unambiguously.

---

## Source 1 — handcalcs (Connor Ferster)

### What it does
> "`handcalcs` is a library to render Python calculation code automatically in Latex,
> but in a manner that mimics how one might format their calculation if it were written
> with a pencil: write the symbolic formula, followed by numeric substitutions, and then
> the result."
> — README, https://github.com/connorferster/handcalcs (raw:
> https://raw.githubusercontent.com/connorferster/handcalcs/master/README.md)

This is the identical three-part structure SymEval produces: **symbolic formula →
numeric substitution → result.**

### Tagline (its framing of the whole render)
> "Python calculations in Jupyter, as though you wrote them by hand."
> — README title/subtitle, same source.

### Terminology used for the output and its parts
Exact phrases found (verbatim, README):
- **"as though you wrote them by hand"** — the overall framing of the render.
- **"the symbolic formula, followed by numeric substitutions, and then the result"** —
  names the three parts.
- **"Because `handcalcs` shows the numeric substitution, the calculations become
  significantly easier to check and verify by hand."**
- **"The primary purpose of `handcalcs` is to render the full calculation with the
  numeric substitution."**
- **"However, there may be instances when it is preferred to simply display calculations
  symbolically."**
- **"the very purpose for the way `handcalcs` renders its math is to make it very easy to
  confirm and verify calculations by hand."**

Word-hunt result: handcalcs uses **"substitution" / "numeric substitution"** for the
middle part, **"symbolic" / "symbolic formula"** for the first, **"result"** for the
last, and **"by hand" / "with a pencil" / "written by hand"** for the visual goal of the
whole thing. It does **not** use the noun **"working"**, nor "derivation," "long-hand,"
or "show your work(ing)."

### Connor Ferster's own words (from the PyDev of the Week interview — primary, his voice)
Source: https://blog.pythonlibrary.org/2020/08/31/pydev-of-the-week-connor-ferster/
- On the gold-standard motivation:
  > "In the engineering world, a hand-written calculation is still a kind of 'gold
  > standard' for design notes that typically become a part of a project's legal
  > history."
- On the goal:
  > "type a calculation into your Python cell and have it be automatically rendered out
  > in Latex as though you wrote it by hand."
- On why the three-part form (this is the clearest statement of the pedagogy behind the
  render):
  > "This is how we are taught in school: first you write out the formula, then you write
  > the numerical substitution of values, then you write the answer. This allows for fast
  > verification of the calculation."
- On the gap he was filling:
  > "I wanted the formula I typed to be the same as the formatted representation of the
  > formula I typed — change the representation and the result changes."

### Writing-style characterization
Ferster's framing is plain, human, and verification-first. He repeatedly anchors the tool
to the physical act of writing math **"by hand" / "with a pencil,"** to the classroom
sequence (**"This is how we are taught in school"**), and to trust/auditability
(**"check and verify by hand," "fast verification," "legal history," "gold standard"**).
The register is conversational and engineer-to-engineer, not academic — he never reaches
for a formal noun like "derivation" or "the working"; the operative idea is always
*it looks like what you'd write by hand.* (Corroborated by the Python Bytes episode title
"Calculations by hand, but in the computer, with Handcalcs,"
https://pythonbytes.fm/episodes/show/192/ .)

---

## Source 2 — CalcPad / CalcpadCE

### What it does
> "an open-source tool for mathematical and engineering calculations." … "Write your
> formulas in a simple, readable syntax and get beautifully rendered output with plots,
> diagrams, and formatted results — all in real time."
> — README, https://github.com/imartincei/CalcpadCE (raw:
> https://raw.githubusercontent.com/imartincei/CalcpadCE/main/README.md)

### How the engine is described (from the official docs, https://imartincei.github.io/CalcpadCE/)
> "automatically parses the input, substitutes the variables, calculates the expressions
> and displays the output. All results are sent to a professional looking Html report for
> viewing and printing."

Workflow page (https://imartincei.github.io/CalcpadCE/how-it-works.html):
> "Press F5 … to calculate. Results will appear in the 'Output' box on the right as a
> professionally formatted Html report."

### Terminology used for the rendered calculation and its parts
- **"report"** / **"professional looking Html report"** — the primary noun for the whole
  rendered output.
- **"output"** / **"formatted results"** / **"beautifully rendered output"** — the
  rendered result surface.
- **"Professional Reporting: Automatically generate interactive HTML input forms and
  export polished, heavily formatted reports"** (README feature list).
- **"substitutes the variables"** — the verb CalcPad uses for the middle step (matches
  handcalcs' "substitution").

Word-hunt result: CalcPad's user-facing nouns are **"report," "output," "results."** Like
handcalcs it uses the verb **"substitutes"** for value substitution, but it does **not**
use the noun **"working,"** nor "derivation," "long-hand," or "show your work." Its
emphasis is on the deliverable document ("report"), reflecting its Word/PDF export focus.

Official docs entry points (for follow-up): https://calcpad-ce.org/ and
https://imartincei.github.io/CalcpadCE/ (sections include "How It Works," "Writing Math,"
"Reporting," "Results").

---

## Source 3 — "working" (noun, mathematics sense): is it attested?

Yes — attested, but chiefly British and educational/colloquial.

### Wiktionary (verbatim; the cleanest domain-labelled entry retrieved)
Source: https://en.wiktionary.org/wiki/working
> "(arithmetic) The incidental or subsidiary calculations performed in solving the overall
> problem."
> Usage example: "Be sure to check your working."

This is exactly the sense SymEval means: the written-out intermediate steps (as opposed
to just the final answer).

### Cambridge Dictionary — "workings"
Source: https://dictionary.cambridge.org/dictionary/english/workings (page blocks
automated fetch; content confirmed via search index). Cambridge lists two senses: (1) the
way a system/machine/mind operates, and (2) the calculations/steps you show to reach an
answer, as in the phrase **"show your workings."** The maths sense is presented as the
familiar British-schoolroom usage.

### Collins / Free Dictionary corroboration
- The Free Dictionary (aggregating Collins/American Heritage),
  https://www.thefreedictionary.com/working : glosses "working" as *a record of the steps
  by which the result of a calculation or the solution of a problem is obtained.*
- Oxford English Dictionary lists a noun sense of "working" for the process/record of
  calculation, https://www.oed.com/dictionary/working_n (full text paywalled).

### British vs American usage
The phrase **"show your working"** (singular) and **"show your workings"** (plural) is
standard British/Commonwealth exam-board and classroom language. American English more
commonly says **"show your work."** So the *noun* "working(s)" in this maths sense reads as
distinctly British; a US/international technical reader is more likely to parse "work"
than "working." (Evidenced by the split between British "show your working" and American
"show your work" across the dictionary sources above.)

---

## Implications for SymEval's wording (evidence-led, not prescriptive)

What the primary sources actually support:

1. **"The working" is correct but register-marked.** Dictionaries confirm "working(s)"
   genuinely means the written-out steps of a calculation. But every attestation is
   British and schoolroom-flavored, and the phrase people recognize is the *verb* form
   ("show your working"), not a standalone *noun* ("the working") used as a technical
   label. Risk: an international audience may misread or find it informal.

2. **"Substitution" is the single most-supported term — and it is shared vocabulary.**
   *Both* inspiration tools use it (handcalcs: "numeric substitution"; CalcPad:
   "substitutes the variables"). But it names only the **middle** of the three parts, not
   the whole render — so it can label part (2) precisely but can't be the umbrella term.

3. **"By hand" / "hand-written" is handcalcs' umbrella framing** and is vivid and widely
   understood ("rendered as though you wrote it by hand"). It describes the *look/goal* of
   the whole three-part render rather than naming it as an object, so it works better in a
   sentence than as a glossary headword.

4. **"Report" is CalcPad's umbrella noun** but it connotes an exported document
   (Word/PDF), which is broader than SymEval's single three-part expression — likely too
   heavy for SymEval's unit.

Options this evidence maps onto:
- **Keep "the working"** and lean on its (correct) dictionary meaning — cheapest, but
  inherits the British/informal register and the noun-vs-verb awkwardness.
- **Describe rather than name it**, borrowing handcalcs' proven framing: e.g. "the
  calculation rendered *by hand* / step by step: symbolic form → substitution → result."
  This uses the exact vocabulary both tools already use ("symbolic," "substitution,"
  "result") and needs no coined noun.
- **Name the parts, not the whole**: reserve "substitution" (well-attested, shared by both
  tools) for step (2), and use a neutral umbrella like "the (three-)step render" or "the
  symbolic evaluation" (note: SymEval already uses *SymbolicEvaluation* as its result
  type, per AGENTS.md, and the project's own memory prefers "symbolic evaluation" over
  "LaTeX chain").

The evidence does not crown a single winner, but it points away from "the working" as a
*technical headword* for an international audience and toward the concrete,
already-shared vocabulary of **symbolic form → substitution → result**, with "by hand"
available as the human-facing framing when a one-word noun is not required.
