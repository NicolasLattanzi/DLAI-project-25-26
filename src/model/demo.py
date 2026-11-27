import argparse
import json
from pathlib import Path

import torch
from PIL import Image, ImageDraw, ImageFont

from leveledit.evaluate import is_correct
from model.data import DATI, RADICE, TIPI, Risorse, carica_split
from model.evaluate import griglia
from model.model import M1
from model.render import Libreria, ridisegna

SCALA = 3
ALTEZZA_TITOLO = 28
ROSSO, GIALLO, VERDE = (255, 40, 40), (255, 220, 0), (40, 200, 80)


def carica_modello(run, device):
    file = Path(run) / "best.pt"
    ck = torch.load(file if file.exists() else Path(run) / "migliore.pt", map_location=device, weights_only=False)
    modello = M1(**ck["conf"]["modello"]).to(device)
    modello.load_state_dict(ck.get("state", ck.get("stato")))
    return modello.eval(), ck["tau"]


@torch.no_grad()
def esegui(modello, tau, celle, testo):
    modello.eval()
    pad = torch.zeros(1, testo.shape[0], dtype=torch.bool, device=celle.device)
    p, m, n = modello(celle[None].float(), testo[None].float(), pad)
    return griglia(p, m, n, tau)[0].cpu(), p.argmax(-1)[0].cpu(), torch.sigmoid(m.float())[0].cpu()


def pannello(immagine, riquadri):
    img = Image.fromarray(immagine).resize((160 * SCALA, 128 * SCALA), Image.NEAREST)
    d = ImageDraw.Draw(img)
    lato = 16 * SCALA
    for c, colore in riquadri:
        y, x = c // 10 * lato, c % 10 * lato
        d.rectangle([x, y, x + lato - 1, y + lato - 1], outline=colore, width=2)
    return img


def disegna(pannelli, file):
    font = ImageFont.load_default()
    largo, alto = 160 * SCALA, 128 * SCALA
    tela = Image.new("RGB", (len(pannelli) * largo + (len(pannelli) - 1) * 12, alto + ALTEZZA_TITOLO), (255, 255, 255))
    d = ImageDraw.Draw(tela)
    for i, (titolo, immagine, riquadri) in enumerate(pannelli):
        x = i * (largo + 12)
        d.text((x + 4, 8), titolo, fill=(0, 0, 0), font=font)
        tela.paste(pannello(immagine, riquadri), (x, ALTEZZA_TITOLO))
    tela.save(file)


def testo_griglia(g, segna=()):
    return "\n".join(" ".join(f"[{g[y * 10 + x]}]" if y * 10 + x in segna else f" {g[y * 10 + x]} " for x in range(10))
                     for y in range(8))


def gruppo_di(base_id):
    with open(DATI / "rooms.jsonl", encoding="utf-8") as f:
        for riga in f:
            r = json.loads(riga)
            if r["id"] == base_id:
                return r["gfx_group"]


def mostra_esempio(modello, tau, ris, es, i, lib, file, frase=None):
    r = es.record[i]
    celle = ris.celle[es.stanza[i]]
    if frase:
        from flan_t5.text_features import Codificatore
        testo = torch.tensor(Codificatore(device=ris.device)([frase])[0], device=ris.device)
    else:
        f = int(es.frase[i])
        testo = ris.testo[ris.offset[f]:ris.offset[f + 1]]
    dopo, visto, prob = esegui(modello, tau, celle, testo)
    vero = list(r["before"])
    visto_c = [TIPI[int(k)] for k in visto]
    dopo_c = [TIPI[int(k)] for k in dopo]
    cambiate = [c for c in range(80) if dopo_c[c] != visto_c[c]]
    viste_male = [c for c in range(80) if visto_c[c] != vero[c] and c not in cambiate]
    giusto = None if frase else is_correct(r, dopo_c)
    immagine = lib.immagini[int(es.stanza[i])]
    gruppo = gruppo_di(r["base_id"])
    modifica = [dopo_c[c] if c in cambiate else vero[c] for c in range(80)]
    titolo = "after: model" + ("" if giusto is None else " (CORRECT)" if giusto else " (WRONG)")
    pannelli = [("before", immagine, []),
                (titolo, ridisegna(immagine, vero, modifica, gruppo, lib),
                 [(c, ROSSO) for c in cambiate] + [(c, GIALLO) for c in viste_male])]
    if not frase:
        sol = [c for c in range(80) if r["after"][c] != vero[c]]
        pannelli.append(("after: a dataset solution", ridisegna(immagine, vero, r["after"], gruppo, lib),
                         [(c, VERDE) for c in sol]))
    Path(file).parent.mkdir(parents=True, exist_ok=True)
    disegna(pannelli, file)
    return {"record": r, "frase": frase or r["text"], "visto": visto_c, "dopo": dopo_c, "vero": vero,
            "cambiate": cambiate, "viste_male": viste_male, "prob": prob, "giusto": giusto, "file": Path(file)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="runs/m1_seed0")
    ap.add_argument("--esempio", type=int, default=0)
    ap.add_argument("--frase")
    ap.add_argument("--uscita")
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    a = ap.parse_args()
    ris = Risorse.carica(a.device)
    es = carica_split("val", ris)
    modello, tau = carica_modello(RADICE / a.run, a.device)
    file = Path(a.uscita) if a.uscita else RADICE / a.run / f"demo_{a.esempio}{'_frase' if a.frase else ''}.png"
    e = mostra_esempio(modello, tau, ris, es, a.esempio, Libreria.carica(), file, a.frase)
    r, visto_c, dopo_c, vero, cambiate = e["record"], e["visto"], e["dopo"], e["vero"], e["cambiate"]
    print(f"stanza {r['base_id']} | esempio {r['id']} | soglia {tau}")
    print(f"frase: {e['frase']}")
    print(f"celle viste male dal modello: {len(e['viste_male'])}", "".join(f" ({c // 10},{c % 10}) {vero[c]} visto come {visto_c[c]}" for c in e["viste_male"]))
    print("celle cambiate:", ", ".join(f"({c // 10},{c % 10}) {visto_c[c]} -> {dopo_c[c]} (p {e['prob'][c]:.2f})" for c in cambiate) or "nessuna")
    print("\nprima (vista dal modello):\n" + testo_griglia(visto_c, cambiate))
    print("\ndopo (modello):\n" + testo_griglia(dopo_c, cambiate))
    if e["giusto"] is not None:
        print("\ngiusto secondo is_correct:", e["giusto"])
        print("una soluzione giusta:", r["solutions"][0]["changes"], f"(soluzioni possibili: {r['n_solutions']})")
    print("\nimmagine:", file)


if __name__ == "__main__":
    main()
