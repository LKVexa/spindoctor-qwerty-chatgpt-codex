# End-to-end results - spindoctor-qwerty-chatgpt-codex 1.1.0

Date: 2026-10-10 (PT). Engine 1.1.0, parity target: **updated SpinDoctor 3.1.2** (build 3.1.2-298-20261010).

**Publishing decision (recorded as instructed):** Russell approved publishing on the basis of the updated SpinDoctor 3.1.2 passing its own
test suite 18/18, with the three 29-qubit test checks adapted to the new 298-qubit limit.

## Host

- **Real host: Codex CLI 0.162.1** (`@openai/codex`, Apache-2.0), installed for free from npm on a Linux test machine. No sign-in, no API
  key, no model call. Each run used a throw-away `CODEX_HOME`.
- Agent Plugins schema check: manifests declare **1.0.0** and validate against the official 1.0.0 schemas; they also satisfy the **1.1.0**
  schema rules (identical apart from the `$schema` identifier). Codex 0.162.1 only recognizes 1.0.0: the same plugin declaring 1.1.0 is
  refused (`missing or invalid plugin.json`), which the test checks as a negative control. MCPB v0.4 does not apply to Codex.

## Clean-room gate (before push)

The staged repo was copied to a fresh empty folder and run with an empty environment (`env -i`, only `PATH` and a fresh `HOME`), following
only the README.

| Run | Command | Result |
|---|---|---|
| Real Codex | `CODEX=<codex> python3 tests/codex_host_check.py` | **14/14** host checks, end-to-end **12/12** |
| Stand-in host (host-simulated) | `python3 tests/codex_host_check.py` (no Codex on PATH) | **9/9**, end-to-end **12/12** |
| Sample PDFs | `python3 plugins/spindoctor-qwerty/skills/spindoctor-qwerty/examples/theory/make_sample_pdfs.py` | 2 PDFs written |
| Zip | `python3 tools/build_zip.py` | reproducible (same SHA-256 on rebuild) |

Real-Codex host checks: marketplace.json fields; plugin.json + mcp.json vs Agent Plugins 1.0.0 schemas; vs 1.1.0 rules; same version in both
files; version/license/author/OpenAI interface; skill front matter; no hooks; mcp.json paths; `codex plugin marketplace add <repo>`;
`codex plugin add spindoctor-qwerty@spindoctor-qwerty-marketplace`; `codex plugin list` = installed, enabled, 1.1.0; `codex mcp get --json`
with `${PLUGIN_ROOT}`/`${PLUGIN_DATA}` expanded to the installed copy and cwd = plugin root; negative control (1.1.0 refused); end-to-end.

End-to-end (through Codex's app-server: `mcpServerStatus/list` for tools, `mcpServer/tool/call` for every call):

| Check | Result |
|---|---|
| initialize (server spindoctor-qwerty 1.1.0) | PASS |
| tools/list exposes the 6 tools | PASS |
| function table (Markdown, 19 sections, 298-qubit limits listed) | PASS |
| 241 presets listed | PASS |
| one script per command family (16 families, every table example) | PASS |
| 298-qubit circuit with mcx7 (prepared-factor Born-Z) | PASS |
| q.folder on a mixed .txt/.csv/.json/.qasm folder (+ .md skipped) | PASS |
| theory from a file -> supported, TXT+PDF report | PASS |
| theory from a chat summary + quoted excerpts -> supported | PASS |
| theory from an exported chat transcript -> supported | PASS |
| presets qc-001..qc-025 vs the updated 3.1.2 reference (20 identical, 5 documented differences) | PASS |
| TXT+PDF reports valid (255 PDFs, 255 TXT twins) | PASS |

Notes:
- The 5 documented preset differences are the engine's known, accepted ones (work-accounting counters), the same as in every published
  spindoctor-qwerty repo.
- Codex starts the server with only the plugin's own environment, so the reference seeds can't reach it. For the seeded preset comparison
  only, `tests/codex_mcp_bridge.py` creates that one fresh workspace with the seeds using the installed plugin's own engine (path from
  `codex mcp get --json`), then runs all 25 presets through Codex.
- Not tested: a model choosing the tools in a signed-in Codex session (needs an account), and the ChatGPT desktop app's Plugins Directory
  (no desktop app on the test machine).

## Post-push check

After publishing (commit 57d966001f9884910efd0dd27da64e99d9455045), the repo was cloned back from GitHub into a fresh folder:

- 57/57 files byte-identical to the staged copy.
- **Real Codex, straight from GitHub:** `codex plugin marketplace add LKVexa/spindoctor-qwerty-chatgpt-codex` +
  `codex plugin add spindoctor-qwerty@spindoctor-qwerty-marketplace` -> installed, enabled, 1.1.0; `codex mcp list` shows the server;
  end-to-end through Codex on that GitHub-installed copy **12/12**.
- From the clone, empty environment: `tests/codex_host_check.py` with real Codex **14/14** (end-to-end 12/12); stand-in host
  (host-simulated) **9/9** (end-to-end 12/12).
