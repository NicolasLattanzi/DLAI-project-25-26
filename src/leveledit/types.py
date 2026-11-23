"""I 29 tipi di tessera a due simboli e la conversione da id oggetto (ROM) a tipo."""
import json
from dataclasses import dataclass
from pathlib import Path

_QUI = Path(__file__).resolve().parent
_MAPPINGS = _QUI.parent / "la_extract" / "mappings"

CLASSI_CAMMINABILI = {".", "=", "E", "K"}


@dataclass(frozen=True)
class TypeInfo:
    code: str
    cls: str
    name_it: str
    sing: list
    plur: list | None
    walkable: bool
    kind: str  # "item" | "region" | "fixed"


def _carica_tipi():
    tipi = {}
    for t in json.loads((_QUI / "types.json").read_text(encoding="utf-8")):
        tipi[t["code"]] = TypeInfo(t["code"], t["cls"], t["name_it"], t["sing"], t["plur"],
                                   t["cls"] in CLASSI_CAMMINABILI, t["kind"])
    return tipi


TYPES = _carica_tipi()

_oggetti = {}  # cache dei file di mappatura


def _mappa(nome):
    if nome not in _oggetti:
        _oggetti[nome] = json.loads((_MAPPINGS / nome).read_text(encoding="utf-8"))
    return _oggetti[nome]


def _voce(region, obj_id):
    """Voce della mappatura per un oggetto, con le sostituzioni della Color Dungeon."""
    if region == "overworld":
        return _mappa("objects_overworld.json")["objects"].get(obj_id, {})
    indoor = _mappa("objects_indoor.json")
    e = dict(indoor["objects"].get(obj_id, {}))
    ov = indoor["color_dungeon_overrides"].get(obj_id)
    if region == "color" and isinstance(ov, dict):
        e.update(ov)
    return e


# tag -> tipo per gli oggetti solidi (categoria 1), in ordine di priorita'
_SOLIDI = [("cliff", "#C"), ("tree", "#T"), ("building", "#H"), ("statue", "#S"), ("torch", "#F"),
           ("furniture", "#U"), ("chest", "#X"), ("rock", "#R"), ("stone_block", "#P")]


def _tipo(e):
    c = e.get("category")
    tag = set(e.get("tags", []))
    if c is None:
        return "#W"
    if c == 0:
        return "_V"
    if c == 1:
        for t, codice in _SOLIDI:
            if t in tag:
                return codice
        return "#W"  # compresi i muri bombabili non nascosti
    if c == 2:
        if "door_half1" in tag or "bombed_passage" in tag:
            return ".O"
        if "grass" in tag:
            return ".G"
        if "shallow_water" in tag:
            return ".S"
        if "steps" in tag or "ladder" in tag:
            return ".T"
        return ".F"
    if c == 3:
        if "pit" in tag:
            return "~H"
        if "lava" in tag:
            return "~L"
        if "spikes" in tag:
            return "#P"
        return "~W"
    if c == 4:
        return "=B"
    if c == 5:
        return "DK"  # porte con chiave e porte del boss
    if c == 7:
        if "bush" in tag:
            return "BU"
        if "pushable" in tag:
            return "BP"
        if "removable" in tag:
            return "BC"
        return "BV"
    if c == 8:
        return "ED" if ("cave_door" in tag or "house_door" in tag) else "ES"
    return "#W"


def type_of_object(region: str, obj_id: str) -> str:
    return _tipo(_voce(region, obj_id))


def cls_of(code: str) -> str:
    return TYPES[code].cls
