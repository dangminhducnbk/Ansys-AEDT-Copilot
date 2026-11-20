---
name: cut-sweep-merge
title: Cut one channel, set ports + sweep, merge
description: Example workflow built only from catalog tools - trace, cutout, end check, ports, setup, check, merge
inputs: [board .aedb, two component refdes, net names / patterns, sweep start / stop / step GHz, workspace .aedt]
steps:
  - tool: design_trace
    note: show nets, series parts and end types to the user
  - tool: design_cutout
    checkpoint: true
    note: user agrees nets / ends before cutting
  - tool: design_end_check
    note: report unusual ends; stop if the user wants another handling
  - tool: design_ports
    note: on the cut design (copy result of design_cutout), refdes = both ends
  - tool: design_setup
    note: sweep values from the user, never invented
  - tool: design_airbox
    note: team defaults unless the user gives values (a new cut has the PyEDB default airbox)
  - tool: design_check
  - tool: design_merge
    checkpoint: true
    note: user approves the merge (gate user_approved_merge)
---
Example of a new process without code: each step is one catalog tool, each result path feeds the next step.
No GND cleanup / solder ball here; add `design_cleanup` / `design_solder_ball` steps when the engineer wants them.
