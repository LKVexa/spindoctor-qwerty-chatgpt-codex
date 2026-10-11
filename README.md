# SpinDoctor Qwerty for ChatGPT / Codex

**spindoctor-qwerty-chatgpt-codex** is a portable **Agent Plugins** package for OpenAI **Codex** (CLI, IDE extension and Codex in the
ChatGPT desktop app), laid out as a one-plugin **marketplace**. The plugin, `spindoctor-qwerty`, bundles the SpinDoctor Qwerty
quantum-circuit **simulator** as a local MCP server plus a skill. Codex can then build and run circuits with SpinDoctor's `q.*`
commands, run any of the 241 presets, process a folder of command files with `q.folder`, test a theory you give it, and write TXT,
PDF, JSON and CSV reports.

- Version **1.1.0**, engine at **SpinDoctor 3.1.2 parity** (update 3.1.2-298-20261010).
- Layout, as documented at <https://developers.openai.com/codex/plugins/build>:
  - `.agents/plugins/marketplace.json` - marketplace `spindoctor-qwerty-marketplace` with one entry (`./plugins/spindoctor-qwerty`).
  - `plugins/spindoctor-qwerty/plugin.json` - portable manifest (Agent Plugins `$schema`, OpenAI presentation under
    `extensions.com.openai.interface`, `license` and `author`).
  - `plugins/spindoctor-qwerty/mcp.json` - one stdio server: `python3 ${PLUGIN_ROOT}/skills/spindoctor-qwerty/scripts/spindoctor_mcp.py`,
    reports in `${PLUGIN_DATA}/workspace`.
  - `plugins/spindoctor-qwerty/skills/spindoctor-qwerty/` - `SKILL.md` and the bundled engine (`spindoctor/`, `scripts/`, `examples/`).
  - No hooks, no `.app.json`, no network access, no installs. The engine is pure Python (standard library only; NumPy is used if present).
- **Schema version:** the manifests declare Agent Plugins **1.0.0**. They also pass the newer **1.1.0** schema rules (1.1.0 is a
  working draft that only changes the version identifier), but the current Codex CLI (0.162.1) refuses a plugin that declares 1.1.0,
  and the spec says hosts must refuse versions they don't support. So 1.0.0 is the right declaration today. MCPB does not apply
  to Codex.

> **Honest limits.** SpinDoctor runs classical FP64 arithmetic on your computer. It is **not** a quantum computer, never contacts
> quantum hardware, and gives no quantum speed-up or quantum advantage. Registers hold 1-298 logical qubits, but any group of
> entangled qubits (one "factor") is limited to 59 qubits, and dense factors are limited much further by memory
> (2^n x 16 bytes; about 22 qubits with the standard library, more with NumPy). Registers wider than 29 qubits sample in basis Z only.
> Python 3.8 or newer is required (`python3` on PATH).

## Install

1. Install **Python 3.8+** (`python3` on PATH) and Codex (`npm install -g @openai/codex`, or the ChatGPT desktop app).
2. Add this repository as a marketplace and install the plugin:
   ```sh
   codex plugin marketplace add LKVexa/spindoctor-qwerty-chatgpt-codex
   codex plugin add spindoctor-qwerty@spindoctor-qwerty-marketplace
   ```
   Or clone it and use the local folder: `codex plugin marketplace add ./spindoctor-qwerty-chatgpt-codex`.
   In the ChatGPT desktop app (Codex), restart the app, open the **Plugins Directory**, choose **SpinDoctor Qwerty** and install it.
3. Check: `codex plugin list` shows `spindoctor-qwerty@spindoctor-qwerty-marketplace  installed, enabled  1.1.0`, and
   `codex mcp list` shows the `spindoctor-qwerty` server. Then ask *"show the SpinDoctor functions"*.

To enable or disable it for one project, add to that project's `.codex/config.toml`:
```toml
[plugins."spindoctor-qwerty@spindoctor-qwerty-marketplace"]
enabled = true
```

**Notes.**
- Codex copies the plugin to `~/.codex/plugins/cache/spindoctor-qwerty-marketplace/spindoctor-qwerty/1.1.0/` and expands `${PLUGIN_ROOT}`
  and `${PLUGIN_DATA}` (checked with Codex CLI 0.162.1). If an older Codex build does not start the server, add it by hand in
  `~/.codex/config.toml` with an absolute path to `skills/spindoctor-qwerty/scripts/spindoctor_mcp.py` (see openai/codex#22842).
- **Windows:** if `python3` is not available, change `"command"` in `plugins/spindoctor-qwerty/mcp.json` to `"python"` (or `"py"`) in your
  clone before adding the marketplace.
- Reports go to `${PLUGIN_DATA}/workspace/reports/` (Codex keeps it under `~/.codex/plugins/data/`). Tools also accept a `workspace` argument.
- **ChatGPT on the web** only installs plugins from the public directory or a workspace, and needs a remote HTTPS MCP server; this local
  stdio plugin is for Codex and the ChatGPT desktop app.
- **Zip:** `python3 tools/build_zip.py` writes `dist/spindoctor-qwerty-1.1.0.zip` (+ `.sha256`), a reproducible zip of the plugin folder
  to hand to someone who will unpack it into their own marketplace's `plugins/` folder. It is not committed (the GitHub connector used to
  publish this repo carries text files only).

## SpinDoctor Qwerty - plugin tools

