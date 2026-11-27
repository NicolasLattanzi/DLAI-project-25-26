from functools import lru_cache

from leveledit.bases import load_bases
from leveledit.grid import nbs
from leveledit.instructions.programs import program_from_dict
from leveledit.instructions.verifier import verify
from leveledit.library import jolly, load_libraries


def griglia(pred):
    pred = list(pred)
    if len(pred) == 80 and all(isinstance(c, str) for c in pred):
        return [pred[i * 10:(i + 1) * 10] for i in range(8)]
    if len(pred) == 8 and all(len(r) == 10 for r in pred):
        return [list(r) for r in pred]
    raise ValueError("la predizione deve essere 8x10 codici o una lista piatta di 80")


def piatta(pred):
    return [c for riga in griglia(pred) for c in riga]


def soluzioni(record):
    out = []
    for s in record["solutions"]:
        g = list(record["before"])
        for y, x, c in s["changes"]:
            g[y * 10 + x] = c
        out.append(g)
    return out


def _plausibile(T, y, x, t, lib):
    if t in ("MM", "KK"):
        t = ".F"
    n = nbs(T, y, x)
    return (t, n) in lib.ctx or any((t, j) in lib.ctx3 for j in jolly(n))


def _messi(p):
    if p.op == "AND":
        return set().union(*(_messi(q) for q in p.parts))
    return {"ADD": {p.type}, "MOVE": {p.sel.type if p.sel else None}, "DIG2X2": {"~H"},
            "EXTEND": {"~W"}}.get(p.op, set()) - {None}


def celle_plausibili(before, pred, prog, lib):
    T, A = griglia(before), griglia(pred)
    messi = _messi(prog)
    for y in range(8):
        for x in range(10):
            t = A[y][x]
            if t != T[y][x] and t in messi and not (_plausibile(T, y, x, t, lib) or _plausibile(A, y, x, t, lib)):
                return False
    return True


@lru_cache(maxsize=1)
def contesto():
    return {b.id: b for b in load_bases()}, load_libraries()


def is_correct(record, prediction, base=None, lib=None):
    p = piatta(prediction)
    if p in soluzioni(record):
        return True
    if not record.get("solutions_truncated", False):
        return False
    if base is None or lib is None:
        basi, libs = contesto()
        base = base or basi[record["base_id"]]
        lib = lib or libs[base.gfx_group]
    prog = program_from_dict(record["program"])
    if not verify(base, prog, griglia(p), lib=lib)[0]:
        return False
    return celle_plausibili(record["before"], p, prog, lib)
