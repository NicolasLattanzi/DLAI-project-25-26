"""Estrae TUTTE le stanze di Link's Awakening DX dalla ROM e le converte nelle categorie LevelEdit.

Per ogni stanza crea una cartella con:
  room.json     metadati, griglia finale/grezza, oggetti originali, entita', warp, correzioni, validita'
  original.png  la stanza con la grafica del gioco (160x128, SOLO uso locale)
  mapped.png    la griglia finale con i colori/simboli delle categorie (160x128)
Per ogni gruppo (overworld, ogni dungeon, ogni tipo di interno):
  group.json, overview_original.png, overview_mapped.png
In radice:
  index.json, dataset.npz (tutte le griglie), report.json, report.md

Struttura:
  <out>/overworld/room_XXX/
  <out>/dungeons/D1_tail_cave/room_XXX/ ... D8, D9_windfishs_egg, D0_color_dungeon
  <out>/indoor/<tipo>/room_XXX/           (case, caverne, negozi, ...)

Uso:
  python src/la_extract/extract_rooms.py [--rom ROM] [--ladxr DIR] [--out data/la_local/rooms] [--clean] [--no-images]
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ladx  # noqa: E402
from validate import H, W, fix_and_validate  # noqa: E402

SCHEMA = "leveledit_la_room/1"


# ----------------------------------------------------------------------------- mapping
class Mapper:
    def __init__(self, maps_file: str = "maps.json"):
        self.cats = ladx.load_json("categories.json")
        self.cat_by_code = {c["code"]: c for c in self.cats["categories"]}
        self.ascii = {c["code"]: c["ascii"] for c in self.cats["categories"]}
        self.ow = ladx.load_json("objects_overworld.json")["objects"]
        ind = ladx.load_json("objects_indoor.json")
        self.ind = ind["objects"]
        self.color_ovr = {k: v for k, v in ind["color_dungeon_overrides"].items() if not k.startswith("_")}
        self.ents = ladx.load_json("entities.json")["entities"]
        self.maps = ladx.load_json(maps_file)
        self.policy = {k: v for k, v in self.cats["special_policy"].items() if not k.startswith("_")}
        self.validity = dict(self.cats["validity"])
        self.validity["traversable"] = [c["code"] for c in self.cats["categories"] if c["traversable"] is True]
        self.validity["bfs_traversable"] = self.validity["traversable"] + (
            [10] if self.validity.get("bfs_enemies_passable") else [])
        fb = {}
        for k, v in self.cats["physics_fallback"].items():
            if k.startswith("_") or k == "default":
                continue
            a, _, b = k.partition("-")
            for p in range(int(a, 16), int(b or a, 16) + 1):
                fb[p] = v
        self.phys_fb = fb
        self.phys_default = self.cats["physics_fallback"]["default"]

    def obj(self, region, obj_id):
        k = f"{obj_id:02X}"
        if region == "color" and k in self.color_ovr:
            return self.color_ovr[k]
        table = self.ow if region == "overworld" else self.ind
        return table.get(k)

    def group_of(self, d):
        if d["region"] == "overworld":
            return self.maps["overworld"]["folder"], self.maps["overworld"]["name"]
        m = self.maps["maps"].get(f"{d['map_id']:02X}") if d["map_id"] is not None else None
        if m is None:
            return "indoor/unknown", "Unknown"
        return m["folder"], m["name"]


def _retry(fn, path: Path, tries=8):
    """Scrittura atomica con retry: le cartelle sincronizzate (OneDrive) bloccano i file per qualche istante."""
    tmp = path.with_name(path.name + ".tmp")
    for k in range(tries):
        try:
            fn(tmp)
            os.replace(tmp, path)
            return
        except OSError:
            if k == tries - 1:
                raise
            time.sleep(0.25 * (k + 1))


def save_png(img, path: Path):
    _retry(lambda p: img.save(p, format="PNG"), path)


def save_json(obj, path: Path, indent=1):
    def w(p):
        with open(p, "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=indent, ensure_ascii=False)
    _retry(w, path)


def exterior_to_void(grid, pit_like, traversable):
    """Stanze piu' piccole dello schermo: lo spazio attorno e' disegnato con il blocco 'buca'.
    Ogni regione 4-connessa di celle buca/vuoto che tocca il bordo dello schermo e che NON e'
    adiacente a nessuna cella attraversabile diventa 'fuori mappa' (0). Modifica grid in place.
    Ritorna il numero di celle convertite."""
    trav = set(traversable)
    seen = [[False] * W for _ in range(H)]
    changed = 0
    for sy in range(H):
        for sx in range(W):
            if seen[sy][sx] or not pit_like[sy][sx]:
                continue
            comp, stack, touches_border, touches_trav = [], [(sx, sy)], False, False
            seen[sy][sx] = True
            while stack:
                x, y = stack.pop()
                comp.append((x, y))
                touches_border |= x in (0, W - 1) or y in (0, H - 1)
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if not (0 <= nx < W and 0 <= ny < H):
                        continue
                    if grid[ny][nx] in trav:
                        touches_trav = True
                    if pit_like[ny][nx] and not seen[ny][nx]:
                        seen[ny][nx] = True
                        stack.append((nx, ny))
            if touches_border and not touches_trav:
                for x, y in comp:
                    if grid[y][x] != 0:
                        grid[y][x] = 0
                        changed += 1
    return changed


FLOOD_PASSABLE = {2, 3, 4, 5, 6, 7, 8}  # tutto tranne muro e fuori mappa (acqua/buche/blocchi/porte inclusi)
EDGE = {"left": (lambda x, y: x == 0, lambda x, y: (W - 1, y)),
        "right": (lambda x, y: x == W - 1, lambda x, y: (0, y)),
        "up": (lambda x, y: y == 0, lambda x, y: (x, H - 1)),
        "down": (lambda x, y: y == H - 1, lambda x, y: (x, 0))}


def exterior_masks(g, data, convs, apply_maps=None):
    """Analisi di connettivita' tra stanze (solo interni, stanze non a scorrimento laterale).

    Si parte dai punti in cui il gioco fa comparire Link (arrivi dei warp) e si visita ogni cella
    non-muro, passando da una stanza all'altra attraverso i bordi con la stessa regola del gioco
    (ladx.Game.neighbors). Acqua, buche, blocchi e porte sono attraversati di proposito: cosi' isole e
    zone dietro ostacoli restano 'raggiungibili' e non vengono toccate.
    Le regioni di pavimento/acqua NON raggiunte e che toccano il bordo dello schermo sono l'esterno
    della stanza (roccia, riempimento): diventano 'fuori mappa'.
    Ritorna (masks, info): masks[room] = set di celle da azzerare; info[room] = dict di diagnostica."""
    from collections import deque
    rooms = {r for r, d in data.items() if d["region"] != "overworld" and not d["sidescroll"]}

    def passable(r, x, y):
        c = convs[r]
        return c["grid_tiles"][y][x] in FLOOD_PASSABLE or c["flood_extra"][y][x]

    reached = {r: set() for r in rooms}
    q = deque()
    for r in rooms:
        for ax, ay in convs[r]["arrival_cells"]:
            best = None
            for y in range(H):
                for x in range(W):
                    dd = abs(x - ax) + abs(y - ay)
                    if dd <= 2 and passable(r, x, y) and (best is None or (dd, y, x) < best[0]):
                        best = ((dd, y, x), (x, y))
            if best and best[1] not in reached[r]:
                reached[r].add(best[1])
                q.append((r, best[1][0], best[1][1]))
    while q:
        r, x, y = q.popleft()
        for dname, (dx, dy) in (("left", (-1, 0)), ("right", (1, 0)), ("up", (0, -1)), ("down", (0, 1))):
            nx, ny = x + dx, y + dy
            if 0 <= nx < W and 0 <= ny < H:
                if (nx, ny) not in reached[r] and passable(r, nx, ny):
                    reached[r].add((nx, ny))
                    q.append((r, nx, ny))
                continue
            if convs[r]["warp_exit"][y][x]:
                continue  # uscita verso l'esterno: il gioco fa un warp, non passa alla stanza adiacente
            for nr in g.neighbors(r, data[r]["map_id"], dname):
                if nr not in rooms or data[nr]["map_id"] != data[r]["map_id"]:
                    continue
                tx, ty = EDGE[dname][1](x, y)
                if (tx, ty) not in reached[nr] and passable(nr, tx, ty):
                    reached[nr].add((tx, ty))
                    q.append((nr, tx, ty))

    masks, info = {}, {}
    for r in rooms:
        info[r] = {"reached_cells": len(reached[r])}
        if not reached[r]:
            continue
        if apply_maps is not None and (data[r]["map_id"] is None or f"{data[r]['map_id']:02X}" not in apply_maps):
            continue
        grid = convs[r]["grid_tiles"]
        cand = {(x, y) for y in range(H) for x in range(W)
                if (x, y) not in reached[r] and grid[y][x] in (2, 3, 4) and not convs[r]["passage"][y][x]}
        mask = set()
        while cand:
            start = cand.pop()
            comp, stack = {start}, [start]
            while stack:
                x, y = stack.pop()
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    n = (x + dx, y + dy)
                    if n in cand:
                        cand.discard(n)
                        comp.add(n)
                        stack.append(n)
            if any(x in (0, W - 1) or y in (0, H - 1) for x, y in comp):
                mask |= comp
        if mask:
            masks[r] = mask
            info[r]["exterior_cells"] = len(mask)
    return masks, info


def arrival_cell(tx, ty):
    """Coordinate pixel di arrivo di un warp -> cella (convenzione LADXR: x*16+8, y*16+16)."""
    cx = int((tx - 8) / 16 + 0.5)
    cy = int((ty - 16) / 16 + 0.5)
    return min(max(cx, 0), W - 1), min(max(cy, 0), H - 1)


# ----------------------------------------------------------------------------- conversione
def convert_room(g, mp: Mapper, d, arrivals_px, void_mask=None):
    region = d["region"]
    tiles, passage, specials, unmapped, tag_count = [], [], [], [], Counter()
    pit_like = [[False] * W for _ in range(H)]
    flood_extra = [[False] * W for _ in range(H)]
    warp_exit = [[False] * W for _ in range(H)]
    extra_tags = set(mp.cats.get("exterior", {}).get("flood_extra_tags", []))
    for i, o in enumerate(d["objects"]):
        e = mp.obj(region, o)
        x, y = i % W, i // W
        if e is None:
            ph = d["physics"][i]
            cat = mp.phys_fb.get(ph, mp.phys_default)
            unmapped.append({"x": x, "y": y, "object": f"{o:02X}", "physics": f"{ph:02X}", "fallback_category": cat})
            tiles.append(cat)
            passage.append(False)
            continue
        tiles.append(e["category"])
        passage.append(bool(e.get("passage")))
        pit_like[y][x] = e["category"] == 0 or "pit" in e.get("tags", [])
        flood_extra[y][x] = bool(extra_tags & set(e.get("tags", []))) or bool(e.get("passage"))
        # porte che portano fuori con un warp (non verso la stanza adiacente)
        warp_exit[y][x] = bool({"exit_door", "dungeon_entrance"} & set(e.get("tags", [])))
        for t in e.get("tags", []):
            tag_count[t] += 1
        if e.get("special"):
            specials.append({"x": x, "y": y, "special": e["special"], "source": "object", "object": f"{o:02X}",
                             "name": e["name"]})
    grid_tiles = [tiles[r * W:(r + 1) * W] for r in range(H)]
    pass_grid = [passage[r * W:(r + 1) * W] for r in range(H)]
    exterior = exterior_to_void(grid_tiles, pit_like, mp.validity["traversable"])
    unreachable = 0
    for x, y in (void_mask or ()):
        if grid_tiles[y][x] != 0:
            grid_tiles[y][x] = 0
            unreachable += 1
    grid = [row[:] for row in grid_tiles]

    # entita'
    ents_out, key_sources = [], []
    allowed_enemy = set(mp.validity["enemy_overrides_only"])
    allowed_obj = set(mp.validity["object_entity_overrides_only"])
    for e in d["entities"]:
        info = mp.ents[f"{e['entity_id']:02X}"]
        rec = {"x": e["x"], "y": e["y"], "entity_id": f"{e['entity_id']:02X}", "name": e["name"],
               "class": info["class"], "placed_as": None}
        if info.get("special"):
            specials.append({"x": e["x"], "y": e["y"], "special": info["special"], "source": "entity",
                             "name": e["name"]})
        if info["class"] == "key_source":
            key_sources.append({"type": "entity", "name": e["name"], "x": e["x"], "y": e["y"]})
        cat = info["category"]
        if cat is not None:
            x, y = e["x"], e["y"]
            if not (0 <= x < W and 0 <= y < H):
                rec["skipped"] = "fuori griglia"
            else:
                here = grid[y][x]
                ok = allowed_enemy if cat == 10 else allowed_obj
                if here in ok:
                    grid[y][x] = cat
                    rec["placed_as"] = cat
                elif here == cat:
                    rec["placed_as"] = cat
                    rec["note"] = "cella gia' occupata dalla stessa categoria"
                else:
                    rec["skipped"] = f"cella '{mp.cat_by_code[here]['id']}' non sovrascrivibile"
        ents_out.append(rec)

    # forzieri
    chest_cells = [(i % W, i // W) for i, o in enumerate(d["objects"])
                   if region != "overworld" and o in (0xA0, 0xA1)]
    chest = None
    if chest_cells:
        item = g.chest_item(d["room_id"])
        chest = {"item": item, "cells": [list(c) for c in chest_cells]}
        if item and (item.startswith("KEY") or item.startswith("NIGHTMARE_KEY")):
            key_sources.append({"type": "chest", "name": item, "x": chest_cells[0][0], "y": chest_cells[0][1]})

    arrivals = [arrival_cell(a["x_px"], a["y_px"]) for a in arrivals_px]
    return {
        "grid_tiles": grid_tiles, "grid_raw": grid, "passage": pass_grid, "specials": specials,
        "unmapped": unmapped, "entities": ents_out, "key_sources": key_sources, "chest": chest,
        "arrival_cells": arrivals, "tags": dict(tag_count), "exterior_void": exterior,
        "unreachable_void": unreachable, "flood_extra": flood_extra,
        "warp_exit": warp_exit,
    }


def classify(d, conv, mp: Mapper):
    """Motivi di scarto 'strutturali' (prima delle regole di validita') e segnalazioni."""
    reasons, flags = [], []
    if d["sidescroll"]:
        reasons.append("sidescroll")
    if d["num_objects"] == 0 and not d["entities"] and not d["warps"] and d["region"] != "overworld":
        reasons.append("empty_room")
    if conv["unmapped"] and not d["sidescroll"]:
        reasons.append("special:unmapped")
    for s in sorted({s["special"] for s in conv["specials"]}):
        pol = mp.policy.get(s, "flag")
        (reasons if pol == "discard" else flags).append(f"special:{s}")
    return reasons, flags


# ----------------------------------------------------------------------------- immagini
def draw_mapped(grid, mp: Mapper, scale=1, invalid=False):
    from PIL import Image, ImageDraw
    c = 16 * scale
    img = Image.new("RGB", (W * c, H * c), (0, 0, 0))
    dr = ImageDraw.Draw(img)
    for y in range(H):
        for x in range(W):
            code = grid[y][x]
            col = tuple(mp.cat_by_code[code]["color"])
            dr.rectangle([x * c, y * c, x * c + c - 1, y * c + c - 1], fill=col)
            sym = mp.ascii[code]
            if sym.strip():
                lum = 0.299 * col[0] + 0.587 * col[1] + 0.114 * col[2]
                dr.text((x * c + c // 2 - 3, y * c + c // 2 - 6), sym, fill=(0, 0, 0) if lum > 140 else (255, 255, 255))
    if invalid:
        dr.rectangle([0, 0, W * c - 1, H * c - 1], outline=(255, 0, 0), width=max(1, scale))
    return img


def overview(rooms, positions, tiles, label=True):
    """Mosaico: positions[room] = (col, row); tiles[room] = immagine 160x128."""
    from PIL import Image, ImageDraw
    cols = max(p[0] for p in positions.values()) + 1
    rows = max(p[1] for p in positions.values()) + 1
    TW, TH = 161, 129
    img = Image.new("RGB", (cols * TW, rows * TH), (40, 40, 40))
    dr = ImageDraw.Draw(img)
    for r in rooms:
        cx, cy = positions[r]
        img.paste(tiles[r], (cx * TW, cy * TH))
        if label:
            dr.rectangle([cx * TW, cy * TH, cx * TW + 22, cy * TH + 10], fill=(0, 0, 0))
            dr.text((cx * TW + 2, cy * TH), f"{r:03X}", fill=(255, 255, 255))
    return img


# ----------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rom")
    ap.add_argument("--ladxr")
    ap.add_argument("--out", default=str(ladx.DEFAULT_OUT / "rooms"))
    ap.add_argument("--clean", action="store_true", help="svuota la cartella di output (solo se creata da questo script)")
    ap.add_argument("--no-images", action="store_true")
    ap.add_argument("--only", help="solo questi gruppi (es. 'dungeons/D1_tail_cave,overworld')")
    ap.add_argument("--allow-modified-rom", action="store_true",
                    help="accetta una ROM modificata costruita sulla v1.0 (es. LADX-Zelda1); lo sha1 resta in index.json")
    ap.add_argument("--maps", default="maps.json",
                    help="file in mappings/ con nomi e cartelle dei gruppi (es. maps_zelda1.json)")
    ap.add_argument("--reference",
                    help="cartella rooms/ di un'estrazione precedente (es. data/la_local/rooms): ogni stanza con gli "
                         "stessi oggetti della stanza con lo stesso id viene segnata same_as_reference=true")
    args = ap.parse_args()

    t0 = time.time()
    out = Path(args.out)
    if args.clean and out.exists():
        if not (out / "index.json").exists():
            sys.exit(f"{out} non sembra un output di questo script (manca index.json): non la svuoto")
        for k in range(5):
            shutil.rmtree(out, ignore_errors=True)
            if not out.exists():
                break
            time.sleep(0.5)
        if out.exists():
            print(f"attenzione: impossibile svuotare del tutto {out} (file in uso?): sovrascrivo")
    out.mkdir(parents=True, exist_ok=True)

    ref_objects, ref_map = {}, {}
    if args.reference:
        ref = Path(args.reference)
        for e in json.load(open(ref / "index.json", encoding="utf-8"))["rooms"]:
            rj = json.load(open(ref / e["path"] / "room.json", encoding="utf-8"))
            ref_objects[e["room_id"]] = (e["region"] == "overworld", [v for row in rj["objects"] for v in row])
            if rj.get("map_id") is not None:
                ref_map[int(e["room_id"], 16)] = int(rj["map_id"], 16)
    g = ladx.Game(args.rom, args.ladxr, allow_modified=args.allow_modified_rom, map_id_fallback=ref_map)
    mp = Mapper(args.maps)
    only = set(args.only.split(",")) if args.only else None

    data = {r: g.room(r) for r in ladx.all_room_ids()}
    arrivals = defaultdict(list)
    for r, d in data.items():
        for w in d["warps"]:
            arrivals[w["target_room"]].append({"from_room": f"{r:03X}", "x_px": w["target_x"], "y_px": w["target_y"]})

    # passo 1: conversione grezza di tutte le stanze -> analisi di connettivita' tra stanze
    convs0 = {r: convert_room(g, mp, d, arrivals.get(r, [])) for r, d in data.items()}
    masks, conn_info = exterior_masks(g, data, convs0, set(mp.cats.get("exterior", {}).get("apply_to_maps", [])))

    index, groups = [], defaultdict(list)
    npz = defaultdict(list)
    reason_count, flag_count = Counter(), Counter()
    for r, d in data.items():
        folder, gname = mp.group_of(d)
        if only and folder not in only:
            continue
        conv = convert_room(g, mp, d, arrivals.get(r, []), void_mask=masks.get(r))
        pre_reasons, flags = classify(d, conv, mp)
        res = fix_and_validate(conv["grid_raw"], conv["passage"], conv["arrival_cells"], mp.validity)
        grid, fixes = res["grid"], res["fixes"]
        reasons = pre_reasons + [v for v in res["reasons"] if v not in pre_reasons]
        valid = not reasons
        notes = list(res["notes"])
        # stessa griglia senza giocatore e nemici: al loro posto il tile del layout originale
        grid_noent = [[conv["grid_tiles"][y][x] if grid[y][x] in (9, 10) else grid[y][x] for x in range(W)]
                      for y in range(H)]
        if flags:
            notes.append("segnalazioni: " + ", ".join(flags))
        for e in conv["entities"]:
            if e.get("skipped"):
                notes.append(f"entita' {e['name']} in ({e['x']},{e['y']}) non messa in griglia: {e['skipped']}")
        if conv["unreachable_void"]:
            notes.append(f"{conv['unreachable_void']} celle fuori dai muri della stanza, mai raggiungibili nel gioco "
                         "(analisi di connettivita' tra stanze) -> fuori mappa")
        if (r in conn_info and conn_info[r]["reached_cells"] == 0 and not d["sidescroll"]
                and d["map_id"] is not None and f"{d['map_id']:02X}" in mp.cats.get("exterior", {}).get("apply_to_maps", [])):
            notes.append("stanza non raggiunta dall'analisi di connettivita' (es. si entra cadendo dall'alto): layout lasciato invariato")
        if conv["exterior_void"]:
            notes.append(f"{conv['exterior_void']} celle di buca attorno a una stanza piu' piccola dello schermo -> fuori mappa")
        if conv["unmapped"]:
            notes.append(f"{len(conv['unmapped'])} celle con oggetti non mappati (fallback da physics)")
        rid = f"{r:03X}"
        rel = f"{folder}/room_{rid}"
        rdir = out / rel
        rdir.mkdir(parents=True, exist_ok=True)

        objects_hex = [[f"{o:02X}" for o in d["objects"][y * W:(y + 1) * W]] for y in range(H)]
        same_as_ref, ref_near, ref_diff = None, None, None
        if args.reference:
            # stanza di riferimento piu' simile (stessa regione overworld/interni), per trovare copie e quasi-copie
            flat = [v for row in objects_hex for v in row]
            is_ow = d["region"] == "overworld"
            ref_diff, ref_near = min((sum(a != b for a, b in zip(flat, objs)), k)
                                     for k, (ow, objs) in ref_objects.items() if ow == is_ow)
            same_as_ref = ref_diff == 0
            if same_as_ref:
                notes.append(f"stessi oggetti della stanza {ref_near} di {args.reference}: non e' una stanza nuova")
            elif ref_diff <= 3:
                notes.append(f"quasi uguale alla stanza {ref_near} di {args.reference} ({ref_diff} celle diverse)")
        if r in g.map_id_from_fallback:
            notes.append("mappa non deducibile dai warp di questa ROM: presa dalla stessa stanza dell'estrazione di riferimento")
        ascii_rows = ["".join(mp.ascii[c] for c in row) for row in grid]
        ascii_noent = ["".join(mp.ascii[c] for c in row) for row in grid_noent]
        cat_counts = Counter(c for row in grid for c in row)
        room = {
            "schema": SCHEMA,
            "room_id": rid,
            "region": d["region"],
            "group": folder,
            "group_name": gname,
            "map_id": None if d["map_id"] is None else f"{d['map_id']:02X}",
            "position": {
                "table": d["table_pos"],
                "layout": d["layout_pos"],
                "_doc": "table = posizione nella mappa 16x16 (overworld o tabella interni A/B); layout = posizione nella minimappa 8x8 del dungeon",
            },
            "sidescroll": d["sidescroll"],
            "same_as_reference": same_as_ref,
            "reference_nearest": ref_near,
            "reference_min_diff": ref_diff,
            "valid": valid,
            "discard_reasons": reasons,
            "notes": notes,
            "grid_ascii": ascii_rows,
            "grid_no_entities_ascii": ascii_noent,
            "_grids_doc": "grid = layout originale 1:1 + nemici (M) + giocatore (P, nel punto d'ingresso); "
                          "grid_no_entities = stessa griglia senza giocatore e nemici; grid_raw = tile + entita' prima di P/E; "
                          "grid_tiles = solo i tile del gioco",
            "fixes": fixes,
            "openings": res["openings"],
            "doors": res["doors"],
            "brief_checks": res["brief_checks"],
            "brief_valid": bool(valid and res["brief_checks"]["all_ok"]),
            "grid": grid,
            "grid_no_entities": grid_noent,
            "grid_raw": conv["grid_raw"],
            "grid_tiles": conv["grid_tiles"],
            "objects": objects_hex,
            "physics": [[f"{p:02X}" for p in d["physics"][y * W:(y + 1) * W]] for y in range(H)],
            "passage": conv["passage"],
            "specials": conv["specials"],
            "unmapped": conv["unmapped"],
            "entities": conv["entities"],
            "key_sources": conv["key_sources"],
            "chest": conv["chest"],
            "warps": [{**w, "target_room": f"{w['target_room']:03X}", "map_id": f"{w['map_id']:02X}"} for w in d["warps"]],
            "arrivals": [{**a, "cell": list(c)} for a, c in zip(arrivals.get(r, []), conv["arrival_cells"])],
            "stats": {
                "category_counts": {mp.cat_by_code[k]["id"]: v for k, v in sorted(cat_counts.items())},
                "num_room_objects": d["num_objects"],
                "num_entities": len(d["entities"]),
                "num_enemies": cat_counts.get(10, 0),
                "tags": conv["tags"],
            },
            "render": {"animation_id": d["animation_id"], "floor_object": f"{d['floor_object']:02X}"},
            "images": None if args.no_images else {"original": "original.png", "mapped": "mapped.png"},
        }
        save_json(room, rdir / "room.json")

        index.append({"room_id": rid, "region": d["region"], "group": folder, "path": rel, "valid": valid,
                      "discard_reasons": reasons, "flags": flags, "num_enemies": cat_counts.get(10, 0),
                      "fixes": [fx["type"] for fx in fixes], "openings": len(res["openings"]),
                      "brief_valid": bool(valid and res["brief_checks"]["all_ok"]),
                      "brief_checks": res["brief_checks"],
                      "table_pos": d["table_pos"], "layout_pos": d["layout_pos"],
                      "same_as_reference": same_as_ref, "reference_nearest": ref_near,
                      "reference_min_diff": ref_diff})
        groups[folder].append((r, d, grid, valid))
        for k in reasons:
            reason_count[k] += 1
        for k in flags:
            flag_count[k] += 1
        npz["grid"].append(grid)
        npz["grid_no_entities"].append(grid_noent)
        npz["grid_raw"].append(conv["grid_raw"])
        npz["grid_tiles"].append(conv["grid_tiles"])
        npz["objects"].append([d["objects"][y * W:(y + 1) * W] for y in range(H)])
        npz["room_id"].append(r)
        npz["region"].append(d["region"])
        npz["group"].append(folder)
        npz["map_id"].append(-1 if d["map_id"] is None else d["map_id"])
        npz["table_x"].append(d["table_pos"]["x"])
        npz["table_y"].append(d["table_pos"]["y"])
        lp = d["layout_pos"] or {"layout": -1, "x": -1, "y": -1}
        npz["layout"].append(lp["layout"])
        npz["layout_x"].append(lp["x"])
        npz["layout_y"].append(lp["y"])
        npz["valid"].append(valid)
        npz["brief_valid"].append(bool(valid and res["brief_checks"]["all_ok"]))
        npz["notes"].append(" | ".join(reasons + notes))
        npz["same_as_reference"].append(bool(same_as_ref))
        npz["reference_min_diff"].append(-1 if ref_diff is None else ref_diff)

        if not args.no_images:
            save_png(g.render(r), rdir / "original.png")
            save_png(draw_mapped(grid, mp), rdir / "mapped.png")

    # --- gruppi: json + mosaici ----------------------------------------------------------
    for folder, items in groups.items():
        gdir = out / folder
        rooms = [it[0] for it in items]
        pos = {}
        if folder.startswith("dungeons/"):
            extra = 0
            for r, d, _, _ in items:
                if d["layout_pos"]:
                    pos[r] = (d["layout_pos"]["x"], d["layout_pos"]["y"])
            for r, d, _, _ in sorted(items):
                if r not in pos:
                    pos[r] = (extra % 8, 8 + extra // 8)
                    extra += 1
        else:
            # posizione nella tabella 16x16; le stanze della tabella interni B vanno a destra di quelle della A
            raw = {r: (d["table_pos"]["x"] + (17 if 0x200 <= r < 0x300 else 0), d["table_pos"]["y"])
                   for r, d, _, _ in items}
            used_x = sorted({p[0] for p in raw.values()})
            used_y = sorted({p[1] for p in raw.values()})
            # comprime righe/colonne vuote
            pos = {r: (used_x.index(p[0]), used_y.index(p[1])) for r, p in raw.items()}
        if len(set(pos.values())) < len(pos):  # difensivo: disposizione a griglia semplice
            pos = {r: (i % 8, i // 8) for i, r in enumerate(sorted(rooms))}
        save_json({"group": folder, "rooms": [f"{r:03X}" for r in sorted(rooms)],
                   "valid": sum(1 for it in items if it[3]),
                   "overview_positions": {f"{r:03X}": list(p) for r, p in pos.items()}}, gdir / "group.json")
        if not args.no_images:
            orig = {r: g.render(r) for r in rooms}
            save_png(overview(rooms, pos, orig), gdir / "overview_original.png")
            mapped = {r: draw_mapped(grid, mp, invalid=not valid) for r, _, grid, valid in items}
            save_png(overview(rooms, pos, mapped), gdir / "overview_mapped.png")

    # --- radice: index, npz, report ---------------------------------------------------------
    save_json({"schema": "leveledit_la_index/1", "rom_sha1": g.rom_sha1, "rooms": index}, out / "index.json")
    import numpy as np

    def write_npz(p):
        with open(p, "wb") as f:
            np.savez_compressed(f, **arrays)

    arrays = dict(
        grid=np.array(npz["grid"], dtype=np.int8),
        grid_no_entities=np.array(npz["grid_no_entities"], dtype=np.int8), grid_raw=np.array(npz["grid_raw"], dtype=np.int8),
        grid_tiles=np.array(npz["grid_tiles"], dtype=np.int8), objects=np.array(npz["objects"], dtype=np.uint8),
        room_id=np.array(npz["room_id"], dtype=np.int16), region=np.array(npz["region"]), group=np.array(npz["group"]),
        map_id=np.array(npz["map_id"], dtype=np.int16), table_x=np.array(npz["table_x"], dtype=np.int8),
        table_y=np.array(npz["table_y"], dtype=np.int8), layout=np.array(npz["layout"], dtype=np.int8),
        layout_x=np.array(npz["layout_x"], dtype=np.int8), layout_y=np.array(npz["layout_y"], dtype=np.int8),
        valid=np.array(npz["valid"], dtype=bool), brief_valid=np.array(npz["brief_valid"], dtype=bool), notes=np.array(npz["notes"]),
    )
    if args.reference:
        arrays["same_as_reference"] = np.array(npz["same_as_reference"], dtype=bool)
        arrays["reference_min_diff"] = np.array(npz["reference_min_diff"], dtype=np.int16)
    _retry(write_npz, out / "dataset.npz")
    by_group = {}
    for folder, items in sorted(groups.items()):
        by_group[folder] = {"rooms": len(items), "valid": sum(1 for it in items if it[3]),
                            "brief_valid": sum(1 for it in index if it["group"] == folder and it["brief_valid"])}
    fix_count = Counter(fx for it in index for fx in it["fixes"])
    brief_fail = Counter(k for it in index if it["valid"] for k, v in it["brief_checks"].items()
                         if k != "all_ok" and v is not True)
    report = {
        "rooms_total": len(index),
        "rooms_valid": sum(1 for it in index if it["valid"]),
        "rooms_discarded": sum(1 for it in index if not it["valid"]),
        "rooms_brief_valid": sum(1 for it in index if it["brief_valid"]),
        "brief_rule_failures_on_valid_rooms": dict(brief_fail.most_common()),
        "discard_reasons": dict(reason_count.most_common()),
        "flags_on_rooms": dict(flag_count.most_common()),
        "fixes_applied": dict(fix_count.most_common()),
        "by_group": by_group,
        "seconds": round(time.time() - t0, 1),
    }
    save_json(report, out / "report.json")
    _retry(lambda p: Path(p).write_text(report_md(report, index), encoding="utf-8"), out / "report.md")
    print(json.dumps({k: v for k, v in report.items() if k != "by_group"}, indent=1))


REASON_IT = {
    "sidescroll": "stanza a scorrimento laterale (2D), non rappresentabile dall'alto",
    "empty_room": "stanza vuota/non usata (nessun oggetto, entita' o warp)",
    "no_floor_for_player": "nessuna cella di pavimento dove mettere il giocatore (es. schermate d'acqua)",
    "special:unmapped": "oggetti non presenti nelle tabelle di mapping",
}


def report_md(rep, index):
    L = ["# Report estrazione stanze - Link's Awakening DX (U) v1.0", "",
         f"- Stanze estratte: **{rep['rooms_total']}**",
         f"- Valide: **{rep['rooms_valid']}**",
         f"- Scartate: **{rep['rooms_discarded']}** (una stanza puo' avere piu' motivi)",
         f"- Valide che rispettano anche tutte le regole del brief (scale, bordi chiusi, max 2 porte): **{rep['rooms_brief_valid']}**", "",
         "La griglia e' fedele 1:1 al gioco: le scale non vengono inventate e i bordi non vengono chiusi.",
         "Le regole del brief sono solo verificate (`brief_checks` in ogni room.json).", "",
         "## Regole del brief non rispettate (stanze valide)", "", "| Regola | Stanze |", "|---|---|"]
    for k, v in rep["brief_rule_failures_on_valid_rooms"].items():
        L.append(f"| `{k}` | {v} |")
    L += ["",
         "## Motivi di scarto", "", "| Motivo | Stanze | Significato |", "|---|---|---|"]
    for k, v in rep["discard_reasons"].items():
        desc = REASON_IT.get(k) or ("tile/entita' speciale con politica 'discard' (vedi mappings/categories.json)"
                                    if k.startswith("special:") else "")
        L.append(f"| `{k}` | {v} | {desc} |")
    L += ["", "## Segnalazioni (stanze comunque valide)", "", "| Segnalazione | Stanze |", "|---|---|"]
    for k, v in rep["flags_on_rooms"].items():
        L.append(f"| `{k}` | {v} |")
    L += ["", "## Correzioni applicate", "", "| Correzione | Stanze |", "|---|---|"]
    for k, v in rep["fixes_applied"].items():
        L.append(f"| `{k}` | {v} |")
    L += ["", "## Per gruppo", "", "| Gruppo | Stanze | Valide |", "|---|---|---|"]
    for k, v in rep["by_group"].items():
        L.append(f"| {k} | {v['rooms']} | {v['valid']} |")
    L += ["", "## Stanze scartate", "", "| Stanza | Gruppo | Motivi |", "|---|---|---|"]
    for it in index:
        if not it["valid"]:
            L.append(f"| {it['room_id']} | {it['group']} | {', '.join(it['discard_reasons'])} |")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    main()
