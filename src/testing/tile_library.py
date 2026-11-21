"""
tile_library.py - costruisce immagini di stanze di Link's Awakening usando SOLO la cartella delle tile
(data/la_local/tiles, creata da src/la_extract/export_tiles.py). Non servono ne' le stanze ne'
la ROM, e non serve sapere da quale stanza arrivi l'ASCII: basta scegliere il tileset (gruppo).

Tre modi per costruire un'immagine
----------------------------------
1. Da ID:            lib.render_ids(ids, group)            # griglia 8x10 di ID esadecimali ("2C")
2. Da ASCII:         lib.render_ascii(rows, group)         # ogni cella: categoria + vicinato -> ID piu' probabile
3. Misto:            lib.render_ascii(rows, group, ids=griglia_parziale)
                     celle con un ID (es. "37") usano quello, celle con None/"" vengono dedotte dall'ASCII
Per forzare un ID per tutti i caratteri di un tipo:  render_ascii(rows, group, symbol_ids={"#": "37"})

P (giocatore) e M (nemico) vengono ignorati: la cella diventa pavimento.

Per vedere quali ID esistono: guarda tiles/_atlas/<gruppo>.png oppure tiles/index.json
(per ogni ID: file, nome, categoria, simbolo, conteggio, varianti di palette).

Da riga di comando (dalla radice del repository)
------------------------------------------------
  python src/testing/tile_library.py --list-groups
  python src/testing/tile_library.py --ascii layout.txt --group dungeons/D1_tail_cave --out out.png
  python src/testing/tile_library.py --ascii layout.txt --ids ids.txt --group overworld --out out.png
  python src/testing/tile_library.py --room data/la_local/rooms/overworld/room_000/room.json --compare --out out.png
  # (--room usa grid_no_entities_ascii e, con --use-room-ids, anche gli ID del file)
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
TILES_DIR = ROOT / "data" / "la_local" / "tiles"

CELL = 16
ROWS, COLS = 8, 10
OUTSIDE = "@"
FLOOR_SYMBOL = "."
VALID_SYMBOLS = set(" #.~=DKBEPM")
ENTITY_SYMBOLS = {"P", "M"}
# i 4 vicini diretti (N, E, S, O) pesano il doppio delle diagonali (NO, NE, SE, SO)
WEIGHTS = (2, 2, 2, 2, 1, 1, 1, 1)
OFFSETS = ((-1, 0), (0, 1), (1, 0), (0, -1), (-1, -1), (-1, 1), (1, 1), (1, -1))
FLAT_COLOR = {" ": (0, 0, 0), "#": (120, 120, 120), ".": (200, 180, 120), "~": (40, 80, 200),
              "=": (230, 140, 40), "D": (200, 40, 40), "K": (240, 220, 0), "B": (140, 90, 40),
              "E": (60, 200, 90)}
MISSING = (255, 0, 255)


class TileLibrary:
    def __init__(self, tiles_dir: Path = TILES_DIR):
        self.dir = Path(tiles_dir)
        self.index = json.load(open(self.dir / "index.json", encoding="utf-8"))
        self._cache: dict[str, Image.Image] = {}
        self._stats_raw = json.load(open(self.dir / "context_stats.json", encoding="utf-8"))["groups"]
        self._by_center: dict[str, dict[str, list]] = {}  # gruppo -> simbolo centrale -> [(ctx, Counter)]

    # ------------------------------------------------------------------ info
    def groups(self, with_sidescroll: bool = False) -> list[str]:
        return [g for g, v in self.index["groups"].items() if with_sidescroll or not v["sidescroll"]]

    def ids(self, group: str) -> list[str]:
        return sorted(self.index["groups"][group]["tiles"])

    def info(self, group: str, oid: str) -> dict | None:
        return self.index["groups"].get(group, {}).get("tiles", {}).get(oid.upper().zfill(2))

    # ------------------------------------------------------------------ tile
    def _load(self, rel: str) -> Image.Image:
        if rel not in self._cache:
            self._cache[rel] = Image.open(self.dir / rel).convert("RGB")
        return self._cache[rel]

    def tile(self, group: str, oid: str, variant: int = 1) -> Image.Image:
        """Tile 16x16 di un ID. variant=1 e' la piu' frequente, 2.. le altre palette.
        Se l'ID non esiste nel gruppo prova gli altri gruppi della stessa famiglia, poi magenta."""
        oid = str(oid).strip().upper().zfill(2)
        info = self.info(group, oid)
        if info is None:
            fam = group.split("/")[0]
            for g, gv in self.index["groups"].items():
                if gv["family"] == fam and not gv["sidescroll"] and oid in gv["tiles"]:
                    info = gv["tiles"][oid]
                    break
        if info is None:
            return Image.new("RGB", (CELL, CELL), MISSING)
        v = info["variants"][min(max(variant, 1), len(info["variants"])) - 1]
        return self._load(v["file"])

    # ------------------------------------------------------------------ ASCII -> ID
    def _center_index(self, group: str) -> dict[str, list]:
        if group not in self._by_center:
            idx: dict[str, list] = defaultdict(list)
            for ctx, counts in self._stats_raw.get(group, {}).items():
                idx[ctx[0]].append((ctx[1:], Counter(counts)))
            self._by_center[group] = idx
        return self._by_center[group]

    def _candidates(self, group: str, symbol: str) -> list:
        idx = self._center_index(group)
        if idx.get(symbol):
            return idx[symbol]
        fam = group.split("/")[0]  # gruppo senza questo tipo di cella: usa la stessa famiglia
        merged = []
        for g in self.groups():
            if g.split("/")[0] == fam and self._center_index(g).get(symbol):
                merged.extend(self._center_index(g)[symbol])
        return merged

    @staticmethod
    def _clean(rows: list[str]) -> list[str]:
        if len(rows) != ROWS or any(len(r) != COLS for r in rows):
            raise ValueError(f"servono {ROWS} righe da {COLS} caratteri, trovate {[len(r) for r in rows]}")
        bad = {c for r in rows for c in r} - VALID_SYMBOLS
        if bad:
            raise ValueError(f"caratteri sconosciuti: {sorted(bad)}")
        return ["".join(FLOOR_SYMBOL if c in ENTITY_SYMBOLS else c for c in r) for r in rows]

    def ascii_to_ids(self, rows: list[str], group: str, ids: list[list] | None = None,
                     symbol_ids: dict[str, str] | None = None) -> list[list[str | None]]:
        """Griglia 8x10 di ID dedotti dall'ASCII (None se non esiste nessun candidato)."""
        rows = self._clean(rows)
        out: list[list[str | None]] = [[None] * COLS for _ in range(ROWS)]
        for y in range(ROWS):
            for x in range(COLS):
                fixed = ids[y][x] if ids else None
                if fixed:
                    out[y][x] = str(fixed).strip().upper().zfill(2)
                    continue
                sym = rows[y][x]
                if symbol_ids and sym in symbol_ids:
                    out[y][x] = symbol_ids[sym].upper().zfill(2)
                    continue
                ctx = [rows[y + dy][x + dx] if 0 <= y + dy < ROWS and 0 <= x + dx < COLS else OUTSIDE
                       for dy, dx in OFFSETS]
                cands = self._candidates(group, sym)
                if not cands:
                    continue
                best, total = -1, Counter()
                for c_ctx, counts in cands:
                    s = sum(w for w, a, b in zip(WEIGHTS, ctx, c_ctx) if a == b)
                    if s > best:
                        best, total = s, Counter()
                    if s == best:
                        total.update(counts)
                out[y][x] = total.most_common(1)[0][0]
        return out

    # ------------------------------------------------------------------ rendering
    def render_ids(self, ids: list[list[str]], group: str, variant: int = 1) -> Image.Image:
        img = Image.new("RGB", (COLS * CELL, ROWS * CELL))
        for y in range(ROWS):
            for x in range(COLS):
                img.paste(self.tile(group, ids[y][x], variant), (x * CELL, y * CELL))
        return img

    def render_ascii(self, rows: list[str], group: str, ids: list[list] | None = None,
                     symbol_ids: dict[str, str] | None = None, variant: int = 1) -> Image.Image:
        rows_c = self._clean(rows)
        grid = self.ascii_to_ids(rows_c, group, ids, symbol_ids)
        img = Image.new("RGB", (COLS * CELL, ROWS * CELL))
        for y in range(ROWS):
            for x in range(COLS):
                if grid[y][x] is None:  # nessun ID possibile: quadrato piatto col colore della categoria
                    tile = Image.new("RGB", (CELL, CELL), FLAT_COLOR.get(rows_c[y][x], MISSING))
                else:
                    tile = self.tile(group, grid[y][x], variant)
                img.paste(tile, (x * CELL, y * CELL))
        return img


