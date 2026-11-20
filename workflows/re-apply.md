---
name: re-apply
title: Change simulation settings of an applied interface
description: Re-apply setup / sweep / airbox only (cut group locked); backup first
guide: interface_sim
inputs: [request id, interface name, new setup / sweep / airbox values]
steps:
  - tool: isim_status
  - tool: isim_validate_settings
  - tool: isim_apply
    checkpoint: true
    note: GATE B - user agrees the new values
  - tool: isim_merge
    checkpoint: true
    note: GATE C - merged again as a new design
---
Use when an interface is already applied or merged and only simulation settings change.
Follow `get_guide("interface_sim")` (step 8 re-apply).
