#!/usr/bin/env python3
"""Render learn-sanskrit clips — videofactory Fish stack, run TTS on opencode3.

model fish-audio/s2.1-pro-free · verse/granny frozen seats · sha1 cache · -21dB
Hub Rule 8: no local ffmpeg — ssh vps for Fish + normalize.
  python3 render_clips.py --dry-run
  python3 render_clips.py --limit 1
  python3 render_clips.py
"""
from __future__ import annotations
import argparse, base64, hashlib, json, os, shlex, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLAN = ROOT / "audio-plan.json"
OUT = ROOT / "audio" / "clips"
RECEIPTS = ROOT / "audio" / "receipts" / "calls.jsonl"
SSH_HOST = os.environ.get("BF_TTS_HOST", "vps")
REMOTE_PY = os.environ.get("BF_TTS_PY", "/usr/bin/python3")
REMOTE_DIR = os.environ.get("BF_TTS_DIR", "/tmp/learn-sanskrit-tts")
VOICES = {
    "verse": "4e873c37d4cb439e9bccc4dc1f633290",
    "granny": "614f8afd83f841048c040b2c6234d2c1",
}

def sha12(voice, text):
    return hashlib.sha1(f"{voice}|{text}".encode()).hexdigest()[:12]

def ssh_cmd(cmd, timeout=180):
    return subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", SSH_HOST, cmd],
        capture_output=True, text=True, timeout=timeout)

REMOTE_SCRIPT = """
import base64, json, os, re, subprocess, sys, urllib.request
key = None
for p in ["/home/ubuntu/.config/opencode/.env", os.path.expanduser("~/.config/opencode/.env")]:
    try:
        for line in open(p):
            if line.startswith("FISH_API_KEY="):
                key = line.split("=", 1)[1].strip()
                break
    except OSError:
        pass
    if key:
        break
assert key, "no FISH_API_KEY on remote"
text = base64.b64decode(sys.argv[1]).decode()
voice = sys.argv[2]
body = json.dumps({
    "model": "fish-audio/s2.1-pro-free",
    "input": text,
    "voice": voice,
    "response_format": "wav",
    "speed": 1.0,
}).encode()
req = urllib.request.Request(
    "https://api.fish.audio/compat/v1/audio/speech",
    data=body,
    headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
raw = urllib.request.urlopen(req, timeout=120).read()
open("/tmp/fish_raw.wav", "wb").write(raw)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "/tmp/fish_raw.wav",
                "-ar", "44100", "-ac", "1", "/tmp/fish_out.wav"], check=True)
r = subprocess.run(["ffmpeg", "-nostats", "-v", "info", "-i", "/tmp/fish_out.wav",
                    "-af", "volumedetect", "-f", "null", "-"],
                   capture_output=True, text=True)
me = re.search(r"mean_volume: ([\\-\\d.]+) dB", r.stderr)
mx = re.search(r"max_volume: ([\\-\\d.]+) dB", r.stderr)
g = 0.0
if me and mx:
    g = max(-12.0, min(12.0, min(-21.0 - float(me.group(1)), -1.5 - float(mx.group(1)))))
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "/tmp/fish_out.wav",
                "-af", "volume=%.1fdB" % g, "/tmp/fish_norm.wav"], check=True)
d = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                    "-of", "default=nw=1:nk=1", "/tmp/fish_norm.wav"],
                   capture_output=True, text=True).stdout.strip()
print(json.dumps({"ok": True, "dur": d, "gain_db": round(g, 1)}))
"""

def tts_remote(text, voice, dest, speed=1.0):
    ssh_cmd(f"mkdir -p {shlex.quote(REMOTE_DIR)}")
    b64 = base64.b64encode(text.encode()).decode()
    up = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", SSH_HOST,
         f"cat > {REMOTE_DIR}/tts_one.py"],
        input=REMOTE_SCRIPT, capture_output=True, text=True, timeout=30)
    if up.returncode != 0:
        return {"ok": False, "error": f"upload: {up.stderr[-300:]}"}
    run = ssh_cmd(
        f"cd {shlex.quote(REMOTE_DIR)} && {REMOTE_PY} tts_one.py {shlex.quote(b64)} {shlex.quote(voice)}",
        timeout=180)
    if run.returncode != 0:
        return {"ok": False, "error": (run.stderr or run.stdout)[-400:]}
    try:
        meta = json.loads(run.stdout.strip().splitlines()[-1])
    except Exception:
        return {"ok": False, "error": f"bad remote: {run.stdout[-300:]}"}
    dest.parent.mkdir(parents=True, exist_ok=True)
    scp = subprocess.run(
        ["scp", "-o", "BatchMode=yes", f"{SSH_HOST}:{REMOTE_DIR}/fish_norm.wav", str(dest)],
        capture_output=True, text=True, timeout=60)
    if scp.returncode != 0:
        return {"ok": False, "error": f"scp: {scp.stderr[-300:]}"}
    sha = hashlib.sha256(dest.read_bytes()).hexdigest()[:16]
    return {"ok": True, "file": str(dest), "voice": voice, "chars": len(text),
            "sha": sha, "dur": meta.get("dur"), "gain_db": meta.get("gain_db"),
            "src": "fish", "model": "fish-audio/s2.1-pro-free",
            "cache_key": sha12(voice, text)}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    plan = json.loads(PLAN.read_text())
    entries = plan.get("entries") or []
    RECEIPTS.parent.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    n_new = n_cached = 0
    log = None if args.dry_run else open(RECEIPTS, "a", encoding="utf-8")
    try:
        for e in entries:
            for kind in ("verse", "howto"):
                clip = e.get(kind) or {}
                text, voice_id = clip.get("text"), clip.get("voice_id")
                if not text or not voice_id:
                    continue
                h = sha12(voice_id, text)
                dest = OUT / f"{e[chr(39)+chr(39)] if False else e[\"id\"]}__{kind}_{h}.wav"
                # fix f-string - use e["id"] properly below
                dest = OUT / (e["id"] + "__" + kind + "_" + h + ".wav")
                if dest.is_file() and dest.stat().st_size > 1000 and not args.force:
                    n_cached += 1
                    print("cached", dest.name)
                    continue
                if args.dry_run:
                    n_new += 1
                    print("RENDER", dest.name, kind, len(text), "ch", h)
                    continue
                print("render", dest.name, kind, "...", flush=True)
                rec = tts_remote(text, voice_id, dest)
                rec.update({"entry": e["id"], "kind": kind, "cache_key": h})
                if log:
                    log.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    log.flush()
                if not rec.get("ok"):
                    print("FAIL", dest.name, rec.get("error"), flush=True)
                    return 1
                n_new += 1
                if args.limit and n_new >= args.limit:
                    print("limit", args.limit, "reached")
                    return 0
    finally:
        if log:
            log.close()
    print(f"done: {n_new} rendered, {n_cached} cached")
    return 0

if __name__ == "__main__":
    sys.exit(main())
