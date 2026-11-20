---
name: layout-review
title: Layout review as data (any board or design)
description: Measure review checks per channel (OK / NOT OK), NOT OK counts stored in a review record, HTML report on request
guide: review_measure
inputs: [board .aedb or cut design, "channels CompA-CompB:pattern; ...", checks (optional)]
steps:
  - tool: design_review
    note: all checks, or the one the engineer names; html=true for the report with pictures
  - tool: get_guide
    note: review_measure rules for the chat summary
---
Use for "review layout", "kiểm tra via stub / SOV / GND via / chiều dài" (HTML with images: `html=true`).
Follow `get_guide("review_measure")`. Ends with NOT OK counts per channel in the review record
(`<board folder>/Ansys AEDT Copilot/reviews/`); no severity levels, the engineer decides. Interface
simulation of the same board / channel reuses the record while valid. Inside interface simulation use `isim_review`
(mandatory step, always with the HTML report).
