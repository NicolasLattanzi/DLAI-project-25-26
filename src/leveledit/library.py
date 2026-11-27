import json
from dataclasses import dataclass, field
from pathlib import Path

LIBRERIE = Path(__file__).resolve().parents[2] / "data" / "librerie_train.json"


@dataclass
class GroupLibrary:
    hpairs: set = field(default_factory=set)
    vpairs: set = field(default_factory=set)
    ctx: set = field(default_factory=set)
    ctx3: set = field(default_factory=set)
    style: dict = field(default_factory=dict)
    max_count: dict = field(default_factory=dict)
    obj_type: dict = field(default_factory=dict)
    rooms: list = field(default_factory=list)


def jolly(vicini: tuple) -> list[tuple]:
    return [vicini[:i] + ("*",) + vicini[i + 1:] for i in range(4)]


def load_libraries(path=LIBRERIE) -> dict[str, GroupLibrary]:
    dati = json.loads(Path(path).read_text(encoding="utf-8"))
    return {g: GroupLibrary(ctx={(t, tuple(n)) for t, n in d["ctx"]},
                            ctx3={(t, tuple(n)) for t, n in d["ctx3"]},
                            obj_type=dict(d["obj_type"]))
            for g, d in dati.items()}