| Function | What it does | Command to type |
|---|---|---|
| Function table (spindoctor_functions) | Show this table in chat | Ask: "show the SpinDoctor functions" (CLI: `spindoctor_cli.py functions`) |
| Run a script (spindoctor_run_script) | Run any q.* lines above; returns results + TXT/JSON/CSV/PDF report paths | Ask: "run q.circuit new bell 2 / q.circuit add h 0 / ..." |
| Run a preset (spindoctor_run_preset) | Run qc-001..qc-241 with overrides | Ask: "run preset qc-067 with shots=64" |
| List presets (spindoctor_list_presets) | Search the 241 presets | Ask: "list presets about Grover" |
| Read a report (spindoctor_report) | List/read TXT reports (PDF/JSON paths alongside) | Ask: "show the newest SpinDoctor report" |
| Test a theory from a file (spindoctor_test_theory source=file) | Read a .txt/.md/.pdf/.py/.json/.csv/.q attachment, then hypothesis -> prediction -> q.* script -> run -> verdict + TXT/PDF theory report | Ask: "test the theory in C:/notes/theory.md" (the host must pass the file path/content) |
| Test a theory from text (spindoctor_test_theory source=text) | Same pipeline for pasted text | Ask: "test this theory: a Hadamard on \|0> gives 50/50" |
| Test the theory we discussed (spindoctor_test_theory source=chat) | The AI summarises the theory from the conversation (claims, assumptions, variables, prediction), you confirm, then it is tested; quoted excerpts go in the report under 'Source: chat history'. An exported chat transcript (.txt/.md/.json/.html) also works | Ask: "test the theory we discussed" or "test the theory in my exported chat C:/chats/conversation.json" |

Every command family is listed with a runnable example in **[FUNCTIONS.md](FUNCTIONS.md)** (the exact table the tool shows):
circuits (`q.circuit`, including 298-qubit wide registers and the `mcx7` gate), queries (`q.query`), the tranche register
(`q.tranche`), the procedural grid, presets and sequences, resource planning, math calculators, physics models, lessons, noise, error
correction, compilation, algorithms, inputs/folders/history (`q.input`, `q.folder`, `q.history`) and the cartridge commands.

## Theory testing

`spindoctor_test_theory` turns a claim into a test: hypothesis -> measurable prediction -> `q.*` script -> run -> compare -> a TXT +
JSON + PDF **theory test report** with the hypothesis, script, raw results, verdict (*supported*, *not supported* or *inconclusive*)
and limits.

- **From a file:** .txt, .md, .pdf, .py, .json, .csv or .q. In Codex, give the file's path in the workspace. In ChatGPT, an uploaded file is seen by the model, not by the plugin: the model passes its text, or a path only if the file is on the computer where the plugin runs.
- **From pasted text.**
- **From the chat history:** say *"test the theory we discussed"*. The model writes a short summary (claims, assumptions, variables,
  measurable prediction), shows it to you to confirm or correct, then passes it with optional quoted excerpts; the report records them
  under *Source: chat history*. Exported chat transcripts (.txt/.md/.json/.html from ChatGPT, Claude and others) also work.
- The plugin cannot read your conversation or attachments by itself: only the model sees them, and very long conversations may already
  be truncated by the context window.

Sample theory files and chat transcripts are in `plugins/spindoctor-qwerty/skills/spindoctor-qwerty/examples/theory/`. The two sample
PDFs are stored as text; run `python3 plugins/spindoctor-qwerty/skills/spindoctor-qwerty/examples/theory/make_sample_pdfs.py` to
recreate them.

## Folder ingestion (`q.folder`)

`q.folder run path="<folder>"` runs every supported file at the top level of a folder (.txt, .csv, .json, .qasm, .qasm2, .circuit,
.pdf) in ordinal name order: 1-128 supported files, at most 4 MiB per file, 1-128 commands per file and 4096 characters per command,
strict UTF-8. Other files (for example .md) are skipped and listed. The first failing file stops the job.

## Testing

| Test | Command | Result for 1.1.0 |
|---|---|---|
| Host check with the **real Codex CLI** (manifests vs Agent Plugins 1.0.0 + 1.1.0 schemas, marketplace add, plugin add, list, mcp get, negative control, end-to-end through Codex) | `CODEX=$(command -v codex) python3 tests/codex_host_check.py` | 14/14 host checks, end-to-end 12/12 |
| Same without Codex (stand-in host, host-simulated) | `python3 tests/codex_host_check.py` | 9/9 checks, end-to-end 12/12 |
| Reproducible zip | `python3 tools/build_zip.py` (twice: same SHA-256) | 38 files (40 after `make_sample_pdfs.py`), identical hashes |

**Real host:** Codex CLI 0.162.1 was installed for free from npm on a Linux test machine and used **without signing in** and without calling
any model. It added this marketplace, installed the plugin, listed it as enabled, resolved `${PLUGIN_ROOT}`/`${PLUGIN_DATA}`, started the
MCP server and listed its 6 tools. `tests/codex_mcp_bridge.py` then drove every end-to-end tool call through Codex's own app-server
(`mcpServerStatus/list`, `mcpServer/tool/call`). One test-only step is outside Codex: Codex passes the server only the plugin's own
environment, so for the seeded preset comparison the bridge creates that one fresh workspace with the reference seeds using the installed
plugin's own engine, then runs the presets through Codex. Details in [E2E_RESULTS.md](E2E_RESULTS.md).

## Author and license

Author: **RUSSELL PHILIP SMITHSON** <russellsmithson77@outlook.com>

Copyright (C) 2026 RUSSELL PHILIP SMITHSON. Licensed under the GNU General Public License v3.0 or later (`GPL-3.0-or-later`): see
[LICENSE](LICENSE), [NOTICE](NOTICE) and [COPYRIGHT](COPYRIGHT). `plugin.json` carries `"license": "GPL-3.0-or-later"` and the author.
The Agent Plugins schemas under `tests/schemas/` are Apache-2.0 (see NOTICE). OpenAI, ChatGPT and Codex are trademarks of OpenAI; this
project is not affiliated with OpenAI.
