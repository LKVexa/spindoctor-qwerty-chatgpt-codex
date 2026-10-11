# SpinDoctor Qwerty 1.1.0 - Codex host check
# Copyright (C) 2026 RUSSELL PHILIP SMITHSON <russellsmithson77@outlook.com>
# SPDX-License-Identifier: GPL-3.0-or-later
# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version. It is distributed WITHOUT ANY WARRANTY; see the LICENSE file for details.
"""Codex host check. Standard library only (Python 3.8+); no OpenAI account, no sign-in, no model calls.

1. Validates plugins/spindoctor-qwerty/plugin.json and mcp.json against the official Agent Plugins JSON schemas
   (tests/schemas/agent-plugins, Apache-2.0): exactly against 1.0.0 (the version the files declare and the version
   Codex supports), and against the 1.1.0 rules (same rules, only the $schema identifier differs). Also checks the
   OpenAI extension, .agents/plugins/marketplace.json (fields the Codex docs require), the skill, and that there are
   no hooks.
2. With the REAL Codex CLI (set CODEX=/path/to/codex or have `codex` on PATH), in a throw-away CODEX_HOME:
   `codex plugin marketplace add <repo>`, `codex plugin add spindoctor-qwerty@spindoctor-qwerty-marketplace`,
   `codex plugin list`, `codex mcp get --json` (PLUGIN_ROOT/PLUGIN_DATA expanded by Codex), a negative control (the
   same plugin declaring Agent Plugins 1.1.0 is refused by this Codex), then tests/e2e_mcp.py through
   tests/codex_mcp_bridge.py, so every tool call goes Codex app-server -> plugin MCP server.
3. Without Codex: stand-in host. Expands ${PLUGIN_ROOT}/${PLUGIN_DATA} in mcp.json the way the Agent Plugins spec
   and Codex do (cwd = plugin root), starts the server and runs tests/e2e_mcp.py (host-simulated).

usage: python3 tests/codex_host_check.py [REPO_DIR]"""
import json, os, re, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN_ID = "spindoctor-qwerty@spindoctor-qwerty-marketplace"


def validate(inst, schema, root=None, path="$"):
    """Small JSON Schema (2020-12) subset: everything the Agent Plugins schemas use."""
    root = root or schema; errs = []
    if "$ref" in schema:
        node = root
        for part in schema["$ref"].lstrip("#/").split("/"): node = node[part]
        return validate(inst, node, root, path)
    if "oneOf" in schema:
        n = sum(1 for s in schema["oneOf"] if not validate(inst, s, root, path))
        if n != 1: errs.append("%s: matches %d of oneOf" % (path, n))
    t = schema.get("type")
    types = {"object": dict, "array": list, "string": str, "boolean": bool}
    if t and not isinstance(inst, types[t]): return errs + ["%s: not %s" % (path, t)]
    if "const" in schema and inst != schema["const"]: errs.append("%s: must be %r" % (path, schema["const"]))
    if isinstance(inst, str):
        if len(inst) < schema.get("minLength", 0) or len(inst) > schema.get("maxLength", 10 ** 9): errs.append(path + ": length")
        if "pattern" in schema and not re.search(schema["pattern"], inst): errs.append(path + ": pattern")
    if isinstance(inst, list) and "items" in schema:
        for i, v in enumerate(inst): errs += validate(v, schema["items"], root, "%s[%d]" % (path, i))
    if isinstance(inst, dict):
        props = schema.get("properties", {})
        errs += ["%s: missing %s" % (path, k) for k in schema.get("required", []) if k not in inst]
        for k, v in inst.items():
            if "propertyNames" in schema and k in schema["propertyNames"].get("not", {}).get("enum", []): errs.append("%s: name %s not allowed" % (path, k))
            if k in props: errs += validate(v, props[k], root, path + "." + k)
            elif schema.get("additionalProperties") is False: errs.append("%s: unknown field %s" % (path, k))
            elif isinstance(schema.get("additionalProperties"), dict): errs += validate(v, schema["additionalProperties"], root, path + "." + k)
    return errs


def frontmatter(path):
    m = re.match(r"^---\n(.*?)\n---\n", open(path, encoding="utf-8").read(), re.S)
    return dict(re.findall(r"^([A-Za-z_-]+):\s*(.+)$", m.group(1), re.M)) if m else {}


