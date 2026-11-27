import torch

from model.model import M1


def conta(m):
    return sum(p.numel() for p in m.parameters())


def test_parametri():
    assert conta(M1()) == 14_673_851
    assert conta(M1(bozza=True)) == 14_673_851 + 30 * 384


def test_forme():
    m = M1().eval()
    p, c, n = m(torch.randn(3, 80, 384), torch.randn(3, 12, 768), torch.zeros(3, 12, dtype=torch.bool))
    assert p.shape == (3, 80, 29) and c.shape == (3, 80) and n.shape == (3, 80, 29)


def test_bozza():
    m = M1(bozza=True).eval()
    b = torch.full((2, 80), 29)
    b[0, 5] = 21
    p, c, n = m(torch.randn(2, 80, 384), torch.randn(2, 7, 768), torch.zeros(2, 7, dtype=torch.bool), bozza=b)
    assert c.shape == (2, 80)


def test_padding_non_cambia_le_uscite():
    torch.manual_seed(0)
    m = M1().eval()
    celle, testo = torch.randn(1, 80, 384), torch.randn(1, 9, 768)
    a = m(celle, testo, torch.zeros(1, 9, dtype=torch.bool))
    testo2 = torch.cat([testo, torch.randn(1, 6, 768)], 1)
    pad2 = torch.cat([torch.zeros(1, 9, dtype=torch.bool), torch.ones(1, 6, dtype=torch.bool)], 1)
    b = m(celle, testo2, pad2)
    for x, y in zip(a, b):
        assert torch.allclose(x, y, atol=1e-5)
