---
name: re-cut
title: Re-cut an interface like last time
description: Reuse the agreed settings of an earlier run; show only the differences
guide: interface_sim
inputs: [interface name, workspace .aedt]
steps:
  - tool: isim_previous
    checkpoint: true
    note: user picks the earlier run
  - tool: isim_start
  - tool: isim_recut
  - tool: isim_review
    checkpoint: true
    note: MANDATORY - reused when board / ends / nets unchanged; HTML report always; an earlier approval is shown, never reused
  - tool: isim_confirm_content
    checkpoint: true
    note: GATE A - user resolves every difference
  - tool: isim_cut
  - tool: isim_check_ends
  - tool: isim_apply
    checkpoint: true
    note: GATE B
---
Use when the engineer says "cut lại X như lần trước" or "settings cũ". Never re-type old values.
Follow `get_guide("interface_sim")` (Phase R).
