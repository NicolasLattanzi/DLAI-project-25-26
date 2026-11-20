"""Fogli di revisione visiva: ogni stanza con la grafica originale e sopra la codifica per categorie.

Sovrapposizione (griglia finale, con entita'): muro grigio, fuori mappa nero, acqua/buche blu, ponte marrone
chiaro, porta rossa (D), blocco marrone (B), scale verdi (E), giocatore azzurro (P), nemico magenta (M);
il pavimento resta scoperto. Etichetta: id stanza, V = valida / X = scartata.

Output (solo locale): <out>/review/<gruppo>_NN.png
Uso:  python src/la_extract/review_sheets.py [--rooms data/la_local/rooms] [--cols 8] [--rows 8] [--scale 1]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw

TINT = {0: ((0, 0, 0), 200), 1: ((60, 60, 70), 165), 3: ((30, 90, 255), 130), 4: ((200, 130, 40), 150),
        5: ((230, 20, 20), 190), 7: ((150, 80, 20), 170), 8: ((20, 220, 80), 190), 9: ((0, 200, 255), 210),
        10: ((255, 0, 210), 190), 6: ((255, 220, 0), 200)}
LETTER = {5: "D", 7: "B", 8: "E", 9: "P", 10: "M", 6: "K", 4: "="}


def overlay(orig: Image.Image, grid, scale=1):
    base = orig.convert("RGBA")
    ov = Image.new("RGBA", base.size, (0, 0, 0, 0))
    dr = ImageDraw.Draw(ov)
    for y in range(8):
        for x in range(10):
            c = grid[y][x]
            if c in TINT:
                col, a = TINT[c]
                dr.rectangle([x * 16, y * 16, x * 16 + 15, y * 16 + 15], fill=col + (a,))
            if c == 1:  # muro: tratteggio per distinguerlo dalla grafica scura
                dr.line([x * 16, y * 16 + 15, x * 16 + 15, y * 16], fill=(200, 200, 200, 160))
            if c in LETTER:
                dr.text((x * 16 + 5, y * 16 + 2), LETTER[c], fill=(255, 255, 255, 255))
    img = Image.alpha_composite(base, ov).convert("RGB")
    if scale != 1:
        img = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rooms", default="data/la_local/rooms")
    ap.add_argument("--out")
    ap.add_argument("--cols", type=int, default=8)
    ap.add_argument("--rows", type=int, default=8)
    ap.add_argument("--scale", type=int, default=1)
    ap.add_argument("--group", help="solo questo gruppo (es. dungeons/D1_tail_cave)")
    args = ap.parse_args()
    root = Path(args.rooms)
    out = Path(args.out) if args.out else root.parent / "review"
    out.mkdir(parents=True, exist_ok=True)
    idx = json.load(open(root / "index.json", encoding="utf-8"))["rooms"]
    groups = {}
    for it in idx:
        if args.group and it["group"] != args.group:
            continue
        groups.setdefault(it["group"], []).append(it)
    TW, TH = 160 * args.scale + 4, 128 * args.scale + 14
    for gname, items in groups.items():
        items.sort(key=lambda it: it["room_id"])
        per = args.cols * args.rows
        for s in range(0, len(items), per):
            chunk = items[s:s + per]
            rows = (len(chunk) + args.cols - 1) // args.cols
            sheet = Image.new("RGB", (args.cols * TW, rows * TH), (255, 255, 255))
            dr = ImageDraw.Draw(sheet)
            for k, it in enumerate(chunk):
                rd = root / it["path"]
                room = json.load(open(rd / "room.json", encoding="utf-8"))
                img = overlay(Image.open(rd / "original.png"), room["grid"], args.scale)
                ox, oy = (k % args.cols) * TW, (k // args.cols) * TH
                sheet.paste(img, (ox, oy + 12))
                tag = "V" if it["valid"] else "X " + ",".join(r.replace("special:", "") for r in it["discard_reasons"])[:22]
                dr.text((ox + 1, oy), f"{it['room_id']} {tag}", fill=(0, 120, 0) if it["valid"] else (200, 0, 0))
            name = gname.replace("/", "_") + f"_{s // per:02d}.png"
            sheet.save(out / name)
            print(out / name)


if __name__ == "__main__":
    main()
