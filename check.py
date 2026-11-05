#!/usr/bin/env python3
"""check.py — the bookfactory gate. exit 0 = canonical, else failing lane named."""
import json, os, re, sys

VISUALS = "/home/box/visuals/prints"
UPSTREAM = "/home/box/repos/translation-work"
CEILING = 110            # KDP flat tier; prayer books target 108


def load(p):
    with open(p) as f:
        return json.load(f)


def fail(lane, msg):
    print(f"[FAIL] {lane}: {msg}")
    return 1


def check_lane(name, lane, reg):
    errs = 0
    book_dir = lane.get("book_dir")
    if book_dir:
        bd = os.path.join(VISUALS, book_dir)
        ent_p = os.path.join(bd, "entries.json")
        if not os.path.exists(ent_p):
            return fail(name, f"missing {ent_p}")
        entries = load(ent_p)
        if not entries:
            return fail(name, "entries.json empty")
        ids = [e.get("id") for e in entries]
        if len(ids) != len(set(ids)):
            errs += fail(name, "duplicate entry ids")
        for e in entries:
            sp = e.get("source_path", "")
            if not sp:
                errs += fail(name, f"{e['id']}: no source_path"); continue
            fp = os.path.join(bd, sp)
            if not os.path.exists(fp):
                errs += fail(name, f"{e['id']}: source file missing: {sp}"); continue
            ref = e.get("source_ref", "")
            if ref and fp.endswith(".md"):
                txt = open(fp, errors="ignore").read()
                cands = [ref] + re.findall(r"\d+\.\d+|\d+|bh-p\d+|anu-p\d+|vbt-p\d+|\w+-p\d+|\w+-\d+", ref)
                if not any(c in txt for c in cands):
                    errs += fail(name, f"{e['id']}: ref {ref!r} not found in {sp}")
            if not (e.get("iast") or e.get("corpus")):
                errs += fail(name, f"{e['id']}: no iast and no corpus ref")
            for f_ in ("brief", "en"):
                if not e.get(f_):
                    errs += fail(name, f"{e['id']}: empty {f_}")
            for f_ in ("what", "how", "sign"):
                if not (e.get(f_) or e.get({"what": "logic", "how": "howto", "sign": ""}[f_])):
                    errs += fail(name, f"{e['id']}: explainer block {f_} empty")
        # page ceiling (cheap: from a shipped preview pdf via pdfinfo if present)
        for pdfn in (f"{book_dir}-preview.pdf", "preview.pdf"):
            p = os.path.join(bd, pdfn)
            if os.path.exists(p):
                import subprocess
                out = subprocess.run(["pdfinfo", p], capture_output=True, text=True).stdout
                m = re.search(r"Pages:\s+(\d+)", out)
                if m and int(m.group(1)) > CEILING:
                    errs += fail(name, f"preview {pdfn} is {m.group(1)}pp > ceiling {CEILING}")
                break
    # upstream presence for queued lanes
    for t in lane.get("upstream_texts", []) or ([lane["text"]] if lane.get("text") else []):
        if not os.path.isdir(os.path.join(UPSTREAM, t)):
            errs += fail(name, f"upstream text dir missing: {t}")
    if not errs:
        stage = reg.get("lanes", {}).get(name, {}).get("stage", "?")
        print(f"[PASS] {name} ({stage})")
    return errs


def main():
    reg = load(os.path.join(os.path.dirname(os.path.abspath(__file__)), "REGISTRY.json"))
    lanes = reg.get("lanes", {})
    total = 0
    only = sys.argv[1] if len(sys.argv) > 1 else None
    for name in lanes:
        if only and name != only:
            continue
        lp = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "projects", name, "lane.py")
        if os.path.exists(lp):
            ns = {}
            exec(open(lp).read(), ns)          # lane declares, core reads
            lane = ns.get("LANE", {})
        else:
            errs = fail(name, "no projects/%s/lane.py — lanes declare, core never guesses" % name)
            total += errs
            continue
        total += check_lane(name, lane, reg)
    if only and only not in lanes:
        total += fail(only, "not in REGISTRY lanes")
    print(f"{'FAIL' if total else 'OK'} — {total} problem(s)")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
