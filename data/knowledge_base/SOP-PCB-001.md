# SOP-PCB-001 — Automated Optical Inspection of Assembled PCBs

> Sample SOP for the Visual QC Copilot knowledge base. Replace with your own drafted version.

## 1. Purpose
Define verification and disposition of anomalies flagged on assembled printed circuit boards after reflow.

## 2. Scope
Applies to all boards imaged at the post-reflow AOI station.

## 3. Defect classes
- Missing component: placement absent. Severity: critical.
- Solder bridge: unintended solder connection between pads or leads. Severity: critical.
- Open / insufficient solder: incomplete joint. Severity: major.
- Misalignment / tombstoning: component shifted or lifted at one end. Severity: major.
- Scratch on solder mask without exposed copper: minor.
- Foreign material / flux residue: minor if outside component areas, major if on pads.

## 4. Verification of automated flags
4.1 Flagged boards go to the review station; the technician inspects the heatmap region under 10x magnification.
4.2 ESD wrist strap must be worn and tested before handling any board.
4.3 Unconfirmed flags are recorded as "false call" with board serial number for model retraining.

## 5. Disposition
5.1 Critical: send to rework. A board may be reworked a maximum of 2 times; after that it is scrapped.
5.2 Major: send to rework; re-inspect at AOI after rework.
5.3 Minor: accept, log the finding.
5.4 If the same defect type appears at the same reference designator on 3 consecutive boards, stop the line and notify process engineering (likely stencil or placement issue).

## 6. Records
Record board serial, reference designator (if identifiable), defect class, disposition and technician ID in the MES.
