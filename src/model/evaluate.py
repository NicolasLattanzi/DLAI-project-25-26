from dataclasses import replace

import torch

from leveledit.evaluate import is_correct
from model.data import TIPI, prepara_batch


def griglia(percezione, modifica, nuovo, tau):
    return torch.where(torch.sigmoid(modifica.float()) > tau, nuovo.argmax(-1), percezione.argmax(-1))


@torch.no_grad()
def predici(modello, ris, es, batch=512):
    modello.eval()
    n = len(es.record)
    uscite = ([], [], [])
    for a in range(0, n, batch):
        b = prepara_batch(ris, es, torch.arange(a, min(a + batch, n)))
        for lista, x in zip(uscite, modello(b["celle"], b["testo"], b["pad"])):
            lista.append(x.float().cpu())
    return tuple(torch.cat(lista) for lista in uscite)


def misure(es, pred, perc):
    pred, perc = pred.cpu(), perc.cpu()
    prima, soluzioni, valide = es.prima.cpu(), es.soluzioni.cpu().long(), es.valide.cpu()
    n = len(es.record)
    giuste = sum(is_correct(r, [TIPI[i] for i in pred[j].tolist()]) for j, r in enumerate(es.record))
    perc_ok = perc == prima
    cambiata = pred != prima
    in_soluzione = ((soluzioni >= 0) & valide[:, :, None]).any(1)
    tipo_ok = ((soluzioni == pred[:, None, :]) & valide[:, :, None]).any(1)
    non_richieste = (cambiata & ~in_soluzione).sum(1)
    cambi_giusti = cambiata & in_soluzione
    return {
        "successo": giuste / n,
        "perc_celle": perc_ok.sum().item() / perc_ok.numel(),
        "perc_stanze": perc_ok.all(1).sum().item() / n,
        "non_richieste_media": non_richieste.sum().item() / n,
        "zero_non_richieste": (non_richieste == 0).sum().item() / n,
        "cambi_in_soluzione": cambi_giusti.sum().item() / n,
        "tipo_giusto": (tipo_ok & cambi_giusti).sum().item() / max(cambi_giusti.sum().item(), 1),
    }


def parte(es, indici):
    t = torch.tensor(indici, dtype=torch.long, device=es.stanza.device)
    return replace(es, stanza=es.stanza[t], frase=es.frase[t], prima=es.prima[t], soluzioni=es.soluzioni[t],
                   valide=es.valide[t], record=[es.record[i] for i in indici],
                   bioma=[es.bioma[i] for i in indici], origine=[es.origine[i] for i in indici])


def misure_per_gruppo(es, pred, perc, chiave):
    valori = getattr(es, chiave)
    out = {}
    for g in sorted(set(valori)):
        indici = [i for i, v in enumerate(valori) if v == g]
        t = torch.tensor(indici, dtype=torch.long)
        out[g] = misure(parte(es, indici), pred.cpu()[t], perc.cpu()[t])
    return out


def scegli_tau(es, uscite, soglie):
    p, m, n = uscite
    perc = p.argmax(-1)
    migliore = None
    for tau in soglie:
        g = misure(es, griglia(p, m, n, tau), perc)
        if migliore is None or g["successo"] > migliore[1]["successo"]:
            migliore = (tau, g)
    return migliore
