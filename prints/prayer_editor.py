#!/usr/bin/env python3
"""
prayer_editor.py — Interactive editor for prayer card specs.

Allows you to:
- Edit devanagari/english text
- Change font sizes (DEV_SD, EN_SE)
- Add/remove stanzas
- Save and render

Run: python3 prints/prayer_editor.py
"""
import json, os, sys
from pathlib import Path

# --- Default values ---
DEV_SD_DEFAULT = 70      # Devanagari font size (points)
EN_SE_DEFAULT = 52       # English font size (points)
INK_DEFAULT = (23, 20, 15)

ROOT = Path(__file__).parent.parent
PRAYERS_DIR = ROOT / "prints" / "prayers"
SPECS = sorted(PRAYERS_DIR.glob("*.json"))

def load_spec(name):
    path = PRAYERS_DIR / name
    return path.read_text(), path

def parse_stanzas(text):
    return json.loads(text)

def save_spec(spec, path):
    path.write_text(json.dumps(spec, indent=2, ensure_ascii=False))

def print_stanza(i, st):
    print(f"\nStanza {i+1}:")
    print(f"  Dev lines ({len(st['dev'])}):")
    for j, d in enumerate(st["dev"]):
        print(f"    {j+1}: {d}")
    print(f"  En lines ({len(st['en'])}):")
    for j, e in enumerate(st["en"]):
        print(f"    {j+1}: {e}")

def edit_line(prompt, current=""):
    print(f"  [{prompt}] (current: {current or '(empty)'})")
    new = input("  Enter new value (or press enter to keep): ").strip()
    return new if new else current

def edit_spec(spec):
    print("\n=== Edit Prayer Spec ===")
    
    # Edit ID
    spec["id"] = edit_line("ID", spec.get("id", ""))
    
    # Edit title
    spec["title"] = edit_line("Title", spec.get("title", ""))
    
    # Edit source
    spec["source"] = edit_line("Source", spec.get("source", ""))
    
    # Edit font sizes
    spec["dev_sd"] = int(edit_line("Dev font size (pt)", spec.get("dev_sd", 70)))
    spec["en_se"] = int(edit_line("Eng font size (pt)", spec.get("en_se", 52)))
    
    # Edit stanzas
    n = int(edit_line("Number of stanzas", len(spec.get("stanzas", []))))
    
    # Ensure we have right number of stanzas
    while len(spec["stanzas"]) < n:
        spec["stanzas"].append({"dev": [], "en": []})
    while len(spec["stanzas"]) > n:
        spec["stanzas"].pop()
    
    for i in range(n):
        print_stanza(i, spec["stanzas"][i])
        
        # Edit dev lines
        dev_count = int(edit_line(f"Dev lines count for stanza {i+1}", len(spec["stanzas"][i]["dev"])))
        while len(spec["stanzas"][i]["dev"]) < dev_count:
            spec["stanzas"][i]["dev"].append(edit_line(f"Dev line {len(spec['stanzas'][i]['dev'])+1}"))
        while len(spec["stanzas"][i]["dev"]) > dev_count:
            spec["stanzas"][i]["dev"].pop()
        
        # Edit en lines
        en_count = int(edit_line(f"English lines count for stanza {i+1}", len(spec["stanzas"][i]["en"])))
        while len(spec["stanzas"][i]["en"]) < en_count:
            spec["stanzas"][i]["en"].append(edit_line(f"Eng line {len(spec['stanzas'][i]['en'])+1}"))
        while len(spec["stanzas"][i]["en"]) > en_count:
            spec["stanzas"][i]["en"].pop()
    
    return spec

def main():
    print("=== Prayer Card Editor ===")
    print(f"\nAvailable specs ({len(SPECS)}):")
    for i, p in enumerate(SPECS):
        print(f"  {i+1}: {p.name}")
    
    print("  0: Create new spec")
    
    choice = input("\nSelect spec number: ").strip()
    
    if choice == "0":
        # Create new
        name = input("Enter spec filename (e.g. myprayer.json): ").strip()
        if not name.endswith(".json"):
            name += ".json"
        spec = {"id": name.replace(".json", ""), "title": name, "source": "edited via editor", "stanzas": [{"dev": [], "en": []}]}
        PRAYERS_DIR.mkdir(parents=True, exist_ok=True)
        path = PRAYERS_DIR / name
        path.write_text(json.dumps(spec, indent=2, ensure_ascii=False))
        print(f"Created {path}")
        spec = load_spec(name)[1]
    else:
        idx = int(choice) - 1
        if 0 <= idx < len(SPECS):
            text, path = SPECS[idx]
            spec = parse_stanzas(text)
        else:
            print("Invalid choice")
            return
    
    # Edit spec
    spec = edit_spec(spec)
    
    # Save
    save_spec(spec, path)
    print(f"\nSaved to {path}")
    
    # Render?
    render = input("\nRender now? (y/n): ").strip().lower()
    if render == "y":
        # Run engine
        os.system(f"python3 {ROOT}/prints/prayer_engine.py {path}")
    
    print("\nDone!")

if __name__ == "__main__":
    main()