"""Accesso ai dati delle stanze di Link's Awakening DX (U) v1.0 tramite i parser di LADXR.

Questo modulo NON contiene dati del gioco: legge tutto dalla ROM a runtime.

Fonti (verificate sul codice, non a memoria):
  - LADXR (third_party/LADXR): romTables.py, roomEditor.py, roomInfo.py, mapexport.py, entityData.py
  - zladx/LADX-Disassembly (third_party/LADX-Disassembly):
      src/constants/physics.asm, src/data/objects/physics.asm, src/code/bank0.asm (GetObjectPhysicsFlags),
      src/data/maps/layouts.asm, src/constants/maps.asm, src/constants/gfx.asm
"""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PKG_DIR = Path(__file__).resolve().parent
MAPPINGS_DIR = PKG_DIR / "mappings"
DEFAULT_LADXR = REPO_ROOT / "third_party" / "LADXR"
DEFAULT_ROM_DIR = REPO_ROOT / "src" / "rom"
DEFAULT_OUT = REPO_ROOT / "data" / "la_local"

# ROM richiesta da LADXR: Link's Awakening DX (U) v1.0
EXPECTED_SHA1 = "d90ac17e9bf17b6c61624ad9f05447bdb5efc01a"

# Tabelle dei physics flag (bank 0x08). GetObjectPhysicsFlags (00:2A12) indicizza
# OverworldObjectPhysicFlags (08:4AD4) con l'object id; per gli interni il chiamante somma 0x100
# (-> Indoors1ObjectPhysicFlags 08:4BD4) e per la Color Dungeon si parte da Indoors1 (-> Indoors2 08:4CD4).
PHYSICS_ADDR = {"overworld": 0x0AD4, "indoor": 0x0BD4, "color": 0x0CD4}

# Range degli id stanza (convenzione LADXR)
OVERWORLD_ROOMS = range(0x000, 0x100)
INDOOR_A_ROOMS = range(0x100, 0x200)
INDOOR_B_ROOMS = range(0x200, 0x2FF)  # 0x2FF non esiste (la tabella indoor B ha 0xFF voci)
COLOR_ROOMS = range(0x300, 0x316)

# Layout delle minimappe (bank 0x14:0x4220, 8x8 byte ciascuno, src/data/maps/layouts.asm).
# Indice layout -> map id. Il 9 e' vuoto, il 10 sono passaggi di caverne (MAP_CAVE_B),
# il 12 e' Eagle's Tower dopo il crollo (stesse stanze del 6, non usato qui).
LAYOUT_TO_MAP = {0: 0x00, 1: 0x01, 2: 0x02, 3: 0x03, 4: 0x04, 5: 0x05, 6: 0x06, 7: 0x07, 8: 0x08,
                 10: 0x0A, 11: 0xFF}


def find_rom(rom_dir: Path = DEFAULT_ROM_DIR) -> Path:
    cands = [p for p in rom_dir.glob("*") if p.suffix.lower() in (".gb", ".gbc")]
    for p in cands:
        if hashlib.sha1(p.read_bytes()).hexdigest() == EXPECTED_SHA1:
            return p
    raise FileNotFoundError(f"Nessuna ROM LADX (U) v1.0 (sha1 {EXPECTED_SHA1}) in {rom_dir}")


def region_of(room: int) -> str:
    if room < 0x100:
        return "overworld"
    if room >= 0x300:
        return "color"
    return "indoor"


def all_room_ids():
    yield from OVERWORLD_ROOMS
    yield from INDOOR_A_ROOMS
    yield from INDOOR_B_ROOMS
    yield from COLOR_ROOMS


def load_json(name: str):
    with open(MAPPINGS_DIR / name, encoding="utf-8") as f:
        return json.load(f)


