#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import subprocess
import pathlib
import stat
import sys

SCRIPT_DIR = pathlib.Path("/shared")

PORT = 2000

print("Searching for handlers in", SCRIPT_DIR)

processes = []
for script in SCRIPT_DIR.iterdir():
    print("Found file", script)
    mode = script.stat().st_mode
    if not (stat.S_ISREG(mode) and mode & stat.S_IXUSR):
        continue

    print("Starting", script, "on port", PORT)

    processes.append(subprocess.Popen([
        "socat",
        f"OPENSSL-LISTEN:{PORT},fork=1,cert=/cert.pem,verify=0,key=/privkey.pem",
        "EXEC:" + str(script)
    ]))
    PORT += 1

print("Waiting for handlers")
sys.stdout.flush()
for p in processes:
    p.wait()
print("All closed!")
