"""Vettori DINOv3 delle immagini delle stanze: un vettore per cella (patch 16x16)."""
import argparse
import hashlib
import json
import re
import time
from pathlib import Path

import numpy as np
import torch

MODELLO = "facebook/dinov3-vits16-pretrain-lvd1689m"
MEDIA = (0.485, 0.456, 0.406)
DEV_STD = (0.229, 0.224, 0.225)
PATCH = 16
RIGHE, COLONNE = 8, 10
DATA = Path(__file__).resolve().parents[2] / "data" / "dataset"   # percorso dalla radice, non dalla cartella corrente


def _media_std(model_name):
    """(media, std, origine): dal preprocessor del modello se disponibile, altrimenti le costanti ImageNet."""
    try:
        from transformers import AutoImageProcessor
        p = AutoImageProcessor.from_pretrained(model_name)
        return tuple(p.image_mean), tuple(p.image_std), "preprocessor"
    except Exception:
        return MEDIA, DEV_STD, "costanti"


def controlla_immagini(images) -> None:
    """Le immagini devono essere uint8 di forma (N, 128, 160, 3): altrimenti la normalizzazione sarebbe sbagliata."""
    assert images.dtype == np.uint8, f"immagini di tipo {images.dtype}, atteso uint8"
    assert images.ndim == 4 and images.shape[1:] == (RIGHE * PATCH, COLONNE * PATCH, 3), (
        f"immagini di forma {images.shape}, attesa (N, {RIGHE * PATCH}, {COLONNE * PATCH}, 3)")


def revisione_modello(model) -> str | None:
    """Revisione (commit) dei pesi effettivamente caricati: dalla config, altrimenti dal percorso dello snapshot."""
    rev = getattr(model.config, "_commit_hash", None)
    if rev:
        return rev
    m = re.search(r"snapshots[/\\]([0-9a-f]{40})", str(getattr(model.config, "_name_or_path", "")))
    return m.group(1) if m else None


def hash_ids(ids) -> str:
    """sha256 della lista degli id, nell'ordine dato (garantisce l'allineamento con images.npz)."""
    return hashlib.sha256(chr(10).join(str(i) for i in ids).encode("utf-8")).hexdigest()


def _passo(model, x, n_attesi, registri):
    with torch.no_grad():
        h = model(pixel_values=x).last_hidden_state
    assert h.shape[1] == 1 + registri + n_attesi, (
        f"sequenza di {h.shape[1]} token, attesi {1 + registri + n_attesi}")
    return h[:, -n_attesi:]  # scarta CLS e registri, tiene le patch in ordine riga per riga


def extract_features(images, model_name=MODELLO, upscale=1, batch=256, model=None,
                     device=None, mean_std=None):
    """Restituisce (N, 80*upscale^2, dim) float16 con i token di patch dell'ultimo strato.

    Le immagini (uint8 RGB 128x160) vanno al modello senza ridimensionare: il token k
    corrisponde alla cella (k // 10, k % 10). Con upscale=2 l'immagine e' ingrandita
    con nearest-neighbor (16x20 patch). Se il batch non entra in memoria, si dimezza.
    """
    controlla_immagini(images)
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
    if model is None:
        from transformers import AutoModel
        model = AutoModel.from_pretrained(model_name)
        if mean_std is None:
            mean_std = _media_std(model_name)[:2]
    media, dev_std = mean_std or (MEDIA, DEV_STD)
    model = model.to(device).eval()
    registri = model.config.num_register_tokens
    assert model.config.patch_size == PATCH
    n_attesi = RIGHE * COLONNE * upscale ** 2
    m = torch.tensor(media, device=device).view(1, 3, 1, 1)
    s = torch.tensor(dev_std, device=device).view(1, 3, 1, 1)
    out, i = [], 0
    while i < len(images):
        try:
            x = torch.from_numpy(np.ascontiguousarray(images[i:i + batch])).to(device)
            x = (x.permute(0, 3, 1, 2).float() / 255 - m) / s
            if upscale > 1:
                x = torch.repeat_interleave(torch.repeat_interleave(x, upscale, 2), upscale, 3)
            out.append(_passo(model, x, n_attesi, registri).half().cpu().numpy())
            i += batch
        except torch.cuda.OutOfMemoryError:
            if batch == 1:
                raise
            torch.cuda.empty_cache()
            batch = max(1, batch // 2)
            print(f"memoria GPU esaurita: batch ridotto a {batch}")
    return np.concatenate(out) if out else np.zeros((0, n_attesi, model.config.hidden_size), np.float16)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", default=MODELLO)
    ap.add_argument("--upscale", type=int, default=1)
    ap.add_argument("--batch", type=int, default=256)
    a = ap.parse_args()
    t0 = time.time()
    dati = np.load(DATA / "images.npz")
    images, ids = dati["images"], [str(i) for i in dati["ids"]]
    assert len(ids) == len(images), f"{len(ids)} id contro {len(images)} immagini"
    controlla_immagini(images)
    from transformers import AutoModel
    model = AutoModel.from_pretrained(a.model)
    media, dev_std, origine = _media_std(a.model)
    feats = extract_features(images, a.model, a.upscale, a.batch, model=model, mean_std=(media, dev_std))
    assert len(feats) == len(ids)
    np.save(DATA / "features_dinov3_s16.npy", feats)
    meta = {"model": a.model, "revision": revisione_modello(model), "upscale": a.upscale,
            "dtype": str(feats.dtype), "shape": list(feats.shape),
            "ids_order": "data/dataset/images.npz (chiave ids)", "n_ids": len(ids), "ids_sha256": hash_ids(ids),
            "image_dtype": str(images.dtype), "image_shape": list(images.shape),
            "mean": list(media), "std": list(dev_std), "mean_std_origine": origine,
            "seconds": round(time.time() - t0, 1)}
    (DATA / "features_dinov3_s16.json").write_text(json.dumps(meta, indent=2))
    print(meta)


if __name__ == "__main__":
    main()
