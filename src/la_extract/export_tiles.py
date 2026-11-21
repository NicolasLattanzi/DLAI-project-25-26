"""
export_tiles.py - salva su disco le tile 16x16 di tutto il gioco, una per ogni ID oggetto.

Legge le stanze gia' estratte (data/la_local/rooms: original.png + room.json) e, per ogni
coppia (tileset, ID oggetto), ritaglia le celle 16x16 e le salva come PNG.

Output (default data/la_local/tiles/):
  index.json            tutte le tile: file, nome, categoria, simbolo ASCII, conteggi, varianti
  context_stats.json    statistiche "categoria + vicinato -> ID" per passare da ASCII a ID
                        (usate da src/testing/tile_library.py, non servono per usare gli ID diretti)
  <gruppo>/<ID>.png     la tile piu' frequente di quell'ID in quel tileset (es. overworld/37.png)
  <gruppo>/<ID>_v2.png  eventuali varianti (stesso ID con palette diversa), dalla piu' alla meno frequente
  <gruppo>/sidescroll/  tile delle stanze a scorrimento laterale: stessi ID ma significato diverso
  _atlas/<gruppo>.png   foglio con tutte le tile del gruppo e il loro ID, per consultazione

Il "gruppo" e' il tileset: overworld, dungeons/D1_tail_cave ... D0_color_dungeon, indoor/house, ...
Lo stesso ID in gruppi diversi e' un'immagine diversa: per questo le tile sono divise per gruppo.

Uso (dalla radice del repository):
    python src/la_extract/export_tiles.py
    python src/la_extract/export_tiles.py --out /percorso/tiles --exclude 000 101   # per test
"""
from __future__ import annotations

import argparse
import json
import shutil
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
ROOMS_DIR = ROOT / "data" / "la_local" / "rooms"
MAPPINGS = ROOT / "src" / "la_extract" / "mappings"

CELL = 16
ROWS, COLS = 8, 10
CAT_TO_SYMBOL = {0: " ", 1: "#", 2: ".", 3: "~", 4: "=", 5: "D", 6: "K", 7: "B", 8: "E", 9: "P", 10: "M"}
OUTSIDE = "@"  # simbolo usato per "fuori schermo" nelle chiavi di contesto
MAX_ROOMS_PER_VARIANT = 12


def load_names() -> dict[str, dict[str, dict]]:
    """region -> id -> voce di mapping (nome, categoria, ...)."""
    ow = json.load(open(MAPPINGS / "objects_overworld.json", encoding="utf-8"))["objects"]
    indoor = json.load(open(MAPPINGS / "objects_indoor.json", encoding="utf-8"))
    color = dict(indoor["objects"])
    color.update({k: v for k, v in indoor["color_dungeon_overrides"].items() if not k.startswith("_")})
    return {"overworld": ow, "indoor": indoor["objects"], "color": color}


def ctx9(cats: list[list[int]], y: int, x: int) -> str:
    """Centro + 8 vicini (N, E, S, O, NO, NE, SE, SO) come stringa di simboli ASCII."""
    out = [CAT_TO_SYMBOL[cats[y][x]]]
    for dy, dx in ((-1, 0), (0, 1), (1, 0), (0, -1), (-1, -1), (-1, 1), (1, 1), (1, -1)):
        yy, xx = y + dy, x + dx
        out.append(CAT_TO_SYMBOL[cats[yy][xx]] if 0 <= yy < ROWS and 0 <= xx < COLS else OUTSIDE)
    return "".join(out)


def collect(rooms_dir: Path, exclude: set[str]):
    """Passa su tutte le stanze. Ritorna (tiles, stats, regions)."""
    # tiles[gruppo][id][bytes] = {"img", "count", "rooms": set}
    tiles: dict[str, dict[str, dict[bytes, dict]]] = defaultdict(lambda: defaultdict(dict))
    cats_seen: dict[str, dict[str, Counter]] = defaultdict(lambda: defaultdict(Counter))
    stats: dict[str, dict[str, Counter]] = defaultdict(lambda: defaultdict(Counter))
    region_of: dict[str, str] = {}
    index = json.load(open(rooms_dir / "index.json", encoding="utf-8"))["rooms"]
    for e in index:
        if e["room_id"] in exclude:
            continue
        folder = rooms_dir / e["path"]
        room = json.load(open(folder / "room.json", encoding="utf-8"))
        img = Image.open(folder / "original.png").convert("RGB")
        side = bool(room["sidescroll"])
        group = e["group"] + ("/sidescroll" if side else "")
        region_of[group] = room["region"]
        ids, cats = room["objects"], room["grid_tiles"]
        use_ctx = e["valid"] and not side  # statistiche ASCII->ID solo da stanze buone
        for y in range(ROWS):
            for x in range(COLS):
                oid = str(ids[y][x]).upper().zfill(2)
                crop = img.crop((x * CELL, y * CELL, (x + 1) * CELL, (y + 1) * CELL))
                slot = tiles[group][oid].setdefault(crop.tobytes(), {"img": crop, "count": 0, "rooms": set()})
                slot["count"] += 1
                slot["rooms"].add(e["room_id"])
                if not side:
                    cats_seen[group][oid][cats[y][x]] += 1
                    if use_ctx:
                        stats[group][ctx9(cats, y, x)][oid] += 1
    return tiles, cats_seen, stats, region_of


