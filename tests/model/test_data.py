import numpy as np
import torch

from model.data import TIPI, Risorse, carica_split, prepara_batch, solo_segnata


def test_tipi():
    assert len(TIPI) == 29 and TIPI[0] == "_V" and TIPI[22] == "BP" and TIPI[28] == "MM"


def test_val_completa():
    ris = Risorse.carica("cpu")
    es = carica_split("val", ris)
    assert len(es.record) == 976 and es.prima.shape == (976, 80)
    assert es.soluzioni.shape == (976, 80, 80) and es.soluzioni.dtype == torch.int8
    assert es.valide.sum(1).tolist() == [r["n_solutions"] for r in es.record]
    for i in (0, 500, 975):
        r = es.record[i]
        assert es.prima[i].tolist() == [TIPI.index(c) for c in r["before"]]
        for k, s in enumerate(r["solutions"]):
            assert int((es.soluzioni[i, k] >= 0).sum()) == len(s["changes"])
            for y, x, c in s["changes"]:
                assert int(es.soluzioni[i, k, y * 10 + x]) == TIPI.index(c)
    assert set(es.origine) <= {"LA", "Z1", "GEN"}
    assert len(es.bioma) == 976


def test_batch_collega_stanza_e_frase():
    ris = Risorse.carica("cpu")
    es = carica_split("val", ris, limite=8)
    b = prepara_batch(ris, es, torch.arange(8))
    F = np.load("data/dataset/features_dinov3_s16.npy", mmap_mode="r")
    from flan_t5.text_features import carica
    T = carica()
    for i, r in enumerate(es.record):
        assert torch.equal(b["celle"][i], torch.tensor(np.asarray(F[ris.pos_stanza[r["base_id"]]]), dtype=torch.float32))
        v = torch.tensor(np.asarray(T[r["text"]]), dtype=torch.float32)
        n = v.shape[0]
        assert int((~b["pad"][i]).sum()) == n and torch.equal(b["testo"][i, :n], v)
    assert b["celle"].shape == (8, 80, 384) and b["testo"].shape[0] == 8 and b["testo"].shape[2] == 768


def test_solo_segnata():
    ris = Risorse.carica("cpu")
    es = solo_segnata(carica_split("val", ris))
    assert es.valide.sum(1).eq(1).all() and es.valide[:, 0].all()
