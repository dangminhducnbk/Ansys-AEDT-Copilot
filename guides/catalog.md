<!-- Tool catalog: every tool has a safety level, every process is a workflow (team or personal). Read for any request that is not clearly one existing process, for "bạn làm được gì", and before combining tools into a new sequence. -->
# TOOL CATALOG — TOOLS + WORKFLOWS

## 1. MISSION
Serve any engineering request by picking a workflow (a process) or composing a sequence of catalog tools, agreed
with the engineer. Processes are not fixed: the same tools serve many workflows.

## 2. RULES OF ENGAGEMENT
- Start with `list_workflows()` and `list_tools()` for any request that is not clearly one existing process.
- Workflow found → `get_workflow(name)`. If it has a `guide`, call `get_guide(<guide>)` and follow that guide (it
  holds the rules and gates of that process). Else follow its `steps` in order.
- Same name in team and personal → ask the engineer which one; then `get_workflow(name, source)`.
- Workflow status `broken` (a step names a tool that does not exist) or `error` → tell the engineer, do not run it.
  Status `shadowed` = an old personal copy (folder used before 2.0.0) hidden by a newer one of the same name: ignore it.
- No workflow fits → propose a sequence of tools (table: step, tool, inputs, safety) and wait for the engineer's go
  before the first step that is not `read`.
- `kind: process` tools (`isim_*`) work only inside their process.
  Never mix them into another sequence; use the matching `design_*` tool instead.
- Checkpoints (`checkpoint: true`) → STOP, show the result, wait for an explicit go ("đồng ý", "làm đi").
- Safety levels:
  | Safety | Meaning | What you do |
  |---|---|---|
  | read | design / board not changed | run |
  | copy | new design / file; given file unchanged | run, give the result path |
  | original | changes the given file (only when `condition`) | explain + backup, wait for go, pass the `gate` flag |
  | workspace | changes the engineer's AEDT project | show what is added, wait for go, pass the `gate` flag |
  | remote | runs on another machine | only when asked, pass the `gate` flag |
  Gates are locked in the server for each tool, whatever workflow calls it. Never set a gate flag without the
  engineer's explicit go in THIS conversation.
- Never call or propose an operation that is not a registered tool (`list_tools`), and never write ad-hoc scripts
  (pyaedt-mcp, PyEDB) to fill a gap. A missing tool → tell the engineer what is missing; it is added through Spec Kit
  (specify → plan with Tool catalog check → tasks → implement), never improvised.
- Workflow status `misplaced` = a process tool (`kind: process`) used outside its own process — do not run that step;
  use the matching `design_*` tool or the process workflow.
- Each step's result path feeds the next step (e.g. `design_cutout` result `.aedb` → `design_ports` board).
- Never invent mandatory values (sweep start / stop / step). Ask.
- Save a sequence as a personal workflow ONLY when the engineer asks: write the Markdown (front matter `name`,
  `title`, `description`, `inputs`, `steps[{tool, note, checkpoint}]` + body) and call `save_workflow`. Existing
  name → ask before `overwrite=true`. Team workflows (repo `workflows/`) are edited by the repo owner only.
- Reply in the user's language. Short. Tables. Give file paths.

## 3. EXECUTION
1. "Bạn làm được gì" / new user → `list_workflows()` + `list_tools()`; answer in ONE message: workflows table
   (name, what for, checkpoints) + tools grouped (board, cut, design, merge, layout, pidc, processes).
2. Request → match a workflow by description / inputs. Ask only for missing inputs listed in the workflow.
3. Run the steps. After each step: one line of result (path, counts, warnings). At a checkpoint: stop and ask.
4. Unusual result (end check `unusual`, check `mismatches`, warnings) → show it, ask how to continue.
   `no_gnd_pin` / `gnd_questions` (end without GND pin): send the image, ask a multiple-choice question with exactly
   its `options`; never choose. No design tool rebuilds an end: the choice is used by `isim_apply`.
5. End: table of produced files (path, what it is) and what is not done.

## 4. WORKFLOW FORMAT
```
---
name: my-flow                 # slug a-z 0-9 -
title: My flow
description: one line
inputs: [board .aedb, refdes, nets, sweep GHz]
guide: ""                     # or an existing guide name (then the guide rules apply)
steps:
  - tool: design_trace
  - tool: design_cutout
    checkpoint: true
    note: user agrees nets / ends first
---
Free text: when to use, notes.
```
Folders: team = repo `workflows/`; personal = `%USERPROFILE%\.aedt_copilot\workflows` (env `AEDT_COPILOT_WORKFLOWS`).
Personal files saved before 2.0.0 (old folder) are still listed and read; new saves go to the new folder only.
