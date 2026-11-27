import json
from collections import Counter, defaultdict

import numpy as np

from model.data import DATI

CELLA = 16
COLORI = {"#": (90, 90, 90), "~": (40, 90, 200), ".": (120, 170, 90), "=": (150, 110, 60), "D": (160, 90, 30),
          "B": (140, 100, 50), "E": (200, 200, 60), "K": (230, 200, 30), "M": (200, 40, 40), "_": (0, 0, 0)}


def quadratino(img, y, x):
    return img[y * CELLA:(y + 1) * CELLA, x * CELLA:(x + 1) * CELLA]


class Libreria:
    def __init__(self, immagini, stanze):
        self.immagini = immagini
        self.per_gruppo = defaultdict(list)
        self.cache = {}
        for k, r in enumerate(stanze):
            if r["split"] == "train":
                self.per_gruppo[r["gfx_group"]].append((k, r["types"]))

    @classmethod
    def carica(cls):
        z = np.load(DATI / "images.npz")
        stanze = {}
        with open(DATI / "rooms.jsonl", encoding="utf-8") as f:
            for riga in f:
                r = json.loads(riga)
                stanze[r["id"]] = r
        return cls(z["images"], [stanze[str(i)] for i in z["ids"]])

    def tile(self, gruppo, tipo):
        if (gruppo, tipo) not in self.cache:
            conta, esempio = Counter(), {}
            for k, tipi in self.per_gruppo.get(gruppo, []):
                for y in range(8):
                    for x in range(10):
                        if tipi[y][x] == tipo:
                            p = quadratino(self.immagini[k], y, x)
                            conta[p.tobytes()] += 1
                            esempio[p.tobytes()] = p
            self.cache[(gruppo, tipo)] = esempio[conta.most_common(1)[0][0]].copy() if conta else None
        return self.cache[(gruppo, tipo)]


def vicina(prima, tipo, y, x):
    celle = [(c // 10, c % 10) for c in range(80) if prima[c] == tipo]
    return min(celle, key=lambda p: (p[0] - y) ** 2 + (p[1] - x) ** 2) if celle else None


def ridisegna(immagine, prima, dopo, gruppo, libreria):
    out = immagine.copy()
    for c in range(80):
        if dopo[c] == prima[c]:
            continue
        y, x = c // 10, c % 10
        sorgente = vicina(prima, dopo[c], y, x)
        if sorgente is not None:
            nuovo = quadratino(immagine, *sorgente)
        else:
            nuovo = libreria.tile(gruppo, dopo[c])
            if nuovo is None:
                nuovo = np.empty((CELLA, CELLA, 3), np.uint8)
                nuovo[:] = COLORI.get(dopo[c][0], (255, 0, 255))
        out[y * CELLA:(y + 1) * CELLA, x * CELLA:(x + 1) * CELLA] = nuovo
    return out
