"""Operazioni sulle griglie di tipi (8 righe x 10 colonne di codici a due simboli)."""
from leveledit.types import TYPES

Grid = list[list[str]]
Cell = tuple[int, int]  # (y, x)

OOB = "OOB"
_DIREZIONI = ((-1, 0), (0, 1), (1, 0), (0, -1))  # su, destra, giu', sinistra


def _cammina(code: str) -> bool:
    """Attraversabile: le classi camminabili piu' il nemico MM (si puo' passare dove sta)."""
    return code == "MM" or TYPES[code].walkable


def nbs(T: Grid, y: int, x: int) -> tuple[str, str, str, str]:
    """Vicini nell'ordine su, destra, giu', sinistra; "OOB" fuori griglia."""
    out = []
    for dy, dx in _DIREZIONI:
        ny, nx = y + dy, x + dx
        out.append(T[ny][nx] if 0 <= ny < len(T) and 0 <= nx < len(T[0]) else OOB)
    return tuple(out)


def blocked(T: Grid, y: int, x: int) -> int:
    """Numero di lati non attraversabili (fuori griglia = bloccato, MM = attraversabile)."""
    return sum(1 for n in nbs(T, y, x) if n == OOB or not _cammina(n))


def components(T: Grid) -> dict[Cell, int]:
    """Componenti connesse (4-vicini) delle celle attraversabili: cella -> indice."""
    comp: dict[Cell, int] = {}
    n = 0
    for y in range(len(T)):
        for x in range(len(T[0])):
            if (y, x) in comp or not _cammina(T[y][x]):
                continue
            comp[(y, x)] = n
            pila = [(y, x)]
            while pila:
                cy, cx = pila.pop()
                for dy, dx in _DIREZIONI:
                    p = (cy + dy, cx + dx)
                    if (0 <= p[0] < len(T) and 0 <= p[1] < len(T[0]) and p not in comp
                            and _cammina(T[p[0]][p[1]])):
                        comp[p] = n
                        pila.append(p)
            n += 1
    return comp


def exit_links(T: Grid, exits: set[Cell]) -> set[frozenset[Cell]]:
    """Coppie di uscite collegate da un percorso attraversabile."""
    comp = components(T)
    ex = sorted(c for c in exits if c in comp)
    return {frozenset((a, b)) for i, a in enumerate(ex) for b in ex[i + 1:] if comp[a] == comp[b]}
