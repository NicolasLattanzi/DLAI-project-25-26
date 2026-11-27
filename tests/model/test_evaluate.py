import torch

from leveledit.evaluate import is_correct
from model.data import TIPI, Risorse, carica_split
from model.evaluate import griglia, misure, scegli_tau


def idx(codici):
    return torch.tensor([[TIPI.index(c) for c in g] for g in codici])


def val():
    return carica_split("val", Risorse.carica("cpu"), limite=50)


def test_griglia_segue_la_soglia():
    p = torch.zeros(1, 80, 29)
    p[0, :, 11] = 5
    n = torch.zeros(1, 80, 29)
    n[0, :, 21] = 5
    m = torch.full((1, 80), -10.0)
    m[0, 3] = 0.0
    assert griglia(p, m, n, 0.4)[0, 3] == 21 and griglia(p, m, n, 0.6)[0, 3] == 11
    assert (griglia(p, m, n, 0.4)[0, :3] == 11).all()


def test_misure_risposta_giusta_e_sbagliata():
    es = val()
    dopo = idx([r["after"] for r in es.record])
    g = misure(es, dopo, es.prima)
    assert g["successo"] == 1.0 and g["non_richieste_media"] == 0.0 and g["zero_non_richieste"] == 1.0 and g["perc_celle"] == 1.0
    assert misure(es, es.prima, es.prima)["successo"] == 0.0


def test_errore_di_percezione_e_una_modifica_non_richiesta():
    es = val()
    dopo = idx([r["after"] for r in es.record])
    ferma = next(c for c in range(80) if all(int(es.soluzioni[0, k, c]) < 0 for k in range(80) if es.valide[0, k]))
    dopo[0, ferma] = (int(dopo[0, ferma]) + 1) % 29
    g = misure(es, dopo, es.prima)
    assert g["successo"] == 49 / 50 and abs(g["non_richieste_media"] - 1 / 50) < 1e-9


def test_successo_coincide_con_is_correct():
    es = val()
    dopo = idx([r["after"] for r in es.record])
    dopo[::3, 0] = 0
    attesi = [is_correct(r, [TIPI[i] for i in dopo[j].tolist()]) for j, r in enumerate(es.record)]
    assert misure(es, dopo, es.prima)["successo"] == sum(attesi) / len(attesi)


def test_scegli_tau():
    es = val()
    dopo = idx([r["after"] for r in es.record])
    cambia = dopo != es.prima
    p = torch.full((50, 80, 29), -5.0).scatter(2, es.prima.unsqueeze(2), 5.0)
    sbagliato = torch.where(cambia, dopo, (es.prima + 1) % 29)
    n = torch.full((50, 80, 29), -5.0).scatter(2, sbagliato.unsqueeze(2), 5.0)
    m = torch.where(cambia, torch.tensor(1.0), torch.tensor(0.2))
    tau, g = scegli_tau(es, (p, m, n), [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9])
    assert tau == 0.6 and g["successo"] == 1.0
