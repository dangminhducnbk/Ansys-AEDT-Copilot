# Feature Specification: Kitchen model — tools as utensils, skills as recipes

**Feature Branch**: `008-kitchen-tools-recipes` (work stays on `main`, user repo, no branch workflow)

**Created**: 2026-11-07

**Status**: Draft

**Input**: User description: "tôi muốn ansys-aedt-copilot giống như một nhà bếp, có nghĩa là mọi tool giống như dao, thớt,
nồi,... còn quy trình skills giống như công thức nấu ăn. Mọi thứ đều phải sẵn sàng cho nhiều công thức nấu ăn khác nhau
chứ không cố định một quy trình không thể thay đổi."

## Clarifications

### Session 2026-11-07

- Q: Where are approvals locked? → A: On the utensil by its risk level (merge, writing originals, remote run always
  need the engineer's go), whatever recipe calls it.
- Q: Who adds recipes, where? → A: Both: team recipes in the repo (owner) + personal recipes in a per-user folder.
- Q: Scope of the first delivery? → A: Catalogs + recipe format + missing utensils now; rebuilding the existing
  processes as recipes in later features.

## Problem

- The copilot has ~51 MCP tools, but most belong to ONE process and only work inside it: the Excel cut flow
  (`propose_channels` → `start_cut_batch` → `merge_to_project`), interface simulation (`isim_*`), PI-DC (`pidc_*`).
  A tool of one process cannot be used by another (for example: cutout or GND cleanup alone on any board, merge any
  cut design into any workspace).
- Gates and steps are wired to a process position ("merge only after report of this job"), so a new way of working
  needs new code instead of a new recipe.
- Feature 007 started the other direction (atomic `design_*` tools on any `.aedb`) but only for setup, sweep, airbox,
  ports and solder ball.
- The engineer wants: tools = utensils (knife, board, pot) that are always ready and can be used in any order;
  skills = recipes that combine them. New ways of working must come from new recipes, not from new fixed processes.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Use any utensil on its own (Priority: P1)

The engineer asks for one operation ("cắt vùng quanh U14-U26", "dọn GND design X", "merge design Y vào workspace Z",
"đặt port cho net A") and the agent does exactly that, on any suitable input, without going through a whole process.

**Why this priority**: this is the base of the kitchen; recipes can only be flexible if every utensil works alone.

**Independent Test**: on board1 copies, run each utensil alone on an input that did not come from its usual process
(e.g. GND cleanup on a cut design made by hand in AEDT, merge of a `design_*` result into a copy of the workspace);
each gives the same result as inside its old process.

**Acceptance Scenarios**:

1. **Given** any board or design file, **When** the engineer asks for one operation, **Then** the agent finds the
   matching utensil in the catalog and runs it alone, on a copy by default, and reports what changed.
2. **Given** an input that does not meet a utensil's preconditions (wrong file type, design open in AEDT, missing
   nets), **When** the utensil is called, **Then** it refuses before touching anything and says what is missing.
3. **Given** a utensil's result, **When** another utensil takes it as input, **Then** it works without conversion
   (results are standard inputs: board / design file paths, net lists, settings).

---

### User Story 2 - Follow a recipe (Priority: P1)

The engineer asks for a known job ("cut board kiểu Excel", "interface simulation", "PI-DC report", "sửa layout"), and the
agent follows that recipe step by step using utensils from the catalog, stopping at the recipe's checkpoints.

**Why this priority**: existing work must keep running exactly as today while it is rebuilt from utensils.

**Independent Test**: run the existing processes as recipes on board1 / B04 copies; results identical to today
(`tests/regression.py`, `tests/pidc_check.py`, `tests/isim_check.py` PASS).

**Acceptance Scenarios**:

1. **Given** the catalog of recipes, **When** the engineer asks what the copilot can do, **Then** the agent lists the
   recipes and the utensils, each with one line on what it does.
2. **Given** a recipe, **When** the agent follows it, **Then** every step names the utensil it uses and every
   checkpoint stops for the engineer's explicit go.
3. **Given** the existing processes, **When** they are run as recipes, **Then** MCP tool names, Excel / CSV formats,
   output folders and results stay the same (Principle IX).

---

### User Story 3 - Change or add a recipe without code (Priority: P2)

The engineer wants a different way of working (skip the layout review, cut then only set sweep, merge several
`design_*` results, run PI-DC on a cut design...). The agent builds the sequence from utensils on request, and a recipe
that should be kept is written as a new recipe file, with no code change.

**Why this priority**: this is the "many recipes" goal; it needs Stories 1–2 first.

**Independent Test**: write a new recipe file that combines utensils in a new order; a new chat follows it end to end
on a board1 copy without any code change.

**Acceptance Scenarios**:

1. **Given** a request that matches no recipe, **When** every needed utensil exists, **Then** the agent proposes a
   step list from the catalog, the engineer agrees, and the agent runs it with the same safety rules.
2. **Given** a sequence the engineer wants to keep, **When** they ask to save it, **Then** it becomes a recipe file
   that appears in the recipe list in a new chat.
