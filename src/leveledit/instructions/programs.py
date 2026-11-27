"""Programmi di istruzione: tipi di dato, inventario degli oggetti e risoluzione di selettori e destinazioni."""
from dataclasses import dataclass
from itertools import combinations
from typing import Callable, Optional

from leveledit.grid import Cell, Grid, nbs
from leveledit.library import GroupLibrary, jolly
from leveledit.types import TYPES

_DIREZIONI = ((-1, 0), (0, 1), (1, 0), (0, -1))
_LATO = {"left": (0, -1), "right": (0, 1), "above": (-1, 0), "below": (1, 0)}
MAX_DUE = 40  # massimo di combinazioni per "two"


@dataclass(frozen=True)
class Landmark:
    """Punto di riferimento: un tipo con una sola istanza nella stanza e le sue celle."""
    type: str
    cells: frozenset


@dataclass(frozen=True)
class Selector:
    """Quale oggetto: `det` in the/a/all/two; `filter` None, ("nearest", Landmark),
    ("extreme", leftmost|rightmost|topmost|bottommost) o ("zone", nome).
    `form` (solo per il testo): indice della forma linguistica da usare al posto di una scelta casuale."""
    type: str
    det: str
    filter: Optional[tuple] = None
    form: Optional[int] = None


@dataclass(frozen=True)
class Dest:
    """Dove: relativa a un riferimento (kind "rel") o in una zona (kind "zone")."""
    kind: str
    rel: Optional[str] = None
    landmark: Optional[Landmark] = None
    zone: Optional[str] = None


@dataclass(frozen=True)
class Program:
    """Un'istruzione: operazione + selettore/destinazione (l'esecuzione e' in un altro modulo)."""
    op: str
    type: Optional[str] = None
    count: int = 1
    sel: Optional[Selector] = None
    dest: Optional[Dest] = None
    to: Optional[str] = None
    direction: Optional[str] = None
    parts: tuple = ()


ZONES: dict[str, Callable[[int, int], bool]] = {
    "top-left corner": lambda y, x: y < 4 and x < 5,
    "top-right corner": lambda y, x: y < 4 and x >= 5,
    "bottom-left corner": lambda y, x: y >= 4 and x < 5,
    "bottom-right corner": lambda y, x: y >= 4 and x >= 5,
    "middle of the room": lambda y, x: 3 <= y <= 4 and 3 <= x <= 6,
    "top wall": lambda y, x: y == 1,
    "bottom wall": lambda y, x: y == 6,
    "left wall": lambda y, x: x == 1,
    "right wall": lambda y, x: x == 8,
}

# Tipi che non possono essere punti di riferimento (troppo diffusi o senza forma propria).
# "#W" (muro): una cella di muro isolata si confonde con le zone dei muri (R32).
_NO_RIFERIMENTO = {".G", ".S", ".F", "#W"}


def instances(T: Grid, t: str) -> list[frozenset]:
    """Istanze del tipo `t`: componenti 4-connesse per le regioni, celle singole per gli altri tipi."""
    celle = [(y, x) for y in range(len(T)) for x in range(len(T[0])) if T[y][x] == t]
    if TYPES[t].kind != "region":
        return [frozenset([c]) for c in celle]
    insieme, visti, comp = set(celle), set(), []
    for c in celle:
        if c in visti:
            continue
        visti.add(c)
        pila, cur = [c], {c}
        while pila:
            a, b = pila.pop()
            for dy, dx in _DIREZIONI:
                q = (a + dy, b + dx)
                if q in insieme and q not in visti:
                    visti.add(q)
                    cur.add(q)
                    pila.append(q)
        comp.append(frozenset(cur))
    return comp


def landmarks(T: Grid) -> list[Landmark]:
    """Tipi con una sola istanza (esclusi .G, .S, .F, #W), in ordine di tipo presente nella griglia."""
    presenti = sorted({c for riga in T for c in riga} - _NO_RIFERIMENTO)
    out = []
    for t in presenti:
        ins = instances(T, t)
        if len(ins) == 1:
            out.append(Landmark(t, ins[0]))
    return out


def dist(a, b) -> int:
    """Distanza di Manhattan minima tra due insiemi di celle."""
    return min(abs(p[0] - q[0]) + abs(p[1] - q[1]) for p in a for q in b)


_ESTREMI = {
    "leftmost": lambda i: min(c[1] for c in i),
    "rightmost": lambda i: -max(c[1] for c in i),
    "topmost": lambda i: min(c[0] for c in i),
    "bottommost": lambda i: -max(c[0] for c in i),
}


