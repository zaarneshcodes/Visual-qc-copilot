# SOP-BTL-001 — Visual Inspection of Glass Bottles (Post-Forming Line)

> Sample SOP for the Visual QC Copilot knowledge base. Replace with your own drafted version.

## 1. Purpose
Define how automated anomaly flags on glass bottles are verified, classified and dispositioned.

## 2. Scope
Applies to all bottles inspected at the end-of-line camera station (top-down view of the bottle mouth and shoulder).

## 3. Defect classes
- Broken large: missing glass > 2 mm along the rim or body. Severity: critical.
- Broken small: chip or missing glass ≤ 2 mm. Severity: major.
- Contamination: foreign particle, residue or debris visible inside or on the bottle. Severity: major if inside, minor if external and removable.
- Scratch / surface mark: no material loss. Severity: minor.

## 4. Verification of automated flags
4.1 Any image with anomaly score ≥ the line threshold must be held for human verification within 15 minutes.
4.2 The operator compares the heatmap location with the physical bottle under the inspection lamp.
4.3 If the operator cannot confirm the defect, record "false alarm" with the image ID; three false alarms in one hour trigger a model review ticket to the QC engineer.

## 5. Disposition
5.1 Critical: reject and destroy (cullet bin). Quarantine the previous 50 units for 100% manual inspection.
5.2 Major: reject. If 3 or more major defects occur within 30 minutes, stop the line and notify the shift supervisor.
5.3 Minor: accept with log entry, unless the customer specification is "Grade A cosmetic", in which case reject.

## 6. Safety
Handle broken glass only with cut-resistant gloves (EN 388 level C or higher). Never reach into the conveyor while running.

## 7. Records
Log image ID, timestamp, anomaly score, defect class, disposition and operator ID in the QC system before end of shift.
