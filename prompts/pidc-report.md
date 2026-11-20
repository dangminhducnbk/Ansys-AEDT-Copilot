---
description: PI-DC report of a solved SIwave DC-IR folder (current density per power net x layer, via current) -> HTML + slide-ready images
---
Make a PI-DC report for this folder: $ARGUMENTS

1. Call get_guide("pidc_workflow") and follow it exactly (it lists the skills and their guides).
2. If the folder (with the solved .siw and .siwaveresults) is missing, ask the user. Ask for the DC sim name only if the project has several.
3. pidc_export -> pidc_current_density -> pidc_via_current -> pidc_voltage_distribution -> pidc_report,
   polling task_result for long steps.
4. Reply with the HTML path, the images folder and the hand-off summary from the guide.
