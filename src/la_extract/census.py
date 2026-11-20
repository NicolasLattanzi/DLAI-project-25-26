"""Censimento di tutti gli oggetti (blocchi 16x16) e delle entita' usati nelle stanze del gioco.

Produce (in locale, cartella ignorata da git):
  <out>/census/census.json           conteggi per regione, physics flag, nomi del disassembly, esempi
  <out>/census/atlas_<regione>_NN.png fogli di revisione: per ogni oggetto 3 esempi con contesto 3x3

Serve a costruire e rivedere a mano i file in mappings/.

Uso:  python -P src/la_extract/census.py [--rom ROM] [--ladxr DIR] [--out data/la_local]
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import ladx

DISASM = ladx.REPO_ROOT / "third_party" / "LADX-Disassembly"


def disasm_object_names():
    """Nomi OBJECT_* da src/constants/gfx.asm, separati per sezione (overworld / indoor / sidescroll)."""
    path = DISASM / "src" / "constants" / "gfx.asm"
    names = {"overworld": {}, "indoor": {}, "sidescroll": {}}
    if not path.exists():
        return names
    section = None
    for line in path.read_text(encoding="utf-8").splitlines():
        low = line.lower()
        if "overworld room objects" in low or "overworld macros" in low:
            section = "overworld"
        elif "indoor room objects" in low:
            section = "indoor"
        elif "sidescroll objects" in low:
            section = "sidescroll"
        elif low.startswith("; room header"):
            section = None
        m = re.match(r"DEF (OBJECT_\w+)\s+EQU \$([0-9A-Fa-f]{2})", line)
        if m and section:
            names[section].setdefault(int(m.group(2), 16), m.group(1))
    return names


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rom")
    ap.add_argument("--ladxr")
    ap.add_argument("--out", default=str(ladx.DEFAULT_OUT))
    ap.add_argument("--no-atlas", action="store_true")
    args = ap.parse_args()

    g = ladx.Game(args.rom, args.ladxr)
    out = Path(args.out) / "census"
    out.mkdir(parents=True, exist_ok=True)
    names = disasm_object_names()

    obj_count = defaultdict(Counter)          # region -> obj -> celle
    obj_rooms = defaultdict(lambda: defaultdict(set))
    obj_examples = defaultdict(lambda: defaultdict(list))  # region -> obj -> [(room, idx)]
    obj_maps = defaultdict(lambda: defaultdict(set))
    side_count = defaultdict(Counter)          # oggetti nelle stanze sidescroll (contati a parte)
    ent_count = Counter()
    ent_rooms = defaultdict(set)
    ent_regions = defaultdict(set)

    for room in ladx.all_room_ids():
        d = g.room(room)
        reg = d["region"]
        key_map = d["map_id"]
        for i, o in enumerate(d["objects"]):
            if d["sidescroll"]:
                side_count[reg][o] += 1
                continue
            obj_count[reg][o] += 1
            obj_rooms[reg][o].add(room)
            ex = obj_examples[reg][o]
            # al massimo 3 esempi, da mappe (interni) o zone (overworld: blocchi 4x4 di schermate) diverse
            zone = key_map if reg != "overworld" else ((room >> 4) // 4, (room & 0xF) // 4)
            if len(ex) < 3 and all(z != zone for _, _, z in ex):
                ex.append((room, i, zone))
            obj_maps[reg][o].add(key_map)
        for e in d["entities"]:
            ent_count[e["entity_id"]] += 1
            ent_rooms[e["entity_id"]].add(room)
            ent_regions[e["entity_id"]].add(reg)

    census = {"rom_sha1": g.rom_sha1, "regions": {}, "sidescroll_objects": {}, "entities": {}}
    for reg in ("overworld", "indoor", "color"):
        nm = names["overworld" if reg == "overworld" else "indoor"]
        census["regions"][reg] = {
            f"{o:02X}": {
                "cells": obj_count[reg][o],
                "rooms": len(obj_rooms[reg][o]),
                "physics": f"{g.physics[reg][o]:02X}",
                "disasm_name": nm.get(o),
                "examples": [f"{r:03X}@{i % 10},{i // 10}" for r, i, _ in obj_examples[reg][o]],
            }
            for o in sorted(obj_count[reg])
        }
        census["sidescroll_objects"][reg] = {f"{o:02X}": c for o, c in sorted(side_count[reg].items())}
    for t in sorted(ent_count):
        census["entities"][f"{t:02X}"] = {"name": g.entity_names[t], "count": ent_count[t],
                                          "rooms": len(ent_rooms[t]), "regions": sorted(ent_regions[t]),
                                          "example_rooms": [f"{r:03X}" for r in sorted(ent_rooms[t])[:5]]}
    with open(out / "census.json", "w", encoding="utf-8") as f:
        json.dump(census, f, indent=1)
    for reg in census["regions"]:
        print(reg, "oggetti distinti:", len(census["regions"][reg]))
    print("entita' distinte:", len(census["entities"]))

    if args.no_atlas:
        return
    from PIL import Image, ImageDraw
    S = 2            # scala
    CTX = 3 * 16 * S  # contesto 3x3 celle
    EW = 3 * (CTX + 2) + 4
    EH = CTX + 30
    COLS, ROWS = 4, 8
    for reg in ("overworld", "indoor", "color"):
        objs = sorted(obj_count[reg])
        nm = names["overworld" if reg == "overworld" else "indoor"]
        for sheet in range(0, len(objs), COLS * ROWS):
            chunk = objs[sheet:sheet + COLS * ROWS]
            img = Image.new("RGB", (COLS * EW, ROWS * EH), (255, 255, 255))
            dr = ImageDraw.Draw(img)
            for k, o in enumerate(chunk):
                ox, oy = (k % COLS) * EW, (k // COLS) * EH
                for j, (room, idx, _) in enumerate(obj_examples[reg][o]):
                    cx, cy = idx % 10, idx // 10
                    src = g.render(room)
                    pad = Image.new("RGB", (160 + 32, 128 + 32), (255, 255, 255))
                    pad.paste(src, (16, 16))
                    crop = pad.crop((cx * 16, cy * 16, cx * 16 + 48, cy * 16 + 48)).resize((CTX, CTX), Image.NEAREST)
                    px = ox + j * (CTX + 2)
                    img.paste(crop, (px, oy))
                    dr.rectangle([px + 16 * S, oy + 16 * S, px + 32 * S - 1, oy + 32 * S - 1], outline=(255, 0, 0))
                lab = f"{o:02X} ph={g.physics[reg][o]:02X} n={obj_count[reg][o]}"
                dr.text((ox + 2, oy + CTX + 2), lab, fill=(0, 0, 0))
                dr.text((ox + 2, oy + CTX + 14), (nm.get(o) or "")[7:], fill=(0, 0, 160))
            path = out / f"atlas_{reg}_{sheet // (COLS * ROWS):02d}.png"
            img.save(path)
            print("atlas:", path)


if __name__ == "__main__":
    main()
