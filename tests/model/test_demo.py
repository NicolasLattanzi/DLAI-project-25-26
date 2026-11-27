import numpy as np
import torch
from PIL import Image

from model.demo import ALTEZZA_TITOLO, SCALA, disegna, esegui
from model.model import M1


def test_esegui_da_una_griglia_e_le_probabilita():
    torch.manual_seed(0)
    m = M1().eval()
    dopo, visto, prob = esegui(m, 0.5, torch.randn(80, 384), torch.randn(9, 768))
    assert dopo.shape == (80,) and visto.shape == (80,) and prob.shape == (80,)
    assert ((prob >= 0) & (prob <= 1)).all()


def test_disegna_mette_i_pannelli_affiancati_e_segna_le_celle(tmp_path):
    nero = np.zeros((128, 160, 3), dtype=np.uint8)
    f = tmp_path / "demo.png"
    disegna([("prima", nero, []), ("dopo", nero, [(16, (255, 40, 40))])], f)
    out = np.array(Image.open(f).convert("RGB"))
    largo = 160 * SCALA
    assert out.shape == (128 * SCALA + ALTEZZA_TITOLO, 2 * largo + 12, 3)
    corpo = out[ALTEZZA_TITOLO:]
    assert corpo[:, :largo].max() == 0 and corpo[:, -largo:].max() > 0
