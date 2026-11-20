---
name: layout-edit
title: Layout improvement on a copy
description: Read an area, agree a plan, apply all ops on a copy with checks and images
guide: layout_edit
inputs: [board .aedb, area (box mm), what to change]
steps:
  - tool: layout_region
  - tool: layout_edit
    checkpoint: true
    note: user agrees the plan before it is applied
---
Use for copper / void / trace / via changes of an EDB. Never ad-hoc scripts.
Follow `get_guide("layout_edit")`.
