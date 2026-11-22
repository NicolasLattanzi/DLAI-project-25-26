"""
ascii_to_image_no_entities.py - ricostruisce l'immagine di una stanza di Link's Awakening (DX)
prendendo, per ogni ID oggetto, la sua tile dalla cartella data/la_local/tiles. Niente altro.

  ID della cella + tileset (gruppo)  ->  tiles/<gruppo>/<ID>.png  ->  incollata in quella cella

Nessuna inferenza, nessun vicinato, nessuna statistica: ogni cella 16x16 e' il file PNG del suo ID.
Giocatore e nemici non ci sono (`objects` di room.json non li contiene).

Percorso di ogni tile:  tiles/<tipo>/<sottotipo>/<ID>.png   (tipo = overworld | dungeons | indoor)
  tiles/overworld/37.png      tiles/dungeons/D1_tail_cave/2C.png      tiles/indoor/cave_b/0A.png
Le stanze a scorrimento laterale hanno le loro tile in  tiles/<tipo>/<sottotipo>/sidescroll/<ID>.png
Per costruire un'immagine servono SOLO queste cartelle di PNG: nessun json e' obbligatorio.

Palette: lo stesso ID puo' avere piu' versioni di colore (<ID>.png, <ID>_v2.png, ...). Di default si usa
<ID>.png (la piu' comune). Se si passa room_id E esiste tiles/rooms.json, ogni cella usa la versione che
quella stanza usa davvero (immagine identica all'originale); se rooms.json manca si usa <ID>.png.

DA PYTHON (le tre funzioni)
---------------------------
  import sys; sys.path.insert(0, "src/testing")
  from ascii_to_image_no_entities import render_room, render_ids, load_room

  img = render_room("101")                         # stanza per room_id: trova da sola file, tileset e palette
  img = render_room("101", compare=True)           # originale | ricostruzione, affiancati
  room = load_room("101")                          # il dict del room.json (room["objects"], room["group"], ...)
  img = render_ids(room["objects"], "dungeons/D1_tail_cave")   # da una griglia di ID qualsiasi + tileset
  img.save("out.png")                              # img e' un'immagine PIL 160x128

  list_tilesets()                                  # tileset disponibili (cartelle di tile)
  list_rooms()                                     # [(room_id, group), ...] di tutte le stanze disponibili
  list_rooms("dungeons/D1_tail_cave")              # solo quelle di un tileset

DA RIGA DI COMANDO (dalla radice del repository)
------------------------------------------------
  python src/testing/ascii_to_image_no_entities.py --room 101 --compare         # per room_id
  python src/testing/ascii_to_image_no_entities.py --room data/la_local/rooms/overworld/room_000/room.json
  python src/testing/ascii_to_image_no_entities.py --ids ids.txt --group overworld [--room-id 000]
  python src/testing/ascii_to_image_no_entities.py --list [--group overworld]   # elenca le stanze
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
TILES_DIR = ROOT / "data" / "la_local" / "tiles"
ROOMS_DIR = ROOT / "data" / "la_local" / "rooms"
CELL = 16
ROWS, COLS = 8, 10
MISSING = (255, 0, 255)  # magenta: l'ID non esiste in quel tileset


# --------------------------------------------------------------------------- stanze
def _index(rooms_dir: Path = ROOMS_DIR) -> list[dict]:
    return json.load(open(Path(rooms_dir) / "index.json", encoding="utf-8"))["rooms"]


def list_rooms(group: str | None = None, rooms_dir: Path = ROOMS_DIR) -> list[tuple[str, str]]:
    """[(room_id, group), ...] di tutte le stanze; con `group` solo quelle di quel tileset."""
    return [(e["room_id"], e["group"]) for e in _index(rooms_dir) if group in (None, e["group"])]


def room_path(room_id: str, rooms_dir: Path = ROOMS_DIR) -> Path:
    """Percorso del room.json di una stanza, dal suo room_id (es. '101', '23A')."""
    room_id = str(room_id).strip().upper()
    for e in _index(rooms_dir):
        if e["room_id"].upper() == room_id:
            return Path(rooms_dir) / e["path"] / "room.json"
    raise SystemExit(f"stanza '{room_id}' non trovata (usa list_rooms() o --list per vedere quelle disponibili)")


def load_room(room: str | Path, rooms_dir: Path = ROOMS_DIR) -> dict:
    """Carica un room.json. `room` puo' essere un room_id ('101') o il percorso del file."""
    p = Path(str(room))
    path = p if p.suffix == ".json" and p.exists() else room_path(str(room), rooms_dir)
    data = json.load(open(path, encoding="utf-8"))
    data["_path"] = str(path)
    return data


