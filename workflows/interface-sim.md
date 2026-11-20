---
name: interface-sim
title: Interface simulation (no Excel)
description: Agree interface content, cut on copies, end check + settings, apply, merge into the workspace, optional remote run
guide: interface_sim
inputs: [workspace .aedt, schematic netlist (preferred) or PDF / BOM (optional), interfaces (refdes and / or nets)]
steps:
  - tool: isim_start
  - tool: isim_trace
  - tool: isim_review
    note: MANDATORY right after trace - always writes the HTML report (OK / NOT OK only, never a gate)
  - tool: isim_cut_preview
    note: final cut region with the default cut settings; returns answer_md = the whole reply, pasted verbatim
  - tool: isim_confirm_content
    checkpoint: true
    note: GATE A = the ONE approval - send the final cut area + the review report, ask "read the review and confirm the cut"; refused without a current review, report or preview
  - tool: isim_cut
  - tool: isim_check_ends
  - tool: isim_settings_form
    note: settings FORM (mandatory; without widget the full table once) - never ask values one by one
  - tool: isim_apply
    checkpoint: true
    note: GATE B - user agrees the settings form / table
  - tool: isim_merge
    checkpoint: true
    note: GATE C - user approves the merge
  - tool: isim_run
    checkpoint: true
    note: GATE D - only when the user asks to run
---
Use for one or more interfaces of a workspace, agreed with the engineer step by step.
Follow `get_guide("interface_sim")`; it holds every rule and gate of this process.
