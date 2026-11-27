import math

import torch
import torch.nn.functional as F

from model.loss import loss_m1


def uscite(B=1):
    return torch.zeros(B, 80, 29), torch.full((B, 80), -20.0), torch.zeros(B, 80, 29)


def soluzioni_vuote(B=1):
    return torch.full((B, 80, 80), -1, dtype=torch.int8), torch.zeros(B, 80, dtype=torch.bool)


def test_sceglie_la_soluzione_piu_vicina():
    p, m, n = uscite()
    s, v = soluzioni_vuote()
    s[0, 0, 5] = 3
    s[0, 1, 7] = 4
    v[0, :2] = True
    m[0, 7] = 20.0
    n[0, 7, 4] = 20.0
    loss, parti = loss_m1(p, m, n, torch.zeros(1, 80, dtype=torch.long), s, v, 33.2)
    assert parti["k"].tolist() == [1]
    assert abs(loss.item() - math.log(29)) < 1e-3


def test_ignora_le_soluzioni_che_non_esistono():
    p, m, n = uscite()
    s, v = soluzioni_vuote()
    s[0, 0, 5] = 3
    v[0, 0] = True
    s[0, 1, 7] = 4
    m[0, 7] = 20.0
    n[0, 7, 4] = 20.0
    _, parti = loss_m1(p, m, n, torch.zeros(1, 80, dtype=torch.long), s, v, 33.2)
    assert parti["k"].tolist() == [0]


def test_una_soluzione_uguale_al_calcolo_diretto():
    torch.manual_seed(0)
    p, m, n = torch.randn(2, 80, 29), torch.randn(2, 80), torch.randn(2, 80, 29)
    prima = torch.randint(0, 29, (2, 80))
    s, v = soluzioni_vuote(2)
    s[0, 0, 3] = 7
    s[0, 0, 4] = 8
    s[1, 0, 60] = 21
    v[:, 0] = True
    loss, _ = loss_m1(p, m, n, prima, s, v, 33.2)
    c = (s[:, 0] >= 0).float()
    atteso = 0
    for b in range(2):
        cel = c[b].bool()
        atteso += (F.cross_entropy(p[b], prima[b])
                   + F.binary_cross_entropy_with_logits(m[b], c[b], pos_weight=torch.tensor(33.2))
                   + F.cross_entropy(n[b][cel], s[b, 0][cel].long()))
    assert torch.allclose(loss, atteso / 2, atol=1e-5)


def test_un_si_mancato_costa_33_volte_un_si_di_troppo():
    p, m, n = uscite()
    s, v = soluzioni_vuote()
    s[0, 0, 0] = 1
    v[0, 0] = True
    _, a = loss_m1(p, m, n, torch.zeros(1, 80, dtype=torch.long), s, v, 33.2)
    m2 = m.clone()
    m2[0, 0] = 20.0
    m2[0, 1] = 20.0
    _, b = loss_m1(p, m2, n, torch.zeros(1, 80, dtype=torch.long), s, v, 33.2)
    assert abs(a["mod"] / b["mod"] - 33.2) < 0.05


def test_bf16():
    p, m, n = (x.to(torch.bfloat16) for x in uscite())
    s, v = soluzioni_vuote()
    s[0, 0, 5] = 3
    v[0, 0] = True
    loss, _ = loss_m1(p, m, n, torch.zeros(1, 80, dtype=torch.long), s, v, 33.2)
    assert loss.dtype == torch.float32 and torch.isfinite(loss)
