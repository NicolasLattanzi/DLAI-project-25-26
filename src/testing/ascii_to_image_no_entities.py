"""
ascii_to_image_no_entities.py - ricostruisce l'immagine di una stanza di Link's Awakening (DX)
ricostruendo ogni tile a partire dal suo ID, salvato nel json della stanza corrispondente.
Nemici e giocatore sono ignorati.

    Gioco di riferimento + tileset + stanza specifica + ID cella  ->  tile trovata

---------------------------
si può utilizzare il file MAIN in questa cartella per provare le varie funzioni,
in alternativa, alcunoi esempi da riga di comando:

  python src/testing/ascii_to_image_no_entities.py --room 101 --compare         # per room_id
  python src/testing/ascii_to_image_no_entities.py --room data/la_local/rooms/overworld/room_000/room.json
  python src/testing/ascii_to_image_no_entities.py --ids ids.txt --group overworld [--room-id 000]
  python src/testing/ascii_to_image_no_entities.py --list [--group overworld]   # elenca le stanze
"""

import argparse
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
TILES_DIR = ROOT / "data" / "dataset" / "tiles_trainval" / "la"
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

def list_tilesets() -> list[str]:
    """Tileset disponibili = cartelle che contengono PNG (es. 'overworld', 'dungeons/D1_tail_cave')."""
    root = Path(TILES_DIR)
    return sorted({p.parent.relative_to(root).as_posix() for p in root.rglob("*.png")
                   if not p.relative_to(root).parts[0].startswith("_")})


def norm_id(v) -> str | None:
    """ID di una cella -> 2 cifre esadecimali maiuscole.  '2c' / '0x2C' / 44 (intero, = 0x2C) -> '2C'.
    Le stringhe sono lette come esadecimale; gli interi (anche numpy) come numero. None resta None."""
    if v is None: return None
    
    if isinstance(v, str):
        v = v.strip().upper()
        return (v[2:] if v.startswith("0X") else v).zfill(2)
    return f"{int(v):02X}"


def render_ids(ids, group: str, room_id: str) -> Image.Image:
    """Immagine 160x128 da una MATRICE DI ID 8 righe x 10 colonne ('2C', '2c', '0x2C')
    group: tileset ('overworld', 'dungeons/D1_tail_cave', 'indoor/house', ...).
    room_id: stanza specifica nel dataset ('D1_tail_cave', 'D2_bottle_grotto', ...)"""
    
    tiles_dir = TILES_DIR / group / room_id
    if not tiles_dir.is_dir():
        raise SystemExit(f"cartella '{tiles_dir}' non trovata. Tileset disponibili: {', '.join(list_tilesets())}")
    if len(ids) != ROWS or any(len(row) != COLS for row in ids):
        raise ValueError(f"la matrice deve essere {ROWS} righe x {COLS} colonne, trovata "
                         f"{len(ids)} x {sorted({len(r) for r in ids})}")

    img = Image.new("RGB", (COLS * CELL, ROWS * CELL), MISSING)
    missing = set()
    for y in range(ROWS):
        for x in range(COLS):
            oid = norm_id(ids[y][x])
            if oid is None:  # cella senza tile (magenta voluta)
                continue
            
            path = tiles_dir / f"{oid}.png"
            if not path.exists():
                missing.add(oid)
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


