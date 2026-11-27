"""Verificatore indipendente: controlla le proprieta' di una modifica senza chiamare l'esecutore.

Rimette in codice le regole di selettori e destinazioni (non usa `resolve` ne' `dest_cells`):
un errore dell'una o dell'altra implementazione emerge nel confronto del Compito 15.
Il verificatore non ha la libreria: non giudica plausibilita' o stile, solo le proprieta'.
"""
from itertools import combinations, product

from leveledit.bases import BaseRoom
from leveledit.grid import Grid
from leveledit.instructions.programs import ZONES, Program, Selector, dist, instances
from leveledit.types import TYPES

MAX_DIFF_AND = 12  # oltre questo numero di celle cambiate un AND non si controlla
_VERSO = {"left": (0, -1), "right": (0, 1), "up": (-1, 0), "above": (-1, 0), "down": (1, 0), "below": (1, 0)}
_ESTREMO = {"leftmost": ("x", min), "rightmost": ("x", max), "topmost": ("y", min), "bottommost": ("y", max)}


# ----------------------------------------------------------------------------- piccoli aiuti
def _diff(a: Grid, b: Grid) -> set:
    return {(y, x) for y in range(len(a)) for x in range(len(a[0])) if a[y][x] != b[y][x]}


def _libera(T: Grid, exits: set, c) -> bool:
    """Libera: `.F`, righe 1-6, colonne 1-8, non un'uscita."""
    y, x = c
    return 1 <= y <= 6 and 1 <= x <= 8 and T[y][x] == ".F" and c not in exits


def _pavimento(code: str) -> bool:
    return TYPES[code].cls == "." and code != ".O"


def _cammina(code: str) -> bool:
    return code == "MM" or TYPES[code].walkable


def _forma_ok(T: Grid, after: Grid) -> bool:
    return (len(T) == len(after) and all(len(r) == len(q) for r, q in zip(T, after))
            and len(T) == 8 and len(T[0]) == 10)


# ----------------------------------------------------------------------------- selettori
def _scelte(T: Grid, sel: Selector) -> list[frozenset]:
    """Tutte le scelte valide del selettore (insiemi di celle); [] se non e' ben definito."""
    ins = instances(T, sel.type)
    f = sel.filter
    if f is not None:
        if f[0] == "zone":
            ins = [i for i in ins if all(ZONES[f[1]](y, x) for y, x in i)]
        elif TYPES[sel.type].kind == "region":      # vicino/estremo: solo per tipi a oggetti singoli
            return []
        elif f[0] == "nearest" and ins:
            d = [dist(i, f[1].cells) for i in ins]
            ins = [i for i, v in zip(ins, d) if v == min(d)]
        elif f[0] == "extreme" and ins:
            asse, fn = _ESTREMO[f[1]]
            k = 1 if asse == "x" else 0
            v = [fn(c[k] for c in i) for i in ins]
            ins = [i for i, w in zip(ins, v) if w == fn(v)]
        elif f[0] in ("nearest", "extreme"):
            return []
    n = len(ins)
    if sel.det == "the":
        return [ins[0]] if n == 1 else []
    if sel.det == "a":
        return list(ins) if n >= 2 else []
    if sel.det == "all":
        return [frozenset().union(*ins)] if n else []
    if sel.det == "two":
        return [a | b for a, b in combinations(ins, 2)] if n >= 3 else []
    return []


# ----------------------------------------------------------------------------- destinazioni
def _dest_ok(c, dest) -> bool:
    """La cella `c` soddisfa la destinazione (solo la relazione: liberta' e tipo si controllano a parte)."""
    y, x = c
    if dest.kind == "zone":
        return ZONES[dest.zone](y, x)
    lm = dest.landmark.cells
    if dest.rel == "left":
        return (y, x + 1) in lm
    if dest.rel == "right":
        return (y, x - 1) in lm
    if dest.rel == "above":
        return (y + 1, x) in lm
    if dest.rel == "below":
        return (y - 1, x) in lm
    if dest.rel == "next":
        return any(abs(y - a) + abs(x - b) == 1 for a, b in lm)
    if dest.rel == "near":
        return 1 <= dist([c], lm) <= 2
    return False