class Game:
    """Wrapper sulla ROM caricata con LADXR."""

    def __init__(self, rom_path: Path | None = None, ladxr_path: Path | None = None, allow_modified: bool = False,
                 map_id_fallback: dict | None = None):
        """allow_modified=True accetta una ROM diversa dalla v1.0 originale, purche' costruita sullo stesso
        motore (es. LADX-Zelda1, generata con LADX-Hackers-Toolbox a partire dalla v1.0)."""
        rom_path = Path(rom_path) if rom_path else find_rom()
        data = rom_path.read_bytes()
        sha1 = hashlib.sha1(data).hexdigest()
        if sha1 != EXPECTED_SHA1 and not allow_modified:
            raise ValueError(f"ROM inattesa (sha1 {sha1}); serve LADX (U) v1.0 {EXPECTED_SHA1}")
        self.rom_sha1 = sha1
        ladxr = Path(ladxr_path) if ladxr_path else DEFAULT_LADXR
        if not (ladxr / "roomEditor.py").exists():
            raise FileNotFoundError(f"LADXR non trovato in {ladxr} (clonare https://github.com/daid/LADXR)")
        if str(ladxr) not in sys.path:
            sys.path.insert(0, str(ladxr))

        from romTables import ROMWithTables
        from roomEditor import RoomEditor, ObjectWarp
        from mapexport import MapExport
        import entityData

        self._RoomEditor = RoomEditor
        self._ObjectWarp = ObjectWarp
        self.entity_names = list(entityData.NAME)
        self.rom = ROMWithTables(io.BytesIO(data))
        with contextlib.redirect_stdout(io.StringIO()):  # MapExport stampa avvisi "Missing map_id"
            self._me = MapExport(self.rom, overworld=False, underworld=False, dungeons=[], entities=False)
        # In una ROM modificata alcune stanze interne non sono raggiunte dai warp che LADXR usa per
        # dedurre la mappa: si usa la mappa della stessa stanza nell'estrazione di riferimento.
        self.map_id_from_fallback = set()
        for r, m in (map_id_fallback or {}).items():
            info = self._me.room_map_info(r)
            if info.map_id is None and m is not None:
                info.map_id = m
                self.map_id_from_fallback.add(r)
        self.entity_data = entityData.EntityData(self.rom)

        b8 = self.rom.banks[0x08]
        self.physics = {k: bytes(b8[a:a + 0x100]) for k, a in PHYSICS_ADDR.items()}
        # Controllo contro src/data/objects/physics.asm: 00=SOLID, 0A=GRASS, 0E=DEEP_WATER, 20=REMOVABLE
        ow = self.physics["overworld"]
        assert (ow[0x00], ow[0x0A], ow[0x0E], ow[0x20]) == (0x01, 0x06, 0x07, 0x30), "tabella physics errata"

        self.layout_pos = {}    # room -> (layout index, x, y) (prima occorrenza)
        self.layout_cells = {}  # layout index -> {(x, y): room}
        for n in LAYOUT_TO_MAP:
            addr = 0x0220 + n * 64
            cells = self.layout_cells.setdefault(n, {})
            for y in range(8):
                for x in range(8):
                    b = self.rom.banks[0x14][addr + x + y * 8]
                    room = b + 0x100 + (0x100 if n > 5 else 0) + (0x100 if n == 11 else 0)
                    if b == 0 and not (n == 11 and (x, y) == (1, 3)):
                        continue
                    if room == 0x2FE and n == 10:  # banana sale room: mappa 0x10, non del layout caverne
                        continue
                    self.layout_pos.setdefault(room, (n, x, y))
                    cells[(x, y)] = room
        self._render_cache = {}

    # ------------------------------------------------------------------ dati stanza
    def room(self, room: int) -> dict:
        re_ = self._RoomEditor(self.rom, room)
        info = self._me.room_map_info(room)
        tiles = re_.getTileArray()
        region = region_of(room)
        phys = self.physics[region]
        warps = []
        for w in re_.getWarps():
            warps.append({"warp_type": w.warp_type, "map_id": w.map_nr, "target_room": w.room,
                          "target_x": w.target_x, "target_y": w.target_y})
        ents = []
        for x, y, t in re_.entities:
            ents.append({"x": x, "y": y, "entity_id": t, "name": self.entity_names[t]})
        lp = self.layout_pos.get(room)
        return {
            "room_id": room,
            "region": region,
            "map_id": info.map_id if region != "overworld" else None,
            "sidescroll": bool(info.sidescroll),
            "table_pos": {"x": room & 0x0F, "y": (room >> 4) & 0x0F},
            "layout_pos": None if lp is None else {"layout": lp[0], "x": lp[1], "y": lp[2]},
            "animation_id": re_.animation_id,
            "floor_object": re_.floor_object,
            "num_objects": len(re_.objects),
            "objects": list(tiles),                       # 80 object id (riga per riga, 10 colonne)
            "physics": [phys[t] for t in tiles],
            "entities": ents,
            "warps": warps,
        }

    def neighbors(self, room: int, map_id, direction: str):
        """Stanze adiacenti nella direzione data ('left','right','up','down'), come le calcola il gioco
        (src/code/room_transition.asm): per le mappe con minimappa (hMapId < 0x0B e Color Dungeon) si
        sposta la posizione nella minimappa 8x8 (IndoorRoomIncrement = +-1, +-8); per gli altri interni e
        per l'overworld l'id stanza cambia di +-1 / +-16 (OverworldRoomIncrement)."""
        dx, dy = {"left": (-1, 0), "right": (1, 0), "up": (0, -1), "down": (0, 1)}[direction]
        if room >= 0x100 and map_id is not None and (map_id < 0x0B or map_id == 0xFF):
            layout = next((n for n, m in LAYOUT_TO_MAP.items() if m == map_id), None)
            if layout is None:
                return []
            cells = self.layout_cells[layout]
            out = []
            for (x, y), r in cells.items():
                if r == room and (x + dx, y + dy) in cells:
                    out.append(cells[(x + dx, y + dy)])
            return out
        low = room & 0xFF
        x, y = (low & 0x0F) + dx, (low >> 4) + dy
        if not (0 <= x < 16 and 0 <= y < 16):
            return []
        return [(room & 0xF00) | (y << 4) | x]

    def chest_item(self, room: int):
        """Contenuto del forziere della stanza (bank 0x14:0x0560 + room, come locations/chest.py di LADXR).
        Ritorna il nome LADXR dell'oggetto (es. 'KEY3', 'NIGHTMARE_KEY2', 'RUPEES_20') o '0xNN' se ignoto."""
        if room >= 0x300:
            return None
        if not hasattr(self, "_chest_names"):
            from locations.constants import CHEST_ITEMS
            self._chest_names = {}
            for k, v in CHEST_ITEMS.items():
                self._chest_names.setdefault(v, k)
        b = self.rom.banks[0x14][0x0560 + room]
        return self._chest_names.get(b, f"0x{b:02X}")

    # ------------------------------------------------------------------ grafica (solo uso locale!)
    def render(self, room: int):
        """Immagine 160x128 della stanza con la grafica originale (PIL.Image)."""
        if room not in self._render_cache:
            with contextlib.redirect_stdout(io.StringIO()):
                self._render_cache[room] = self._me.buildRoom(room)
            if len(self._render_cache) > 64:
                self._render_cache.pop(next(iter(self._render_cache)))
        return self._render_cache[room]