# --------------------------------------------------------------------------- da ASCII
# Per ogni tileset: quale tile (ID) disegnare per ciascun simbolo ASCII. E' l'ID piu' comune di quel simbolo
# in quel tileset in tutto il gioco, calcolato una volta e scritto qui: la funzione non legge nessuna stanza.
# Sono modificabili: render_ascii(rows, group, symbol_ids={"#": "37"}).
SYMBOL_TILES = {
    'dungeons/D0_color_dungeon': {' ': '03', '#': '22', '.': '0D', '~': 'AF', 'D': '2D', 'B': '20', 'E': 'CB'},
    'dungeons/D1_tail_cave': {' ': '03', '#': '22', '.': '0D', '~': 'B0', 'D': '2F', 'B': 'A7', 'E': 'BE'},
    'dungeons/D1_tail_cave/sidescroll': {'#': '6D', '.': '04'},
    'dungeons/D2_bottle_grotto': {' ': '03', '#': '21', '.': '0D', '~': 'AE', 'D': '33', 'B': '20', 'E': 'BF'},
    'dungeons/D2_bottle_grotto/sidescroll': {'#': '54', '.': '04'},
    'dungeons/D3_key_cavern': {' ': '03', '#': '22', '.': '0D', '~': '01', 'D': 'DE', 'B': '20', 'E': 'BE'},
    'dungeons/D3_key_cavern/sidescroll': {'#': '68', '.': '04'},
    'dungeons/D4_anglers_tunnel': {' ': '03', '#': '22', '.': '0D', '~': '0E', 'D': '2D', 'B': '20', 'E': 'BE'},
    'dungeons/D4_anglers_tunnel/sidescroll': {'#': '6D', '.': '04', '~': '84'},
    'dungeons/D5_catfishs_maw': {' ': '03', '#': '22', '.': '0D', '~': '01', 'D': 'DE', 'B': 'DD', 'E': 'BE'},
    'dungeons/D5_catfishs_maw/sidescroll': {'#': '6D', '.': '04', '~': '81'},
    'dungeons/D6_face_shrine': {' ': '03', '#': '22', '.': '0D', '~': 'AE', 'D': 'DE', 'B': '20', 'E': 'BE'},
    'dungeons/D6_face_shrine/sidescroll': {'#': '68', '.': '04'},
    'dungeons/D7_eagles_tower': {' ': '1C', '#': '22', '.': '0D', '~': 'D4', 'D': 'DE', 'B': '20', 'E': 'A3'},
    'dungeons/D7_eagles_tower/sidescroll': {' ': '03', '#': '68', '.': '00'},
    'dungeons/D8_turtle_rock': {' ': '03', '#': '21', '.': '0D', '~': '06', 'D': 'DE', 'B': '20', 'E': 'CB'},
    'dungeons/D8_turtle_rock/sidescroll': {'#': '54', '.': '04', '~': '85'},
    'dungeons/D9_windfishs_egg': {'#': '21', '.': '0D', '~': '1C'},
    'indoor/bowwow_hideout': {' ': '00', '#': '22', '.': '0D'},
    'indoor/cave_b': {' ': 'DF', '#': '21', '.': '05', '~': '01', 'B': 'A7', 'E': 'CB'},
    'indoor/cave_b/sidescroll': {'#': '51', '.': '04', '~': '81'},
    'indoor/cave_c': {' ': '00', '#': '21', '.': '05', '~': '01', 'B': 'A7', 'E': 'CB'},
    'indoor/cave_c/sidescroll': {'#': '54', '~': '81'},
    'indoor/cave_water': {' ': 'DF', '#': '21', '.': '0D', '~': '0E', 'B': '20', 'E': 'CB'},
    'indoor/cave_water/sidescroll': {' ': '03', '#': '54', '.': '04'},
    'indoor/doghouse': {' ': '01', '#': '24', '.': '05', 'B': '20'},
    'indoor/dream_shrine': {'#': '21', '.': '0D', 'B': '4E'},
    'indoor/ghost_house': {'#': '21', '.': '0D', 'B': '20'},
    'indoor/house': {' ': '01', '#': '21', '.': '0D', 'B': '20'},
    'indoor/house/sidescroll': {'#': '61', '.': '00'},
    'indoor/kanalet': {' ': '03', '#': '21', '.': '0D', 'B': '20', 'E': 'CB'},
    'indoor/library': {'#': '99', '.': '0D'},
    'indoor/minigame': {'#': 'D3', '.': '00'},
    'indoor/minigame/sidescroll': {' ': '03', '#': '54', '.': '00', '~': '81'},
    'indoor/s_face_shrine': {' ': '03', '#': '23', '.': '0F', 'B': '20'},
    'indoor/shop': {'#': '21', '.': '0D', 'B': '20'},
    'overworld': {' ': '00', '#': '3A', '.': '04', '~': '0E', '=': '7A', 'B': '5C', 'E': 'E1'},
}

_ASCII_SYMBOLS = " #.~=DKBE"  # P (giocatore) e M (nemico) non hanno tile: si disegna il pavimento '.'


def _parse_ascii(rows: str | list[str]) -> list[str]:
    """Accetta 8 stringhe (o una stringa con 8 righe); le righe corte vengono completate con spazi a 10."""
    rows = rows.split("\n") if isinstance(rows, str) else list(rows)
    if len(rows) != ROWS:
        raise ValueError(f"servono esattamente {ROWS} righe (anche quelle di soli spazi), trovate {len(rows)}. "
                         f"Passa una lista di {ROWS} stringhe.")
    rows = [r.ljust(COLS) for r in rows]
    if any(len(r) > COLS for r in rows):
        raise ValueError(f"ogni riga deve avere al massimo {COLS} caratteri")
    bad = {c for r in rows for c in r} - set(_ASCII_SYMBOLS + "PM")
    if bad:
        raise ValueError(f"simboli ASCII sconosciuti: {sorted(bad)}")
    return rows


def render_ascii(rows: str | list[str], group: str, symbol_ids: dict[str, str] | None = None,
                 tiles_dir: Path = TILES_DIR) -> Image.Image:
    # Immagine 160x128 da una codifica ASCII (8 righe da 10 caratteri) e dal tileset `group`.

    rows = _parse_ascii(rows)
    if group not in SYMBOL_TILES:
        raise SystemExit(f"tileset '{group}' sconosciuto. Disponibili: {', '.join(sorted(SYMBOL_TILES))}")
    table = {**SYMBOL_TILES[group], **(symbol_ids or {})}
    used = {"." if c in "PM" else c for r in rows for c in r}
    absent = sorted(c for c in used if c not in table)
    if absent:
        print(f"ATTENZIONE: nel tileset '{group}' non c'e' una tile per i simboli {absent} (celle magenta). "
              f"Indicala con symbol_ids={{'{absent[0]}': '<ID>'}}")
    ids = [[table.get("." if c in "PM" else c) for c in r] for r in rows]  # None = simbolo senza tile
    return render_ids(ids, group, None, tiles_dir)


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