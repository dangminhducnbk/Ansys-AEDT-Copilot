# Contracts: `aedt_copilot.interface_sim.settings`

Pure except reading the template / state. Tests: `tests/unit/test_isim_ends_settings.py`.

## `proposal(state, ends=None, values=None) -> dict`

`ends` = `ends.json` data (reasons, unusual); `values` = values already given (shown instead of defaults).

Output: `{rows[{key, name, unit, value, mandatory, source, reason}], table_md}` for all template rows of scope
`channel`; `value` = template default (mandatory sweep rows empty); measured info (e.g. pad short side × ratio for
solder ball) shown in `reason`, never as value. Structural rows (`cutout.*`, `series.keep`) carry the value agreed
in content and are marked `locked (re-cut to change)`.

## `validate(values, handling=None, ends=None, structural=None) -> dict`

`structural` = `cutout.*` / `series.keep` agreed in content (a different value → "re-cut needed").

| Input | Type | Valid |
|---|---|---|
| values | dict[str, any] | keys ⊆ template keys of scope channel |
| handling | dict[refdes, option] \| None | every `unusual` end in `ends` has an option from its `options` |

Output: `{valid, errors[], P}`; errors = `cut_board.config.build_params` messages (same as Excel flow) + handling
errors + structural change (`cutout.*` differs from content → "re-cut needed"). Side effects: none.

## `save(request_id, name, values, handling, rows) -> dict`

`rows` = proposal rows written to `settings.md`.

Writes `settings.json` + `settings.md` (agreed table, time). Called by `isim_apply` after GATE B.
