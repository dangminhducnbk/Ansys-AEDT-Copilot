# Contract: review HTML (033) — replaces specs/026 report contract for the HTML form

`review_report.render(info, chans) -> str` (pure). Input as 026 (`info` board / cell / date / version / params / gate /
source; `chans` review channel dicts) + optional `chans[i]["routing"]` (data-model.md). Bad `chans` →
`CopilotInputError` (unchanged).

Output (English, self-contained):

1. `<h1>Layout Review — Pre-cut</h1>` + 3 lines: **Layout version:** board stem (no `.aedb`), **Review gate verdict:**
   per channel verdict word + translated reason, or "not recorded (standalone report)", **Review date:**
   `dd/mm/yyyy - hh:mm:ss`. A live-fallback warning (027) is kept as a 4th line only when present.
2. Tab bar (`button.tabb`, one per channel) + `div.tabp` per channel; ids prefixed `t<k>-`.
3. Per tab: `1. Summary` table Index · Section (bold title + sentence) · <channel> (OK / NOT OK + "N issue(s)") ·
   Verdict; then `2.k <title>` per section: "This section checks:" numbered list (steering `## Report`), lead `OK` or
   `NOT OK — N issue(s)`, table Index · Verdict · Description · Picture (NOT OK rows only).
4. Routing section: "Signal routing per pair" (`details.pbox` per pair) before its table.
5. No text "HIGH", "MEDIUM", "INFO", "Reference data", "↑ summary", "Overall".
6. Error channel tab: Summary cells "review incomplete" + the error text.

Rule REPORT spec (031 + 033): `{section, title, limit_key, describe, layers, rule, picture?}`; steering parts
`Report` / `Issue` / `Recommendation` (variants keyed by finding name or sub-case) are the only source of the sentences.
