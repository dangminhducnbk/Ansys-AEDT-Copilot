---
name: design-tools
title: One operation on any design
description: Read, then setup / sweep / airbox / ports / solder balls on a copy (in place only with approval)
guide: design_tools
inputs: [design .aedb, operation + values]
steps:
  - tool: design_read
  - tool: design_setup
    note: or design_sweep / design_airbox / design_ports / design_solder_ball as asked
  - tool: design_check
---
Use for a single change on an existing design. Copy by default; in place needs the user's explicit go.
Follow `get_guide("design_tools")`.