# ----------------------------------------------------------------------------- operazioni
def _v_add(T, exits, p, A, D, lib=None):
    if any(A[y][x] != p.type for y, x in D):
        return False, "modifica non richiesta"
    if len(D) != p.count:
        return False, "conteggio"
    if any(not _libera(T, exits, c) for c in D):
        return False, "cella non libera"
    if any(not _dest_ok(c, p.dest) for c in D):
        return False, "posizione"
    return True, ""


def _v_remove(T, exits, p, A, D, lib=None):
    t = p.sel.type
    if any(T[y][x] != t for y, x in D):
        return False, "modifica non richiesta"
    if any(not _pavimento(A[y][x]) for y, x in D):
        return False, "tipo"
    if frozenset(D) not in _scelte(T, p.sel):
        return False, "selezione"
    return True, ""


def _v_replace(T, exits, p, A, D, lib=None):
    if p.op == "REPLACE":
        a = p.to
    else:
        a = "DK" if p.op == "LOCK" else ".O"
    if any(T[y][x] != p.sel.type for y, x in D):
        return False, "modifica non richiesta"
    if any(A[y][x] != a for y, x in D):
        return False, "tipo"
    if frozenset(D) not in _scelte(T, p.sel):
        return False, "selezione"
    return True, ""


def _v_move(T, exits, p, A, D, lib=None):
    t = p.sel.type
    tolte = {c for c in D if T[c[0]][c[1]] == t}
    messe = {c for c in D if A[c[0]][c[1]] == t}
    if D - tolte - messe:
        return False, "modifica non richiesta"
    if len(tolte) != 1 or len(messe) != 1:
        return False, "conteggio"
    (c0,), (c,) = tuple(tolte), tuple(messe)
    if not _pavimento(A[c0[0]][c0[1]]):
        return False, "tipo"
    if frozenset({c0}) not in _scelte(T, p.sel):
        return False, "selezione"
    T1 = [r[:] for r in T]
    T1[c0[0]][c0[1]] = A[c0[0]][c0[1]]          # griglia dopo la rimozione di c0
    if not _libera(T1, exits, c):
        return False, "cella non libera"
    if not _dest_ok(c, p.dest):
        return False, "posizione"
    return True, ""


def _v_dig(T, exits, p, A, D, lib=None):
    if any(A[y][x] != "~H" for y, x in D):
        return False, "modifica non richiesta"
    ys, xs = sorted({c[0] for c in D}), sorted({c[1] for c in D})
    if len(D) != 4 or len(ys) != 2 or len(xs) != 2 or ys[1] - ys[0] != 1 or xs[1] - xs[0] != 1:
        return False, "conteggio" if len(D) != 4 else "selezione"
    if any(not _libera(T, exits, c) for c in D):
        return False, "cella non libera"
    if p.dest is None or p.dest.kind != "zone" or any(not ZONES[p.dest.zone](*c) for c in D):
        return False, "posizione"
    return True, ""


def _plausibile(T: Grid, y: int, x: int, t: str, lib) -> bool:
    """(tipo, vicini su-destra-giu'-sinistra, "OOB" fuori griglia) presente in lib.ctx, o con un vicino a jolly in lib.ctx3."""
    if t in ("MM", "KK"):   # R25: sprite sul pavimento, plausibili come ".F"
        t = ".F"
    n = tuple(T[y + dy][x + dx] if 0 <= y + dy < 8 and 0 <= x + dx < 10 else "OOB"
              for dy, dx in ((-1, 0), (0, 1), (1, 0), (0, -1)))
    return (t, n) in lib.ctx or any((t, n[:i] + ("*",) + n[i + 1:]) in lib.ctx3 for i in range(4))


