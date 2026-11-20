---
name: pidc-report
title: PI-DC report of a solved SIwave DC-IR project
description: Export DC report images, current density, via current, voltage, power tree, HTML report
guide: pidc_workflow
inputs: [folder with solved .siw + .siwaveresults]
steps:
  - tool: pidc_export
  - tool: pidc_current_density
  - tool: pidc_via_current
  - tool: pidc_voltage_distribution
  - tool: pidc_power_tree
  - tool: pidc_report
---
Use for a PI-DC review of a solved SIwave folder (works in place, never saves the project).
Follow `get_guide("pidc_workflow")`.
