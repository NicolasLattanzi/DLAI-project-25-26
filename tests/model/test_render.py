import numpy as np

from model.render import Libreria, ridisegna


def quadratino(img, c):
    return img[c // 10 * 16:(c // 10 + 1) * 16, c % 10 * 16:(c % 10 + 1) * 16]


def stanza_finta():
    img = np.zeros((128, 160, 3), dtype=np.uint8)
    for c in range(80):
        img[c // 10 * 16:(c // 10 + 1) * 16, c % 10 * 16:(c % 10 + 1) * 16] = c
    return img


def test_le_celle_ferme_restano_uguali():
    img = stanza_finta()
    prima = [".F"] * 80
    prima[5] = "BV"
    dopo = list(prima)
    dopo[7] = "BV"
    out = ridisegna(img, prima, dopo, "nessuno", Libreria(np.zeros((0, 128, 160, 3), np.uint8), []))
    for c in range(80):
        if c != 7:
            assert np.array_equal(quadratino(out, c), quadratino(img, c))


def test_tipo_presente_nella_stanza_copia_la_cella_piu_vicina():
    img = stanza_finta()
    prima = [".F"] * 80
    prima[5] = "BV"
    prima[60] = "BV"
    dopo = list(prima)
    dopo[7] = "BV"
    out = ridisegna(img, prima, dopo, "nessuno", Libreria(np.zeros((0, 128, 160, 3), np.uint8), []))
    assert np.array_equal(quadratino(out, 7), quadratino(img, 5))


def test_tipo_assente_prende_il_quadratino_dalla_libreria_del_gruppo():
    img = stanza_finta()
    altra = np.full((1, 128, 160, 3), 200, dtype=np.uint8)
    altra[0, 16:32, 32:48] = 77
    tipi = [[".F"] * 10 for _ in range(8)]
    tipi[1][2] = "KK"
    lib = Libreria(altra, [{"split": "train", "gfx_group": "G", "types": tipi}])
    prima = [".F"] * 80
    dopo = list(prima)
    dopo[40] = "KK"
    out = ridisegna(img, prima, dopo, "G", lib)
    assert (quadratino(out, 40) == 77).all()