def _v_extend(T, exits, p, A, D, lib=None):
    if not D or any(A[y][x] != "~W" for y, x in D):
        return False, "modifica non richiesta" if D else "conteggio"
    if any(not _libera(T, exits, c) for c in D):
        return False, "cella non libera"
    dy, dx = _VERSO[p.direction]
    for ch in _scelte(T, p.sel):
        if not all((y - dy, x - dx) in ch for y, x in D):
            continue
        if lib is None:
            return True, ""
        tutte = {(y + dy, x + dx) for y, x in ch}
        tutte = {c for c in tutte if _libera(T, exits, c) and _plausibile(T, c[0], c[1], "~W", lib)}
        if D == tutte:
            return True, ""
        return False, "conteggio"
    return False, "selezione"


def _v_bridge(T, exits, p, A, D, lib=None):
    if not D or any(T[y][x] != "~W" or A[y][x] != "=B" for y, x in D):
        return False, "modifica non richiesta" if D else "conteggio"
    y0, x0 = min(D)
    y1, x1 = max(D)
    for dy, dx in ((0, 1), (1, 0)):                  # una cella sola puo' essere un ponte in entrambi i versi
        if D != {(y0 + dy * i, x0 + dx * i) for i in range(len(D))}:
            continue                                  # non e' un tratto dritto e contiguo in questo verso
        if all(0 <= y < 8 and 0 <= x < 10 and _cammina(T[y][x])
               for y, x in ((y0 - dy, x0 - dx), (y1 + dy, x1 + dx))):
            return True, ""
    return False, "selezione"


def _scritture(p: Program) -> set:
    """Tipi che l'operazione puo' scrivere sulle celle (per il pavimento della rimozione non si sa quale)."""
    if p.op == "AND":
        return _scritture(p.parts[0]) | _scritture(p.parts[1])
    return {"ADD": {p.type}, "MOVE": {p.sel.type if p.sel else None}, "REPLACE": {p.to}, "LOCK": {"DK"},
            "UNLOCK": {".O"}, "DIG2X2": {"~H"}, "EXTEND": {"~W"}, "BRIDGE": {"=B"}}.get(p.op, set()) - {None}


def _puo_scrivere(p: Program, t: str) -> bool:
    """L'operazione (o una sua parte) puo' lasciare il tipo `t` in una cella: lo scrive, o e' un pavimento
    lasciato da una rimozione o dalla cella di partenza di uno spostamento."""
    if p.op == "AND":
        return any(_puo_scrivere(q, t) for q in p.parts)
    return t in _scritture(p) or (p.op in ("REMOVE", "MOVE") and _pavimento(t))


def _legge(p: Program) -> set:
    """Tipi che l'operazione puo' trovare in una cella che cambia (quello che sostituisce/toglie, o ".F" dove scrive)."""
    if p.op == "AND":
        return _legge(p.parts[0]) | _legge(p.parts[1])
    if p.op in ("REMOVE", "REPLACE", "LOCK", "UNLOCK"):
        return {p.sel.type}
    if p.op == "MOVE":
        return {p.sel.type, ".F"}
    return {"BRIDGE": {"~W"}}.get(p.op, {".F"})