3. **Given** a request that needs a utensil that does not exist, **When** the agent plans it, **Then** it says which
   utensil is missing and never writes an ad-hoc script instead.

---

### Edge Cases

- Two recipes need different defaults for the same utensil: the recipe passes its own values; utensil defaults stay
  in the templates (Principle III).
- A utensil that writes the engineer's original file or workspace (merge, in-place edits) or uses a remote server:
  it always needs the engineer's explicit go, whatever recipe calls it.
- An ad-hoc sequence fails half way: earlier results stay (copies), the failing step reports what is missing, nothing
  is deleted.
- Old process tools called directly by an old chat or prompt: they keep working (thin wrappers over utensils).
- A recipe refers to a utensil that was renamed or removed: the recipe list marks it as broken instead of failing mid
  run.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The copilot MUST provide a catalog of utensils: every operation available as a tool on its own, with its
  inputs, outputs, preconditions, what it writes, and its safety level (read-only / writes a copy / writes the
  original / remote).
- **FR-002**: Every utensil MUST validate its inputs and preconditions before touching any file and refuse with a
  message that names the missing or wrong input (Principle VII).
- **FR-003**: Utensils that modify a design MUST work on a copy by default; writing an original file or workspace MUST
  back up first and require the engineer's explicit go (Principles I, II).
- **FR-004**: Utensil outputs MUST be usable as inputs of other utensils without conversion.
- **FR-005**: Operations that today exist only inside a process MUST become utensils usable alone, at least: board
  read / trace, cutout, GND cleanup, end check, port creation, solder ball, setup, sweep, airbox, self-check, merge
  into a workspace, layout review, PI-DC skills, layout edit.
- **FR-006**: The copilot MUST provide a catalog of recipes: each recipe lists its steps (utensils), its checkpoints
  and its inputs, in a recipe file readable by the agent.
- **FR-007** (later feature, see FR-012): The existing processes (Excel cut, interface simulation, re-cut, re-apply, PI-DC, layout edit, design
  tools) MUST be expressed as recipes over the utensils, with identical results and unchanged public interface.
- **FR-008**: The agent MUST be able to run a sequence that is not a saved recipe, built from the catalog and agreed
  with the engineer, under the same safety rules.
- **FR-009**: A new recipe MUST be addable as a file without code change and appear in the recipe list in a new chat.
- **FR-010**: Approvals MUST be locked on the utensil by its safety level, whatever recipe or ad-hoc sequence calls it:
  every utensil that writes an original file / workspace (merge, in-place edit) or runs on a remote server MUST refuse
  without the engineer's explicit go (server-side flag). Recipe checkpoints are guidance for the agent on top of that.
- **FR-011**: Recipes MUST come from two places: team recipes in the repo (added by the repo owner, shared to every user
  by `git pull`) and personal recipes in a per-user folder on each PC. The recipe list MUST show both and mark the
  source; on a name clash the personal recipe is shown as a separate entry, never silently replacing the team one.
- **FR-012**: This feature delivers: the utensil catalog, the recipe catalog and recipe format, and the missing
  utensils of FR-005. Rebuilding the existing processes as recipes (FR-007) is planned as later features; until then
  the existing processes keep working unchanged and are listed in the recipe catalog as they are.
- **FR-013**: A guide MUST tell the agent how to use the kitchen: read the catalogs, pick a recipe or build a sequence,
  never write ad-hoc scripts when a utensil is missing (Principle IV).

### Key Entities

- **Utensil**: one operation; name, inputs, outputs, preconditions, writes, safety level, defaults source.
- **Recipe**: named sequence of steps (utensils with their inputs), checkpoints, required inputs, description.
- **Catalogs**: the list of utensils and the list of recipes the agent reads at the start.
- **Checkpoint**: a point where the engineer must give an explicit go before the next step.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100 % of the operations listed in FR-005 can be run alone on an input that did not come from their old
  process.
- **SC-002**: Existing processes keep identical results (now, and when later rebuilt as recipes): `tests/regression.py`, `tests/pidc_check.py`,
  `tests/isim_check.py` PASS with no reference change.
- **SC-003**: A new recipe (a new order of at least 4 utensils) runs end to end in a new chat with 0 lines of code
  changed.
- **SC-004**: Asked "bạn làm được gì", the agent lists all recipes and utensils in one answer, each in one line.
- **SC-005**: 0 operations that write an original file, a workspace or a remote server run without the engineer's
  explicit go.

## Assumptions

- "Tool" = an MCP tool the agent calls; "skill / quy trình" = a guide / prompt (recipe) the agent follows.
- Existing MCP tool names stay (Principle IX); process tools become thin wrappers over utensils, new utensils are
  additions.
- Defaults stay in `templates/*.csv` (Principle III); recipes may pass their own values.
- Work is done on copies by default; nothing is deleted.
- This feature changes structure, not results: minor version for the new utensils / catalogs, restructure parts must
  give identical results.
- ROADMAP: this becomes 008; review layout and later features move +1.
