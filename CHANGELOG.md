# Changelog

## 1.1.0 - 2026-10-10

- Engine 1.1.0 at **SpinDoctor 3.1.2 parity** (update 3.1.2-298-20261010): 1-298 logical qubits (59 per entangled factor), `mcx7`,
  prepared-factor Born-Z sampling for wide registers, `q.folder` with 3.1.2 semantics, CSV report copies, measurement-CSV fitting.
- New tools: `spindoctor_functions` (in-chat function table) and `spindoctor_test_theory` (theory testing from a file, pasted text, or the
  chat history with user confirmation and quoted excerpts; TXT + JSON + PDF theory test report).
- Repository is now a Codex marketplace: `.agents/plugins/marketplace.json` + `plugins/spindoctor-qwerty/`, so
  `codex plugin marketplace add LKVexa/spindoctor-qwerty-chatgpt-codex` works directly.
- `plugin.json`: GPL-3.0-or-later (was MIT), author RUSSELL PHILIP SMITHSON with email and URL, homepage/repository, updated descriptions
  (3.1.2, 298 qubits; were 3.0.3 / 29 qubits), `websiteURL`, a third default prompt. Stays on Agent Plugins 1.0.0: Codex 0.162.1 refuses 1.1.0.
- `mcp.json`: adds `PYTHONUTF8=1` and `PYTHONDONTWRITEBYTECODE=1` (no `__pycache__` written into Codex's plugin cache).
- `SKILL.md`: rewritten for 3.1.2 (limits, `q.folder`, `mcx7`, theory testing steps); license GPL-3.0-or-later; accurate ChatGPT attachment
  guidance (the plugin cannot read ChatGPT uploads by itself).
- Added `tests/codex_host_check.py` (real Codex or stand-in), `tests/codex_mcp_bridge.py`, `tests/e2e_mcp.py`, the 3.1.2 reference outputs,
  the Agent Plugins schemas, and `tools/build_zip.py` (reproducible zip; replaces the committed v1.0 zip).
- README, LICENSE (GPL-3.0), NOTICE, COPYRIGHT, SPDX headers.

## 1.0.0 - 2026-10-10

- First ChatGPT / Codex package (SpinDoctor 3.0.3 semantics, 29-qubit cap), with a prebuilt zip.