def _intermedie(T: Grid, A: Grid, D: set, p1: Program, p2: Program, lib=None):
    """Griglie intermedie candidate: ogni cella cambiata vale il prima, il dopo o (se la prima parte
    la sovrascrive e la seconda la cambia ancora) un tipo che la prima parte scrive.
    Se la seconda parte non puo' scrivere il valore finale di una cella, quella cella non la tocca:
    l'intermedia vale gia' il dopo (riduce molto le combinazioni)."""
    celle = sorted(D)
    scr = _scritture(p1)
    pav = {c for r in T for c in r if _pavimento(c)} | {".F"}   # pavimenti lasciati da una rimozione
    if lib is not None:
        pav |= {t for t in getattr(lib, "obj_type", {}).values() if _pavimento(t)}   # sotto uno sprite, dal layout
    pav = sorted(pav)
    base_o = [[T[y][x], A[y][x]] for y, x in celle]
    letti = _legge(p2)       # se la seconda parte cambia una cella dopo la prima, ci trova un tipo che legge
    ex_w = [sorted(w for w in scr if w not in o and w in letti) for o, _ in zip(base_o, celle)]
    # un pavimento lasciato da una rimozione e poi sovrascritto serve solo dove il dopo non e' un pavimento
    ex_p = [sorted(w for w in pav if w not in o and w in letti) if not _pavimento(T[y][x]) and not _pavimento(A[y][x]) else []
            for o, (y, x) in zip(base_o, celle)]
    fisse = [not _puo_scrivere(p2, A[y][x]) for y, x in celle]
    opz = None
    for livello in (lambda i: base_o[i] + ex_w[i] + ex_p[i], lambda i: base_o[i] + ex_w[i],
                    lambda i: base_o[i] + ex_p[i], lambda i: base_o[i]):
        opz = [[A[celle[i][0]][celle[i][1]]] if fisse[i] else livello(i) for i in range(len(celle))]
        tot = 1
        for o in opz:
            tot *= len(o)
        if tot <= 20000:                              # altrimenti si prova con meno alternative
            break
    for scelta in product(*opz):
        I = [riga[:] for riga in T]
        for (y, x), v in zip(celle, scelta):
            I[y][x] = v
        yield I


def _v_and(T, exits, p, A, D, lib=None):
    if len(D) > MAX_DIFF_AND:
        return False, "troppe modifiche"
    peggiore = (-1, "selezione")
    for I in _intermedie(T, A, D, p.parts[0], p.parts[1], lib):
        if p.parts[0].op == "AND":      # AND annidato: la seconda parte (semplice) scarta quasi tutte le intermedie
            ok2, m2 = _verifica(I, exits, p.parts[1], A, lib)
            if not ok2:
                peggiore = max(peggiore, (1, m2), key=lambda v: v[0])
                continue
        ok1, m1 = _verifica(T, exits, p.parts[0], I, lib)
        if not ok1:
            peggiore = max(peggiore, (0, m1), key=lambda v: v[0])
            continue
        ok2, m2 = _verifica(I, exits, p.parts[1], A, lib)
        if ok2:
            return True, ""
        peggiore = max(peggiore, (1, m2), key=lambda v: v[0])
    return False, peggiore[1]


_OPERAZIONI = {"ADD": _v_add, "REMOVE": _v_remove, "MOVE": _v_move, "REPLACE": _v_replace,
               "LOCK": _v_replace, "UNLOCK": _v_replace, "DIG2X2": _v_dig, "EXTEND": _v_extend,
               "BRIDGE": _v_bridge, "AND": _v_and}


def _verifica(T: Grid, exits: set, prog: Program, A: Grid, lib=None) -> tuple[bool, str]:
    """Controlla che `A` sia un risultato valido di `prog` applicato a `T`."""
    if not _forma_ok(T, A):
        return False, "forma"
    f = _OPERAZIONI.get(prog.op)
    if f is None:
        return False, "operazione sconosciuta"
    return f(T, exits, prog, A, _diff(T, A), lib)


def verify(base: BaseRoom, prog: Program, after: Grid, lib=None) -> tuple[bool, str]:
    """(valido, motivo): la griglia `after` e' un risultato valido di `prog` sulla base; motivo "" se valido.

    `lib` (opzionale) serve solo a EXTEND: con la libreria si richiede l'estensione completa (tutte le celle
    libere e plausibili per "~W" vicine alla regione); senza, basta che le celle cambiate siano un sottoinsieme
    di quelle vicine alla regione scelta."""
    T = base.types
    exits = set(base.exits) | {(y, x) for y in range(len(T)) for x in range(len(T[0])) if TYPES[T[y][x]].cls == "E"}
    return _verifica(T, exits, prog, after, lib)
