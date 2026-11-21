"""
file di prova - ricostruisce l'immagine di una stanza di Link's Awakening (DX)
SENZA giocatore e nemici, usando la griglia ASCII "pulita" e gli ID delle tile.

Feature principali
---------------------------------------
- Usa `grid_no_entities_ascii` (nessun P / M): la stanza e' solo layout.
  Se nell'ASCII compaiono comunque P o M vengono trattati come pavimento.
- Usa anche l'ID specifico di ogni cella (campo `objects` di room.json, esadecimale). L'ID dice
  esattamente quale blocco del gioco c'e' (es. quale muro, quale tipo di erba), mentre l'ASCII ha
  solo 11 categorie.

Come sceglie la tile di una cella (in ordine):
  1. ritagli con lo stesso ID nello stesso tileset (gruppo di stanze, es. "overworld",
     "dungeons/D1_tail_cave"); se ce ne sono piu' di uno (palette diverse da stanza a stanza)
     vince quello con il vicinato (ID dei vicini, poi categorie dei vicini) piu' simile, poi il piu' frequente;
  2. se l'ID non e' mai stato visto in quel tileset: ritaglio della stessa categoria ASCII,
     scelto in base al vicinato (come in ascii_to_image.py);
  3. se manca anche quello: stessi tentativi sugli altri tileset della stessa famiglia
     (overworld / dungeons / indoor);
  4. altrimenti un quadrato di colore piatto.

Le tile sono ritagli 16x16 degli original.png in data/la_local/rooms (stanze valide).

Esempi (dalla radice del repository)
-----------------------------------
  # da un room.json, affiancato all'originale (la stanza stessa e' esclusa dal banco)
  python src/testing/ascii_to_image_no_entities.py \
      --room data/la_local/rooms/overworld/room_000/room.json --compare --out out.png

  # ASCII + ID da file di testo (8 righe; gli ID sono 10 token esadecimali separati da spazi)
  python src/testing/ascii_to_image_no_entities.py --ascii layout.txt --ids ids.txt \
      --group dungeons/D1_tail_cave --out out.png

Da Python
---------
  from ascii_to_image_no_entities import TileBank, render_room
  bank = TileBank.build()
  img = render_room(room["grid_no_entities_ascii"], room["objects"], bank, room["group"])
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
ROOMS_DIR = ROOT / "data" / "la_local" / "rooms"

CELL = 16
ROWS, COLS = 8, 10

SYMBOL_TO_CAT = {" ": 0, "#": 1, ".": 2, "~": 3, "=": 4, "D": 5, "K": 6,
                 "B": 7, "E": 8, "P": 9, "M": 10}
FLOOR = 2
ENTITY_CATS = {9, 10}  # giocatore e nemico: non hanno tile propria, sotto c'e' il pavimento

FALLBACK_COLOR = {0: (0, 0, 0), 1: (120, 120, 120), 2: (200, 180, 120), 3: (40, 80, 200),
                  4: (230, 140, 40), 5: (200, 40, 40), 6: (240, 220, 0), 7: (140, 90, 40),
                  8: (60, 200, 90)}

# vicini: (dy, dx, peso). I 4 vicini diretti contano il doppio delle diagonali.
NEIGHBOURS = [(-1, 0, 2), (0, 1, 2), (1, 0, 2), (0, -1, 2),
              (-1, -1, 1), (-1, 1, 1), (1, 1, 1), (1, -1, 1)]


# --------------------------------------------------------------------------- griglie
def ascii_to_cats(rows: list[str]) -> list[list[int]]:
    """8 stringhe da 10 caratteri -> categorie 8x10, con P/M sostituiti dal pavimento."""
    if len(rows) != ROWS or any(len(r) != COLS for r in rows):
        raise ValueError(f"servono {ROWS} righe da {COLS} caratteri, trovate "
                         f"{[len(r) for r in rows]}")
    bad = {c for r in rows for c in r if c not in SYMBOL_TO_CAT}
    if bad:
        raise ValueError(f"caratteri sconosciuti: {sorted(bad)}")
    return [[FLOOR if SYMBOL_TO_CAT[c] in ENTITY_CATS else SYMBOL_TO_CAT[c] for c in r] for r in rows]


def norm_ids(ids: list[list[str]]) -> list[list[str]]:
    """Normalizza gli ID in esadecimale maiuscolo a 2 cifre ('2c' -> '2C')."""
    if len(ids) != ROWS or any(len(r) != COLS for r in ids):
        raise ValueError(f"servono {ROWS} righe da {COLS} ID")
    return [[str(v).strip().upper().zfill(2) for v in r] for r in ids]


def context(grid: list[list], y: int, x: int) -> tuple:
    """Valore (categoria o ID) degli 8 vicini; None = fuori schermo."""
    out = []
    for dy, dx, _ in NEIGHBOURS:
        yy, xx = y + dy, x + dx
        out.append(grid[yy][xx] if 0 <= yy < ROWS and 0 <= xx < COLS else None)
    return tuple(out)


def context_score(a: tuple, b: tuple) -> int:
    return sum(w for (_, _, w), p, q in zip(NEIGHBOURS, a, b) if p == q)


# --------------------------------------------------------------------------- banco di tile
class TileBank:
    """Ritagli 16x16 indicizzati per (gruppo, ID) e per (gruppo, categoria)."""

    def __init__(self):
        # chiave -> {bytes ritaglio: [img, Counter(ctx ID), Counter(ctx categorie)]}
        self._by_id: dict[tuple[str, str], dict[bytes, list]] = defaultdict(dict)
        self._by_cat: dict[tuple[str, int], dict[bytes, list]] = defaultdict(dict)
        self._id_f: dict[tuple[str, str], list] = {}
        self._cat_f: dict[tuple[str, int], list] = {}

    @classmethod
    def build(cls, rooms_dir: Path = ROOMS_DIR, only_valid: bool = True,
              exclude: set[str] | None = None) -> "TileBank":
        """exclude: room_id da non usare (per valutare senza barare)."""
        bank = cls()
        index = json.load(open(rooms_dir / "index.json", encoding="utf-8"))["rooms"]
        for e in index:
            if (only_valid and not e["valid"]) or (exclude and e["room_id"] in exclude):
                continue
            folder = rooms_dir / e["path"]
            if not (folder / "original.png").exists():
                continue
            room = json.load(open(folder / "room.json", encoding="utf-8"))
            bank._add_room(e["group"], Image.open(folder / "original.png").convert("RGB"), room)
        bank._freeze()
        return bank

    def _add_room(self, group: str, img: Image.Image, room: dict) -> None:
        cats = room["grid_tiles"]            # categorie dei soli tile (niente P/M)
        ids = norm_ids(room["objects"])      # ID originali del gioco (niente entita')
        for y in range(ROWS):
            for x in range(COLS):
                crop = img.crop((x * CELL, y * CELL, (x + 1) * CELL, (y + 1) * CELL))
                key = crop.tobytes()
                ictx, cctx = context(ids, y, x), context(cats, y, x)
                for store, k in ((self._by_id, (group, ids[y][x])), (self._by_cat, (group, cats[y][x]))):
                    slot = store[k]
                    if key not in slot:
                        slot[key] = [crop, Counter(), Counter()]
                    slot[key][1][ictx] += 1
                    slot[key][2][cctx] += 1

    def _freeze(self) -> None:
        self._id_f = {k: list(v.values()) for k, v in self._by_id.items()}
        self._cat_f = {k: list(v.values()) for k, v in self._by_cat.items()}

    # -- candidati con fallback sulla famiglia
    @staticmethod
    def _family(group: str) -> str:
        return group.split("/")[0]

    def by_id(self, group: str, oid: str) -> list:
        return self._id_f.get((group, oid), [])

    def by_id_family(self, group: str, oid: str) -> list:
        fam = self._family(group)
        return [t for (g, o), ts in self._id_f.items()
                if o == oid and self._family(g) == fam for t in ts]

    def by_cat(self, group: str, cat: int) -> list:
        return self._cat_f.get((group, cat), [])

    def by_cat_family(self, group: str, cat: int) -> list:
        fam = self._family(group)
        return [t for (g, c), ts in self._cat_f.items()
                if c == cat and self._family(g) == fam for t in ts]

    def groups(self) -> list[str]:
        return sorted({g for g, _ in self._id_f})


def _best(cands: list, ictx: tuple, cctx: tuple) -> Image.Image:
    """Tra i candidati: vicinato di ID, poi di categorie, poi frequenza."""
    def score(c):
        _, ids_c, cats_c = c
        return (max(context_score(ictx, k) for k in ids_c),
                max(context_score(cctx, k) for k in cats_c),
                sum(ids_c.values()))
    return max(cands, key=score)[0]


# --------------------------------------------------------------------------- rendering
def render_room(ascii_rows: list[str], ids: list[list[str]], bank: TileBank, group: str,
                stats: Counter | None = None) -> Image.Image:
    """Ricostruisce la stanza da ASCII (senza entita') + ID. `stats` conta il metodo usato per cella."""
    cats, ids = ascii_to_cats(ascii_rows), norm_ids(ids)
    img = Image.new("RGB", (COLS * CELL, ROWS * CELL))
    for y in range(ROWS):
        for x in range(COLS):
            ictx, cctx = context(ids, y, x), context(cats, y, x)
            oid, cat = ids[y][x], cats[y][x]
            for method, cands in (("id", bank.by_id(group, oid)),
                                  ("categoria", bank.by_cat(group, cat)),
                                  ("id_famiglia", bank.by_id_family(group, oid)),
                                  ("categoria_famiglia", bank.by_cat_family(group, cat))):
                if cands:
                    tile = _best(cands, ictx, cctx)
                    break
            else:
                method, tile = "colore_piatto", Image.new("RGB", (CELL, CELL), FALLBACK_COLOR.get(cat, (255, 0, 255)))
            if stats is not None:
                stats[method] += 1
            img.paste(tile, (x * CELL, y * CELL))
    return img


def render_room_json(room: dict, bank: TileBank, group: str | None = None,
                     stats: Counter | None = None) -> Image.Image:
    """Comodo: prende direttamente il dict di un room.json."""
    return render_room(room["grid_no_entities_ascii"], room["objects"], bank,
                       group or room["group"], stats)


# --------------------------------------------------------------------------- confronto
def tile_accuracy(a: Image.Image, b: Image.Image) -> float:
    """Frazione di celle 16x16 identiche pixel per pixel."""
    same = 0
    for y in range(ROWS):
        for x in range(COLS):
            box = (x * CELL, y * CELL, (x + 1) * CELL, (y + 1) * CELL)
            same += a.crop(box).tobytes() == b.crop(box).tobytes()
    return same / (ROWS * COLS)


def side_by_side(*imgs: Image.Image, scale: int = 3, gap: int = 6) -> Image.Image:
    w, h = imgs[0].size
    out = Image.new("RGB", ((w * scale + gap) * len(imgs) - gap, h * scale), (255, 255, 255))
    for i, im in enumerate(imgs):
        out.paste(im.resize((w * scale, h * scale), Image.NEAREST), (i * (w * scale + gap), 0))
    return out


# --------------------------------------------------------------------------- CLI
def _read_ids(path: Path) -> list[list[str]]:
    return [line.split() for line in open(path, encoding="utf-8") if line.strip()][:ROWS]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--room", type=Path, help="percorso di un room.json")
    src.add_argument("--ascii", type=Path, help="file di testo con 8 righe da 10 caratteri (serve anche --ids)")
    ap.add_argument("--ids", type=Path, help="file di testo con 8 righe da 10 ID esadecimali")
    ap.add_argument("--group", help="tileset (es. overworld, dungeons/D1_tail_cave); con --room e' preso dal file")
    ap.add_argument("--rooms-dir", type=Path, default=ROOMS_DIR)
    ap.add_argument("--out", type=Path, default=Path("room_render.png"))
    ap.add_argument("--compare", action="store_true",
                    help="con --room: affianca originale e ricostruzione e stampa la % di celle identiche")
    ap.add_argument("--keep-self", action="store_true",
                    help="con --compare non escludere la stanza stessa dal banco (risultato 'baro')")
    ap.add_argument("--scale", type=int, default=3)
    args = ap.parse_args()

    room = None
    if args.room:
        room = json.load(open(args.room, encoding="utf-8"))
        group, rows, ids = args.group or room["group"], room["grid_no_entities_ascii"], room["objects"]
    else:
        if not (args.ids and args.group):
            ap.error("con --ascii servono anche --ids e --group")
        group = args.group
        rows = [l.rstrip("\n").ljust(COLS) for l in open(args.ascii, encoding="utf-8")][:ROWS]
        ids = _read_ids(args.ids)

    exclude = {room["room_id"]} if room and args.compare and not args.keep_self else None
    bank = TileBank.build(args.rooms_dir, exclude=exclude)
    if group not in bank.groups():
        ap.error(f"gruppo '{group}' sconosciuto. Disponibili: {', '.join(bank.groups())}")

    stats: Counter = Counter()
    img = render_room(rows, ids, bank, group, stats)
    print("celle per metodo:", dict(stats))

    if args.compare and room:
        orig = Image.open(args.room.parent / "original.png").convert("RGB")
        print(f"celle identiche all'originale: {tile_accuracy(img, orig):.0%}")
        img = side_by_side(orig, img, scale=args.scale)
    elif args.scale != 1:
        img = img.resize((img.width * args.scale, img.height * args.scale), Image.NEAREST)
    img.save(args.out)
    print("salvato", args.out)


if __name__ == "__main__":
    main()
