import json
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np
import torch

RADICE = Path(__file__).resolve().parents[2]
DATI = RADICE / "data" / "dataset"
TIPI = [t["code"] for t in json.loads((RADICE / "src" / "leveledit" / "types.json").read_text(encoding="utf-8"))]
INDICE = {c: i for i, c in enumerate(TIPI)}


@dataclass
class Risorse:
    celle: torch.Tensor
    testo: torch.Tensor
    offset: torch.Tensor
    pos_stanza: dict
    pos_frase: dict
    bioma: dict
    device: str

    @classmethod
    def carica(cls, device="cpu"):
        ids = [str(i) for i in np.load(DATI / "images.npz")["ids"]]
        celle = torch.from_numpy(np.load(DATI / "features_dinov3_s16.npy")).to(device)
        meta = json.loads((DATI / "flan_t5" / "testi_flan_t5_base.json").read_text(encoding="utf-8"))
        testo = torch.from_numpy(np.load(DATI / "flan_t5" / "testi_flan_t5_base.npy")).to(device)
        bioma = {}
        with open(DATI / "rooms.jsonl", encoding="utf-8") as f:
            for riga in f:
                r = json.loads(riga)
                bioma[r["id"]] = r["biome"]
        return cls(celle, testo, torch.tensor(meta["offset"], dtype=torch.long, device=device),
                   {s: k for k, s in enumerate(ids)}, {t: k for k, t in enumerate(meta["testi"])}, bioma, device)


@dataclass
class Esempi:
    stanza: torch.Tensor
    frase: torch.Tensor
    prima: torch.Tensor
    soluzioni: torch.Tensor
    valide: torch.Tensor
    record: list
    bioma: list
    origine: list


def carica_split(nome, ris, limite=None):
    record = []
    with open(DATI / f"dataset_{nome}.jsonl", encoding="utf-8") as f:
        for riga in f:
            if limite is not None and len(record) >= limite:
                break
            record.append(json.loads(riga))
    n = len(record)
    prima = np.array([[INDICE[c] for c in r["before"]] for r in record], dtype=np.int64).reshape(n, 80)
    soluzioni = np.full((n, 80, 80), -1, dtype=np.int8)
    valide = np.zeros((n, 80), dtype=bool)
    for i, r in enumerate(record):
        for k, s in enumerate(r["solutions"]):
            valide[i, k] = True
            for y, x, c in s["changes"]:
                soluzioni[i, k, y * 10 + x] = INDICE[c]
    d = ris.device
    return Esempi(
        torch.tensor([ris.pos_stanza[r["base_id"]] for r in record], dtype=torch.long, device=d),
        torch.tensor([ris.pos_frase[r["text"]] for r in record], dtype=torch.long, device=d),
        torch.from_numpy(prima).to(d),
        torch.from_numpy(soluzioni).to(d),
        torch.from_numpy(valide).to(d),
        record,
        [ris.bioma[r["base_id"]] for r in record],
        [r["base_id"].split(":")[0] for r in record],
    )


def solo_segnata(es):
    valide = es.valide.clone()
    valide[:, 1:] = False
    return replace(es, valide=valide)


def prepara_batch(ris, es, idx):
    idx = idx.to(es.stanza.device)
    frasi = es.frase[idx]
    inizio = ris.offset[frasi]
    lunghezza = ris.offset[frasi + 1] - inizio
    passi = torch.arange(int(lunghezza.max()), device=inizio.device)
    pad = passi[None, :] >= lunghezza[:, None]
    pos = torch.where(pad, torch.zeros_like(inizio)[:, None], inizio[:, None] + passi[None, :])
    testo = ris.testo[pos].float()
    testo[pad] = 0
    return {
        "celle": ris.celle[es.stanza[idx]].float(),
        "testo": testo,
        "pad": pad,
        "prima": es.prima[idx],
        "soluzioni": es.soluzioni[idx],
        "valide": es.valide[idx],
    }
