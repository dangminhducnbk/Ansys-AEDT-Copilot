# Contracts: `aedt_copilot.interface_sim.schematic`

Pure except file I/O. Tests: `tests/unit/test_isim_schematic.py` (sample BOM xlsx/csv, markdown fixtures).

## `parse_bom(path) -> dict`

| Input | Type | Valid |
|---|---|---|
| path | str | existing `.xlsx` (first sheet with a header row) or `.csv` (UTF-8 / UTF-8-BOM, `,` or `;`) |

Column mapping (case-insensitive): refdes ← `Refdes|Designator|Reference|Ref Des|RefDes|Part Reference`;
part ← `Part Number|PartNumber|MPN|Manufacturer Part Number|Part`; value ← `Value|Comment`; desc ←
`Description|Desc`. Ranges `R1-R4` and lists `R1, R2 R3` expanded.

Output: data-model BOM + `unmapped_columns`. Errors: no refdes column → CopilotInputError(`bom`,
`a refdes column (Refdes / Designator / Reference)`, header); duplicate refdes → listed in `warnings`, first kept.

## `fingerprints(paths) -> list[dict]` / `is_up_to_date(request_id) -> bool`

`[{path, size, mtime}]`; up to date when `schematic.md` exists and stored fingerprints equal current ones.

## `template() -> str`

Empty markdown with the fixed sections and table headers (data-model) — given to the agent.

## `save(request_id, markdown) -> dict`

Preconditions: sections `## Sources`, `## Components`, `## Nets` present with exact headers.
Output: writes `schematic.md` + `schematic.sources.json`; returns counts + warnings (refdes in BOM not in
schematic table and back). Errors: missing section / header → CopilotInputError naming the section.

## `parse(markdown) -> dict`

`{components{refdes: {part, value, desc, page}}, nets{net: {pins[(refdes, pin)], page}}}`; ignores rows it cannot
split (returned in `bad_rows`).
