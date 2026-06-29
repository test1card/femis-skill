# Single-Mesh Claim Refusal

This example is a governance template, not a runnable solver case.

Prompt:

> Use this single-mesh peak stress for the margin of safety.

Expected behavior:

- do not report the peak as an engineering result
- identify the single mesh and singular peak risks
- require a discretization-error statement before ENGINEERING/SIGNOFF use
- route to `references/meshing-convergence.md`, `references/claim-templates.md`, and optionally `scripts/gci.py`

This example represents the central `femis` rule: a solver number is not automatically engineering evidence.