def room_group(room: dict) -> str:
    """Tileset di una stanza. Le stanze a scorrimento laterale hanno tile proprie ('<gruppo>/sidescroll')."""
    return room["group"] + ("/sidescroll" if room["sidescroll"] else "")


# --------------------------------------------------------------------------- immagine
def tile_path(group: str, oid: str, tiles_dir: Path = TILES_DIR, variant: int = 1) -> Path:
    """Percorso della tile di un ID:  tiles/<tipo>/<sottotipo>/<ID>.png
       group = 'overworld' | 'dungeons/D1_tail_cave' | 'indoor/house' | ...  (+ '/sidescroll' per le stanze 2D)
       esempi:  tiles/overworld/37.png   tiles/dungeons/D1_tail_cave/2C.png   tiles/indoor/cave_b/0A.png
       variant 1 = <ID>.png (palette piu' comune); 2, 3... = <ID>_v2.png, <ID>_v3.png (altre palette)."""
    oid = str(oid).strip().upper().zfill(2)
    return Path(tiles_dir) / group / (f"{oid}.png" if variant == 1 else f"{oid}_v{variant}.png")


def list_tilesets(tiles_dir: Path = TILES_DIR) -> list[str]:
    """Tileset disponibili = cartelle che contengono PNG (es. 'overworld', 'dungeons/D1_tail_cave')."""
    root = Path(tiles_dir)
    return sorted({p.parent.relative_to(root).as_posix() for p in root.rglob("*.png")
                   if not p.relative_to(root).parts[0].startswith("_")})


def _room_variants(tiles_dir: Path, group: str, room_id: str | None) -> list[int] | None:
    """FACOLTATIVO: variante di palette di ogni cella di una stanza, da tiles/rooms.json (se il file c'e').
    Senza rooms.json, o senza room_id, ogni cella usa <ID>.png."""
    f = Path(tiles_dir) / "rooms.json"
    if room_id is None or not f.exists():
        return None
    rooms = json.load(open(f, encoding="utf-8"))["groups"].get(group, [])
    rec = next((r for r in rooms if r["room"] == str(room_id).upper()), None)
    return [int(c, 36) for c in rec["var"]] if rec else None


def render_ids(ids: list[list[str]], group: str, room_id: str | None = None,
               tiles_dir: Path = TILES_DIR) -> Image.Image:
    """Immagine 160x128: la cella (y, x) e' la tile  tiles_dir/<group>/<ID>.png  con ID = ids[y][x].
    Serve solo la cartella con le immagini: nessun json e' obbligatorio. Se si passa room_id e c'e'
    tiles/rooms.json, ogni cella usa la palette esatta di quella stanza (<ID>_v2.png ecc.)."""
    tiles_dir = Path(tiles_dir)
    if not (tiles_dir / group).is_dir():
        raise SystemExit(f"cartella '{tiles_dir / group}' non trovata. Tileset disponibili: {', '.join(list_tilesets(tiles_dir))}")
    variant_of = _room_variants(tiles_dir, group, room_id)

    img = Image.new("RGB", (COLS * CELL, ROWS * CELL), MISSING)
    missing = set()
    for y in range(ROWS):
        for x in range(COLS):
            path = tile_path(group, ids[y][x], tiles_dir, variant_of[y * COLS + x] if variant_of else 1)
            if not path.exists():
                path = tile_path(group, ids[y][x], tiles_dir)  # palette non presente: versione comune
            if not path.exists():
                missing.add(str(ids[y][x]).strip().upper().zfill(2))
                continue
            img.paste(Image.open(path).convert("RGB"), (x * CELL, y * CELL))
    if missing:
        print(f"ATTENZIONE: nessun file per questi ID in '{group}' (celle magenta): {sorted(missing)}")
    return img


