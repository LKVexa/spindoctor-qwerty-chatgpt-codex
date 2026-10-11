# SpinDoctor Qwerty 1.1.0 - plugin zip builder
# Copyright (C) 2026 RUSSELL PHILIP SMITHSON <russellsmithson77@outlook.com>
# SPDX-License-Identifier: GPL-3.0-or-later
# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version. It is distributed WITHOUT ANY WARRANTY; see the LICENSE file for details.
"""Build dist/spindoctor-qwerty-<version>.zip: the plugin folder (plugins/spindoctor-qwerty) as a reproducible zip
(sorted entries, fixed timestamps, no __pycache__), plus its SHA-256. Use it to hand the plugin to someone who will
unpack it into their own marketplace's plugins/ folder. Standard library only.

  python3 tools/build_zip.py
"""
import hashlib, json, os, sys, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN = os.path.join(ROOT, "plugins", "spindoctor-qwerty")


def build(out_dir=os.path.join(ROOT, "dist")):
    version = json.load(open(os.path.join(PLUGIN, "plugin.json"), encoding="utf-8"))["version"]
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "spindoctor-qwerty-%s.zip" % version)
    files = []
    for root, dirs, fs in os.walk(PLUGIN):
        dirs[:] = sorted(d for d in dirs if d != "__pycache__")
        for f in sorted(fs):
            if f.endswith((".pyc", ".pyo")): continue
            files.append(os.path.join(root, f))
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for p in files:
            arc = "spindoctor-qwerty/" + os.path.relpath(p, PLUGIN).replace(os.sep, "/")
            zi = zipfile.ZipInfo(arc, date_time=(2026, 10, 10, 0, 0, 0))
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = (0o755 if p.endswith(".py") and "/scripts/" in p.replace(os.sep, "/") else 0o644) << 16
            z.writestr(zi, open(p, "rb").read())
    h = hashlib.sha256(open(out, "rb").read()).hexdigest()
    open(out + ".sha256", "w", newline="\n").write("%s  %s\n" % (h, os.path.basename(out)))
    return out, h, len(files)


if __name__ == "__main__":
    out, h, n = build(*(sys.argv[1:2]))
    print("%s (%d files)\nsha256 %s" % (out, n, h))
