import json
from dataclasses import dataclass
from pathlib import Path

DATI = Path(__file__).resolve().parents[2] / "data" / "dataset"


@dataclass
class BaseRoom:
    id: str
    split: str
    source: str
    gfx_group: str
    biome: str
    types: list
    objects: list
    enemies: list
    exits: set
    key: tuple | None
    recipe: dict | None


def load_bases(path=DATI / "rooms.jsonl") -> list[BaseRoom]:
    out = []
    with open(path, encoding="utf-8") as f:
        for riga in f:
            d = json.loads(riga)
            out.append(BaseRoom(d["id"], d["split"], d["source"], d["gfx_group"], d["biome"], d["types"],
                                d["objects"], [tuple(e) for e in d["enemies"]], {tuple(c) for c in d["exits"]},
                                tuple(d["key"]) if d["key"] else None, d["recipe"]))
    return out