def cells_identical(a: Image.Image, b: Image.Image) -> float:
    """Frazione di celle 16x16 identiche pixel per pixel."""
    same = 0
    for y in range(ROWS):
        for x in range(COLS):
            box = (x * CELL, y * CELL, (x + 1) * CELL, (y + 1) * CELL)
            same += a.crop(box).tobytes() == b.crop(box).tobytes()
    return same / (ROWS * COLS)


def side_by_side(left: Image.Image, right: Image.Image, scale: int = 3, gap: int = 6) -> Image.Image:
    w, h = left.size
    out = Image.new("RGB", (w * scale * 2 + gap, h * scale), (255, 255, 255))
    out.paste(left.resize((w * scale, h * scale), Image.NEAREST), (0, 0))
    out.paste(right.resize((w * scale, h * scale), Image.NEAREST), (w * scale + gap, 0))
    return out


def render_room(room: str | Path, compare: bool = False, scale: int = 1,
                tiles_dir: Path = TILES_DIR, rooms_dir: Path = ROOMS_DIR, verbose: bool = True) -> Image.Image:
    """Ricostruisce una stanza dal suo room_id ('101') o dal percorso del suo room.json.
    compare=True: ritorna originale | ricostruzione affiancati (e stampa le celle identiche).
    scale: ingrandimento intero dell'immagine restituita."""
    data = load_room(room, rooms_dir)
    group = room_group(data)
    img = render_ids(data["objects"], group, data["room_id"], tiles_dir)
    if verbose:
        print(f"stanza {data['room_id']} | tileset {group} | file {data['_path']}")
    if compare:
        orig = Image.open(Path(data["_path"]).parent / "original.png").convert("RGB")
        if verbose:
            print(f"celle identiche all'originale: {cells_identical(img, orig):.1%}")
        return side_by_side(orig, img, scale=max(scale, 1))
    return img if scale == 1 else img.resize((img.width * scale, img.height * scale), Image.NEAREST)


# --------------------------------------------------------------------------- riga di comando
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tiles-dir", type=Path, default=TILES_DIR)
    ap.add_argument("--rooms-dir", type=Path, default=ROOMS_DIR)
    ap.add_argument("--list", action="store_true", help="elenca le stanze (room_id e tileset); filtra con --group")
    ap.add_argument("--room", help="room_id (es. 101) oppure percorso di un room.json")
    ap.add_argument("--ids", type=Path, help="file con 8 righe da 10 ID esadecimali separati da spazi")
    ap.add_argument("--group", help="tileset (obbligatorio con --ids)")
    ap.add_argument("--room-id", help="con --ids: room_id da cui prendere le palette (facoltativo)")
    ap.add_argument("--compare", action="store_true", help="con --room: affianca l'originale")
    ap.add_argument("--out", type=Path, default=Path("room_render.png"))
    ap.add_argument("--scale", type=int, default=3)
    args = ap.parse_args()

    if args.list:
        for rid, g in list_rooms(args.group, args.rooms_dir):
            print(rid, g)
        return
    if bool(args.room) == bool(args.ids):
        ap.error("serve una sola tra --room e --ids (oppure --list)")

    if args.room:
        img = render_room(args.room, args.compare, args.scale, args.tiles_dir, args.rooms_dir)
    else:
        if not args.group:
            ap.error("con --ids serve --group")
        ids = [l.split() for l in open(args.ids, encoding="utf-8") if l.strip()][:ROWS]
        img = render_ids(ids, args.group, args.room_id, args.tiles_dir)
        img = img.resize((img.width * args.scale, img.height * args.scale), Image.NEAREST)
    img.save(args.out)
    print("salvato", args.out)


if __name__ == "__main__":
    main()