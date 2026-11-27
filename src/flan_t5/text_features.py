import argparse
import json
import time
from pathlib import Path

import numpy as np
import torch
from transformers import AutoTokenizer, T5EncoderModel

DATI = Path(__file__).resolve().parents[2] / "data" / "dataset"
USCITA = DATI / "flan_t5"
NOME = "testi_flan_t5_base"
MODELLO = "google/flan-t5-base"
REVISIONE = "7bcac572ce56db69c1ea7c8af255c5d7c9672fc2"
FILE = ["train", "val", "test_main", "test_compositional", "test_length", "test_ambiguous", "test_human"]


def frasi_del_dataset(dati=DATI):
    frasi = set()
    for nome in FILE:
        p = Path(dati) / f"dataset_{nome}.jsonl"
        if p.exists():
            with open(p, encoding="utf-8") as f:
                frasi.update(json.loads(riga)["text"] for riga in f)
    return sorted(frasi)


class Codificatore:
    def __init__(self, modello=MODELLO, revisione=REVISIONE, device=None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.tok = AutoTokenizer.from_pretrained(modello, revision=revisione)
        self.rete = T5EncoderModel.from_pretrained(modello, revision=revisione, dtype=torch.float32)
        self.rete.to(self.device).eval()
        self.revisione = self.rete.config._commit_hash or revisione

    @torch.no_grad()
    def __call__(self, frasi, batch=256):
        out = []
        for k in range(0, len(frasi), batch):
            t = self.tok(frasi[k:k + batch], padding=True, return_tensors="pt").to(self.device)
            h = self.rete(input_ids=t.input_ids, attention_mask=t.attention_mask).last_hidden_state
            for v, m in zip(h, t.attention_mask):
                out.append(v[m.bool()].float().cpu().numpy())
        return out


def carica(cartella=USCITA):
    meta = json.loads((Path(cartella) / f"{NOME}.json").read_text(encoding="utf-8"))
    v = np.load(Path(cartella) / f"{NOME}.npy", mmap_mode="r")
    o = meta["offset"]
    return {t: v[o[i]:o[i + 1]] for i, t in enumerate(meta["testi"])}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dati", default=str(DATI))
    ap.add_argument("--uscita", default=str(USCITA))
    ap.add_argument("--batch", type=int, default=256)
    a = ap.parse_args()
    uscita = Path(a.uscita)
    uscita.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    frasi = frasi_del_dataset(a.dati)
    cod = Codificatore()
    vettori = cod(frasi, a.batch)
    lunghezze = [len(v) for v in vettori]
    offset = np.concatenate([[0], np.cumsum(lunghezze)]).tolist()
    tutti = np.concatenate(vettori).astype(np.float16)
    assert np.isfinite(tutti).all()
    np.save(uscita / f"{NOME}.npy", tutti)
    meta = {"model": MODELLO, "revision": cod.revisione, "dtype": "float16", "dim": int(tutti.shape[1]),
            "n_testi": len(frasi), "n_token": int(tutti.shape[0]), "max_token": max(lunghezze),
            "secondi": round(time.time() - t0, 1), "testi": frasi, "offset": offset}
    (uscita / f"{NOME}.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    print(f"{len(frasi)} frasi, {tutti.shape[0]} token, max {max(lunghezze)} token, {tutti.nbytes / 1e6:.0f} MB, {meta['secondi']} s")


if __name__ == "__main__":
    main()
