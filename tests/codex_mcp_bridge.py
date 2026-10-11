# SpinDoctor Qwerty 1.1.0 - Codex app-server bridge for the end-to-end test
# Copyright (C) 2026 RUSSELL PHILIP SMITHSON <russellsmithson77@outlook.com>
# SPDX-License-Identifier: GPL-3.0-or-later
# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version. It is distributed WITHOUT ANY WARRANTY; see the LICENSE file for details.
"""Expose the SpinDoctor tools that the REAL Codex CLI loaded from this plugin as a plain MCP stdio server, so
tests/e2e_mcp.py can drive them through Codex.

Codex is started as `codex app-server` (its JSON-RPC interface, no sign-in needed for MCP inventory or tool calls).
tools/list -> Codex `mcpServerStatus/list`; tools/call -> Codex `mcpServer/tool/call` on an ephemeral thread.
So every call goes Codex -> plugin mcp.json (as Codex resolved it) -> bundled engine. No model is called.

Usage: python3 codex_mcp_bridge.py <codex-binary> [codex options such as -c key=value ...]
(CODEX_HOME must already have the plugin installed)
"""
import json, os, queue, subprocess, sys, tempfile, threading, time

SERVER = "spindoctor-qwerty"
WS = os.environ.get("SPINDOCTOR_WORKSPACE", "")


class Codex(object):
    def __init__(self, exe, extra=()):
        self.p = subprocess.Popen([exe] + list(extra) + ["app-server"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                  text=True, encoding="utf-8", bufsize=1)
        self.q = queue.Queue(); self.n = 0
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self):
        for line in self.p.stdout:
            try: m = json.loads(line)
            except ValueError: continue
            if "id" in m and ("result" in m or "error" in m): self.q.put(m)

    def call(self, method, params, timeout=1200):
        self.n += 1; i = self.n
        self.p.stdin.write(json.dumps({"jsonrpc": "2.0", "id": i, "method": method, "params": params}) + "\n"); self.p.stdin.flush()
        end = time.time() + timeout
        while time.time() < end:
            try: m = self.q.get(timeout=1)
            except queue.Empty:
                if self.p.poll() is not None: raise RuntimeError("codex app-server exited")
                continue
            if m.get("id") == i:
                if "error" in m: raise RuntimeError("codex %s: %s" % (method, m["error"]))
                return m["result"]
        raise RuntimeError("codex %s timed out" % method)

    def notify(self, method):
        self.p.stdin.write(json.dumps({"jsonrpc": "2.0", "method": method}) + "\n"); self.p.stdin.flush()


SEEDS = {k: os.environ[k] for k in ("SPINDOCTOR_MEASUREMENT_SEED", "SPINDOCTOR_FIELD_SEED") if os.environ.get(k)}


def seed_workspace(cfg):
    """Reproducible-run support for the harness: Codex only passes the plugin's own env to the server, so the
    reference seeds (which seed a NEW workspace only) can't travel with the tool call. Create that one workspace
    with the INSTALLED plugin's own CLI, exactly as Codex resolved it (`codex mcp get --json`); every tool call still
    goes through Codex."""
    if not SEEDS or not WS or os.path.exists(WS) or not cfg: return
    tr = cfg["transport"]; scripts = os.path.dirname(tr["args"][-1])
    env = dict(os.environ, **{k: v for k, v in tr.get("env", {}).items() if k != "SPINDOCTOR_WORKSPACE"}); env.update(SEEDS)
    code = "import sys; sys.path.insert(0, sys.argv[1]); from spindoctor import api; api._session(sys.argv[2]).save()"
    subprocess.run([tr["command"], "-c", code, os.path.dirname(scripts), WS], cwd=tr.get("cwd"), env=env,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)


def main():
    exe = sys.argv[1]; extra = sys.argv[2:]
    cx = Codex(exe, extra); thread = None; info = None
    exe_cfg = None
    if SEEDS and WS:
        exe_cfg = json.loads(subprocess.run([exe] + extra + ["mcp", "get", SERVER, "--json"], stdout=subprocess.PIPE,
                                            stderr=subprocess.DEVNULL, text=True, check=True).stdout)
    for line in sys.stdin:
        try: msg = json.loads(line)
        except ValueError: continue
        if "id" not in msg: continue
        mid, method, params = msg["id"], msg.get("method"), msg.get("params") or {}
        try:
            if method == "initialize":
                cx.call("initialize", {"clientInfo": {"name": "spindoctor-codex-bridge", "version": "1.1.0"}}); cx.notify("initialized")
                st = cx.call("mcpServerStatus/list", {"detail": "toolsAndAuthOnly", "serverName": SERVER})["data"]
                srv = [s for s in st if s.get("name") == SERVER]
                if not srv or not srv[0].get("tools"): raise RuntimeError("Codex did not load the %s MCP server: %s" % (SERVER, json.dumps(st)[:400]))
                info = srv[0]
                thread = cx.call("thread/start", {"ephemeral": True, "cwd": tempfile.gettempdir()})["thread"]["id"]
                si = info.get("serverInfo") or {}
                res = {"protocolVersion": params.get("protocolVersion", "2025-06-18"), "capabilities": {"tools": {}},
                       "serverInfo": {"name": si.get("name", SERVER), "version": si.get("version", "?")},
                       "_codex": {"pluginId": info.get("pluginId")}}
            elif method == "tools/list":
                res = {"tools": list(info["tools"].values())}
            elif method == "tools/call":
                args = dict(params.get("arguments") or {})
                # The harness picks a workspace per server instance through SPINDOCTOR_WORKSPACE. Codex launches the
                # server with the plugin's own env (mcp.json sets ${PLUGIN_DATA}/workspace), so pass the harness's
                # choice as the documented `workspace` tool argument instead.
                if WS and "workspace" not in args and params["name"] != "spindoctor_functions":
                    args["workspace"] = WS; seed_workspace(exe_cfg)
                params = dict(params, arguments=args)
                res = cx.call("mcpServer/tool/call", {"server": SERVER, "threadId": thread, "tool": params["name"], "arguments": params.get("arguments") or {}})
            elif method == "ping":
                res = {}
            else:
                raise RuntimeError("unsupported method " + str(method))
            out = {"jsonrpc": "2.0", "id": mid, "result": res}
        except Exception as e:
            out = {"jsonrpc": "2.0", "id": mid, "error": {"code": -32000, "message": str(e)}}
        sys.stdout.write(json.dumps(out) + "\n"); sys.stdout.flush()
    cx.p.kill()


if __name__ == "__main__":
    main()