def resolve(T: Grid, sel: Selector) -> list[frozenset]:
    """Scelte possibili del selettore, in ordine di prima cella (riga, colonna); [] se non e' ben definito."""
    ins = sorted(instances(T, sel.type), key=min)
    f = sel.filter
    if f is not None:
        if f[0] != "zone" and TYPES[sel.type].kind == "region":
            return []
        if f[0] == "zone":
            ins = [i for i in ins if all(ZONES[f[1]](*c) for c in i)]
        elif f[0] == "nearest":
            if not ins:
                return []
            m = min(dist(i, f[1].cells) for i in ins)
            ins = [i for i in ins if dist(i, f[1].cells) == m]
        elif f[0] == "extreme":
            if not ins:
                return []
            m = min(_ESTREMI[f[1]](i) for i in ins)
            ins = [i for i in ins if _ESTREMI[f[1]](i) == m]
    d = sel.det
    if d == "the":
        return [ins[0]] if len(ins) == 1 else []
    if d == "a":
        return ins if len(ins) >= 2 else []
    if d == "all":
        return [frozenset().union(*ins)] if ins else []
    if d == "two":
        return [a | b for a, b in combinations(ins, 2)][:MAX_DUE] if len(ins) >= 3 else []
    return []


def _plausibile(T: Grid, y: int, x: int, t: str, lib: GroupLibrary) -> bool:
    """(tipo nuovo, vicini) visto nella libreria, anche con un vicino a jolly.
    MM e KK (sprite sul pavimento, R25) si controllano come ".F"."""
    if t in ("MM", "KK"):
        t = ".F"
    n = nbs(T, y, x)
    return (t, n) in lib.ctx or any((t, j) in lib.ctx3 for j in jolly(n))


def dest_cells(T: Grid, exits: set, dest: Dest, t: str, lib: GroupLibrary) -> list[Cell]:
    """Celle libere (.F, righe 1-6, colonne 1-8, non uscite) della destinazione dove `t` e' plausibile."""
    if dest.kind == "rel":
        lm = dest.landmark.cells
        if dest.rel in _LATO:
            dy, dx = _LATO[dest.rel]
            cand = {(y + dy, x + dx) for y, x in lm}
        elif dest.rel == "next":
            cand = {(y + dy, x + dx) for y, x in lm for dy, dx in _DIREZIONI}
        else:  # near
            cand = {(y, x) for y in range(8) for x in range(10) if 0 < dist([(y, x)], lm) <= 2}
    else:
        zona = ZONES[dest.zone]
        cand = {(y, x) for y in range(8) for x in range(10) if zona(y, x)}
    return [(y, x) for y in range(1, 7) for x in range(1, 9)
            if (y, x) in cand and T[y][x] == ".F" and (y, x) not in exits and _plausibile(T, y, x, t, lib)]


# ----------------------------------------------------------------------------- serializzazione
def _lm_a_dict(lm: Landmark) -> dict:
    return {"type": lm.type, "cells": sorted([y, x] for y, x in lm.cells)}


def _lm_da_dict(d: dict) -> Landmark:
    return Landmark(d["type"], frozenset((y, x) for y, x in d["cells"]))


def program_to_dict(prog: Program) -> dict:
    """Programma -> dizionario JSON (insiemi e tuple diventano liste ordinate); inverso di `program_from_dict`."""
    sel = None
    if prog.sel is not None:
        f = prog.sel.filter
        if f is not None:
            f = [f[0], _lm_a_dict(f[1]) if f[0] == "nearest" else f[1]]
        sel = {"type": prog.sel.type, "det": prog.sel.det, "filter": f, "form": prog.sel.form}
    dest = None
    if prog.dest is not None:
        d = prog.dest
        dest = {"kind": d.kind, "rel": d.rel, "zone": d.zone,
                "landmark": None if d.landmark is None else _lm_a_dict(d.landmark)}
    return {"op": prog.op, "type": prog.type, "count": prog.count, "sel": sel, "dest": dest, "to": prog.to,
            "direction": prog.direction, "parts": [program_to_dict(p) for p in prog.parts]}


def program_from_dict(d: dict) -> Program:
    """Dizionario JSON -> programma identico all'originale."""
    sel = None
    if d["sel"] is not None:
        s = d["sel"]
        f = s["filter"]
        if f is not None:
            f = (f[0], _lm_da_dict(f[1]) if f[0] == "nearest" else f[1])
        sel = Selector(s["type"], s["det"], f, s["form"])
    dest = None
    if d["dest"] is not None:
        x = d["dest"]
        dest = Dest(x["kind"], x["rel"], None if x["landmark"] is None else _lm_da_dict(x["landmark"]), x["zone"])
    return Program(d["op"], d["type"], d["count"], sel, dest, d["to"], d["direction"],
                   tuple(program_from_dict(p) for p in d["parts"]))
