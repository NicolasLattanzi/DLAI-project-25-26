import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image

DATI = Path(__file__).resolve().parents[2] / "data" / "dataset"
MODELLO = "LA:dungeons/D6_face_shrine"


def colori(p):
    return [tuple(int(v) for v in c) for c in np.unique(p.reshape(-1, 3), axis=0)]


def ricolora(disegno, palette):
    m = {c: min(palette, key=lambda t: sum((a - b) ** 2 for a, b in zip(c, t))) for c in colori(disegno)}
    return np.array([[m[tuple(int(v) for v in c)] for c in riga] for riga in disegno], dtype=np.uint8)


def luce(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def inverti(p):
    cs = sorted(colori(p), key=luce)
    m = dict(zip(cs, cs[::-1]))
    return np.array([[m[tuple(int(v) for v in c)] for c in riga] for riga in p], dtype=np.uint8)


def schema(p):
    cs = sorted(colori(p), key=luce)
    r = {c: i for i, c in enumerate(cs)}
    return tuple(r[tuple(int(v) for v in c)] for riga in p for c in riga)


def quadratini(stanze, immagini, pos, tipo, oggetto):
    out = {}
    for r in stanze:
        k = pos[r["id"]]
        for y in range(8):
            for x in range(10):
                if r["types"][y][x] == tipo and r["objects"][y][x] == oggetto:
                    q = immagini[k, y * 16:(y + 1) * 16, x * 16:(x + 1) * 16]
                    if r["gfx_group"] in out:
                        assert np.array_equal(out[r["gfx_group"]], q), r["gfx_group"]
                    else:
                        out[r["gfx_group"]] = q.copy()
    return out


def nuovi_blocchi(stanze, immagini, pos):
    pilastri = quadratini(stanze, immagini, pos, "#P", "A6")
    gruppi = {r["gfx_group"] for r in stanze for riga in r["types"] for c in riga if c == "BP"}
    schemi = {schema(p) for p in pilastri.values()}
    out = {}
    for g in sorted(gruppi):
        nuovo = ricolora(pilastri[MODELLO], colori(pilastri[g]))
        if np.array_equal(nuovo, pilastri[g]):
            nuovo = ricolora(inverti(pilastri[MODELLO]), colori(pilastri[g]))
            assert schema(nuovo) not in schemi, g
        assert not np.array_equal(nuovo, pilastri[g]), g
        out[g] = nuovo
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dati", default=str(DATI))
    a = ap.parse_args()
    dati = Path(a.dati)
    stanze = [json.loads(riga) for riga in open(dati / "rooms.jsonl", encoding="utf-8")]
    z = np.load(dati / "images.npz")
    ids, immagini = z["ids"], z["images"].copy()
    pos = {str(i): k for k, i in enumerate(ids)}
    nuovi = nuovi_blocchi(stanze, immagini, pos)
    celle = 0
    for r in stanze:
        k = pos[r["id"]]
        for y in range(8):
            for x in range(10):
                if r["types"][y][x] == "BP":
                    assert r["objects"][y][x] == "A7"
                    immagini[k, y * 16:(y + 1) * 16, x * 16:(x + 1) * 16] = nuovi[r["gfx_group"]]
                    celle += 1
    np.savez_compressed(dati / "images.npz", ids=ids, images=immagini)
    tile = 0
    for gioco, prefisso in (("la", "LA"), ("z1", "Z1")):
        base = dati / "tiles_trainval" / gioco
        indice = json.loads((base / "index.json").read_text(encoding="utf-8"))
        for g, v in indice["groups"].items():
            t = v["tiles"].get("A7")
            if not t or t["name"] != "pushable block":
                continue
            nuovo = nuovi[f"{prefisso}:{g}"]
            for f in {t["file"], *(x["file"] for x in t["variants"])}:
                Image.fromarray(nuovo).save(base / f)
                tile += 1
    print(f"gruppi {len(nuovi)}, celle ridisegnate {celle}, tile ridisegnati {tile}")


if __name__ == "__main__":
    main()