def main():
    repo = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.dirname(HERE)
    ok = True; mode = "host-simulated"

    def T(name, cond, detail=""):
        nonlocal ok
        ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name + ("" if cond else "  -- " + str(detail)[:600])); sys.stdout.flush()

    load = lambda *p: json.load(open(os.path.join(*p), encoding="utf-8"))
    mk = load(repo, ".agents", "plugins", "marketplace.json")
    entry = next((p for p in mk.get("plugins", []) if p.get("name") == "spindoctor-qwerty"), {})
    src = entry.get("source", {}); spath = src.get("path") if isinstance(src, dict) else src
    T("marketplace.json: name, interface.displayName, entry with ./ local source, policy.installation/authentication, category",
      mk.get("name") == "spindoctor-qwerty-marketplace" and mk.get("interface", {}).get("displayName") and spath and spath.startswith("./")
      and ".." not in spath and entry.get("policy", {}).get("installation") in ("AVAILABLE", "INSTALLED_BY_DEFAULT", "NOT_AVAILABLE")
      and entry.get("policy", {}).get("authentication") and entry.get("category"), mk)
    root = os.path.realpath(os.path.join(repo, spath))
    pj = load(root, "plugin.json"); mj = load(root, "mcp.json")
    sch = os.path.join(HERE, "schemas", "agent-plugins")
    for ver in ("1.0.0", "1.1.0"):
        ps = load(sch, ver, "plugin.schema.json"); ms = load(sch, ver, "mcp.schema.json")
        p2 = dict(pj, **{"$schema": ps["properties"]["$schema"]["const"]}); m2 = dict(mj, **{"$schema": ms["properties"]["$schema"]["const"]})
        e = validate(pj if ver == "1.0.0" else p2, ps) + validate(mj if ver == "1.0.0" else m2, ms)
        T("plugin.json + mcp.json valid against Agent Plugins %s schemas%s" % (ver, "" if ver == "1.0.0" else " (rules; $schema identifier swapped)"), not e, e)
    T("plugin.json and mcp.json declare the same Agent Plugins version (1.0.0)", pj["$schema"].split("/")[-2] == mj["$schema"].split("/")[-2] == "1.0.0")
    oi = pj.get("extensions", {}).get("com.openai", {}).get("interface", {})
    T("plugin.json: version 1.1.0, GPL-3.0-or-later, author, OpenAI interface (displayName, descriptions, developerName, category, capabilities, defaultPrompt)",
      pj.get("version") == "1.1.0" and pj.get("license") == "GPL-3.0-or-later" and pj.get("author", {}).get("name") == "RUSSELL PHILIP SMITHSON"
      and all(oi.get(k) for k in ("displayName", "shortDescription", "longDescription", "developerName", "category", "capabilities", "defaultPrompt"))
      and not any(isinstance(v, str) and v.startswith(".") and not v.startswith("./") for v in oi.values()), pj)
    fm = frontmatter(os.path.join(root, "skills", "spindoctor-qwerty", "SKILL.md"))
    T("skill: name matches its folder, description present (<=1024 chars)", fm.get("name") == "spindoctor-qwerty" and 1 <= len(fm.get("description", "")) <= 1024, fm)
    T("no lifecycle hooks (hooks/hooks.json absent, no extensions.com.openai.hooks)", not os.path.exists(os.path.join(root, "hooks", "hooks.json")) and "hooks" not in pj.get("extensions", {}).get("com.openai", {}))
    srv = mj["mcpServers"]["spindoctor-qwerty"]
    T("mcp.json: one stdio server; script under ${PLUGIN_ROOT}; workspace under ${PLUGIN_DATA}", srv["type"] == "stdio" and srv["args"][0].startswith("${PLUGIN_ROOT}/")
      and os.path.isfile(srv["args"][0].replace("${PLUGIN_ROOT}", root)) and srv["env"]["SPINDOCTOR_WORKSPACE"].startswith("${PLUGIN_DATA}/"), srv)
    examples = os.path.join(root, "skills", "spindoctor-qwerty", "examples", "theory")
    e2e = [sys.executable, os.path.join(HERE, "e2e_mcp.py"), "--server"]
    tail = ["--examples", examples, "--out", os.path.join(tempfile.mkdtemp(prefix="sdq_cx_"), "e2e_results.json")]
    codex = os.environ.get("CODEX") or shutil.which("codex")
    if codex:
        mode = "real Codex"
        home = tempfile.mkdtemp(prefix="sdq_codex_home_")
        env = dict(os.environ, HOME=home, CODEX_HOME=os.path.join(home, ".codex")); os.makedirs(env["CODEX_HOME"])
        run = lambda *a, **k: subprocess.run([codex] + list(a), env=k.get("env", env), stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=180)
        v = run("--version").stdout.strip().splitlines()[-1]
        r = run("plugin", "marketplace", "add", repo)
        T("%s: codex plugin marketplace add <repo>" % v, r.returncode == 0 and "spindoctor-qwerty-marketplace" in r.stdout, r.stdout)
        r = run("plugin", "add", PLUGIN_ID)
        T("codex plugin add %s" % PLUGIN_ID, r.returncode == 0 and "Added plugin" in r.stdout, r.stdout)
        r = run("plugin", "list")
        T("codex plugin list: installed, enabled, 1.1.0", re.search(r"spindoctor-qwerty@spindoctor-qwerty-marketplace\s+installed, enabled\s+1\.1\.0", r.stdout), r.stdout)
        r = run("mcp", "get", "spindoctor-qwerty", "--json")
        try: g = json.loads(r.stdout[r.stdout.index("{"):])
        except ValueError: g = {}
        tr = g.get("transport", {}); pr = tr.get("env", {}).get("PLUGIN_ROOT", "")
        T("codex mcp get: enabled stdio server, ${PLUGIN_ROOT}/${PLUGIN_DATA} expanded to the installed copy, cwd = plugin root",
          g.get("enabled") and tr.get("type") == "stdio" and pr and tr.get("args", [""])[0] == pr + "/skills/spindoctor-qwerty/scripts/spindoctor_mcp.py"
          and tr.get("env", {}).get("SPINDOCTOR_WORKSPACE", "").startswith(tr["env"].get("PLUGIN_DATA", "?") + "/") and tr.get("cwd") == pr and "${" not in json.dumps(tr), g)
        neg = tempfile.mkdtemp(prefix="sdq_cx_neg_"); shutil.copytree(repo, os.path.join(neg, "m"), ignore=shutil.ignore_patterns(".git", "dist", "__pycache__"))
        for f in ("plugin.json", "mcp.json"):
            p = os.path.join(neg, "m", spath, f); t = open(p, encoding="utf-8").read().replace("/schemas/1.0.0/", "/schemas/1.1.0/"); open(p, "w", encoding="utf-8").write(t)
        nh = tempfile.mkdtemp(prefix="sdq_codex_neg_"); nenv = dict(env, HOME=nh, CODEX_HOME=os.path.join(nh, ".codex")); os.makedirs(nenv["CODEX_HOME"])
        run("plugin", "marketplace", "add", os.path.join(neg, "m"), env=nenv); r = run("plugin", "add", PLUGIN_ID, env=nenv)
        T("negative control: this Codex refuses the same plugin declaring Agent Plugins 1.1.0 (why the files declare 1.0.0)", r.returncode != 0 and "plugin.json" in r.stdout, r.stdout)
        os.environ.update(HOME=home, CODEX_HOME=env["CODEX_HOME"])
        r = subprocess.run(e2e + [sys.executable, os.path.join(HERE, "codex_mcp_bridge.py"), codex] + tail, cwd=home)
        T("end-to-end through the real Codex app-server (tools/list + every tool call via Codex)", r.returncode == 0)
    else:
        print("SKIP real Codex CLI not found (set CODEX=/path/to/codex); using the stand-in host")
        data = tempfile.mkdtemp(prefix="sdq_plugin_data_")
        sub = lambda s: s.replace("${PLUGIN_ROOT}", root).replace("${PLUGIN_DATA}", data)
        cmd = [os.environ.get("SPINDOCTOR_PYTHON") or sub(srv["command"])] + [sub(a) for a in srv.get("args", [])]
        env = dict(os.environ, **{k: sub(v) for k, v in srv.get("env", {}).items()}); env.update(PLUGIN_ROOT=root, PLUGIN_DATA=data)
        r = subprocess.run(e2e + cmd + tail, env=env, cwd=root)
        T("end-to-end through the server declared in mcp.json (stand-in host, host-simulated)", r.returncode == 0)
    print("HOST-CHECK (%s)" % mode, "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