def atlas(group: str, entries: list[tuple[str, Image.Image]], path: Path, scale: int = 3, per_row: int = 12) -> None:
    font = ImageFont.load_default()
    cw, ch = CELL * scale + 8, CELL * scale + 18
    rows = (len(entries) + per_row - 1) // per_row
    sheet = Image.new("RGB", (per_row * cw + 8, rows * ch + 24), (245, 245, 245))
    d = ImageDraw.Draw(sheet)
    d.text((6, 6), group, fill=(0, 0, 0), font=font)
    for i, (oid, im) in enumerate(entries):
        x, y = 8 + (i % per_row) * cw, 24 + (i // per_row) * ch
        sheet.paste(im.resize((CELL * scale, CELL * scale), Image.NEAREST), (x, y))
        d.text((x, y + CELL * scale + 3), oid, fill=(0, 0, 0), font=font)
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(path)


def export(rooms_dir: Path, out: Path, exclude: set[str], clean: bool = True) -> dict:
    if clean and out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)
    names = load_names()
    tiles, cats_seen, stats, region_of = collect(rooms_dir, exclude)

    index = {"schema": "la_tiles/1", "tile_size": CELL,
             "description": "Tile 16x16 di Link's Awakening DX per (gruppo/tileset, ID oggetto). "
                            "file = tile piu' frequente; variants = tutte le versioni (palette diverse).",
             "groups": {}}
    for group in sorted(tiles):
        region = region_of[group]
        mapping = names["color" if region == "color" else region if region in names else "indoor"]
        side = group.endswith("/sidescroll")
        entries_for_atlas = []
        gentry = {}
        for oid in sorted(tiles[group]):
            variants = sorted(tiles[group][oid].values(), key=lambda v: -v["count"])
            vlist = []
            for n, v in enumerate(variants, start=1):
                fname = f"{group}/{oid}.png" if n == 1 else f"{group}/{oid}_v{n}.png"
                p = out / fname
                p.parent.mkdir(parents=True, exist_ok=True)
                v["img"].save(p)
                vlist.append({"file": fname, "count": v["count"],
                              "rooms": sorted(v["rooms"])[:MAX_ROOMS_PER_VARIANT]})
            entries_for_atlas.append((oid, variants[0]["img"]))
            info = {"file": vlist[0]["file"], "count": sum(v["count"] for v in variants), "variants": vlist}
            if not side:  # nelle stanze 2D gli ID hanno un altro significato: niente nome/categoria
                m = mapping.get(oid, {})
                cat = (cats_seen[group][oid].most_common(1) or [(m.get("category"), 0)])[0][0]
                info.update({"name": m.get("name"), "category": cat,
                             "symbol": CAT_TO_SYMBOL.get(cat) if cat is not None else None})
            gentry[oid] = info
        index["groups"][group] = {"region": region, "family": group.split("/")[0],
                                  "sidescroll": side, "tiles": gentry}
        atlas(group, entries_for_atlas, out / "_atlas" / (group.replace("/", "__") + ".png"))

    # statistiche categoria+vicinato -> ID (chiave = 9 simboli: centro + 8 vicini)
    json.dump({"schema": "la_tiles_context/1", "outside": OUTSIDE,
               "neighbour_order": "N E S O NO NE SE SO",
               "groups": {g: {k: dict(c) for k, c in d.items()} for g, d in stats.items()}},
              open(out / "context_stats.json", "w", encoding="utf-8"), separators=(",", ":"))
    json.dump(index, open(out / "index.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    return index


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rooms-dir", type=Path, default=ROOMS_DIR)
    ap.add_argument("--out", type=Path, default=ROOT / "data" / "la_local" / "tiles")
    ap.add_argument("--exclude", nargs="*", default=[], help="room_id da non usare (per valutazioni)")
    args = ap.parse_args()
    index = export(args.rooms_dir, args.out, set(args.exclude))
    n_tiles = sum(len(g["tiles"]) for g in index["groups"].values())
    n_files = sum(len(t["variants"]) for g in index["groups"].values() for t in g["tiles"].values())
    print(f"{len(index['groups'])} gruppi, {n_tiles} tile (ID), {n_files} immagini -> {args.out}")


if __name__ == "__main__":
    main()