# ---------------------------------------------------------------------- utilita'
def tile_accuracy(a: Image.Image, b: Image.Image) -> float:
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


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tiles-dir", type=Path, default=TILES_DIR)
    ap.add_argument("--list-groups", action="store_true")
    src = ap.add_mutually_exclusive_group()
    src.add_argument("--ascii", type=Path, help="file di testo con 8 righe da 10 caratteri")
    src.add_argument("--room", type=Path, help="room.json (usa grid_no_entities_ascii)")
    ap.add_argument("--ids", type=Path, help="file con 8 righe da 10 ID esadecimali; '--' = cella da dedurre")
    ap.add_argument("--use-room-ids", action="store_true", help="con --room usa anche gli ID del file")
    ap.add_argument("--group", help="tileset; con --room e' preso dal file")
    ap.add_argument("--variant", type=int, default=1, help="1 = palette piu' frequente (default)")
    ap.add_argument("--compare", action="store_true", help="con --room: affianca originale e risultato")
    ap.add_argument("--out", type=Path, default=Path("room_render.png"))
    ap.add_argument("--scale", type=int, default=3)
    args = ap.parse_args()

    lib = TileLibrary(args.tiles_dir)
    if args.list_groups:
        print("\n".join(lib.groups()))
        return
    if not (args.ascii or args.room):
        ap.error("serve --ascii o --room (oppure --list-groups)")

    ids = None
    room = None
    if args.room:
        room = json.load(open(args.room, encoding="utf-8"))
        group, rows = args.group or room["group"], room["grid_no_entities_ascii"]
        if args.use_room_ids:
            ids = room["objects"]
    else:
        if not args.group:
            ap.error("con --ascii serve --group")
        group = args.group
        rows = [l.rstrip("\n").ljust(COLS) for l in open(args.ascii, encoding="utf-8")][:ROWS]
    if args.ids:
        ids = [[("" if t == "--" else t) for t in l.split()] for l in open(args.ids, encoding="utf-8") if l.strip()][:ROWS]
    if group not in lib.groups():
        ap.error(f"gruppo '{group}' sconosciuto. Usa --list-groups")

    img = lib.render_ascii(rows, group, ids, variant=args.variant)
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
