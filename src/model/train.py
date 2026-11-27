import argparse
import csv
import json
import math
import os
import random
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import torch
import yaml
from torch import nn
from tqdm import tqdm

from model.data import RADICE, Risorse, carica_split, prepara_batch, solo_segnata
from model.evaluate import griglia, misure, misure_per_gruppo, predici, scegli_tau
from model.loss import loss_m1
from model.model import M1

NOMI = {"successo": "success", "perc_celle": "perception_cells", "perc_stanze": "perception_rooms",
        "non_richieste_media": "unrequested_per_example", "zero_non_richieste": "zero_unrequested",
        "cambi_in_soluzione": "changes_in_solution", "tipo_giusto": "right_type"}
BIOMI = {"aperto": "open", "caverne": "caves", "case": "houses", "dungeon": "dungeon"}
TEST = ("test_main", "test_compositional", "test_length", "test_ambiguous")
RIGA = "=" * 78


def carica_config(path):
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def fattore_lr(passo, warmup, totale):
    if passo < warmup:
        return passo / warmup
    return 0.5 * (1 + math.cos(math.pi * min(passo - warmup, totale - warmup) / max(totale - warmup, 1)))


def ottimizzatore(modello, lr, weight_decay):
    embedding = {id(p) for m in modello.modules() if isinstance(m, nn.Embedding) for p in m.parameters()}
    con, senza = [], []
    for p in modello.parameters():
        (senza if p.ndim < 2 or id(p) in embedding else con).append(p)
    return torch.optim.AdamW([{"params": con, "weight_decay": weight_decay}, {"params": senza, "weight_decay": 0.0}], lr=lr)


def semi(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def inglese(m):
    return {NOMI[k]: v for k, v in m.items()}


def gruppi_inglese(val, pred, perc):
    return {"biome": {BIOMI.get(k, k): inglese(v) for k, v in misure_per_gruppo(val, pred, perc, "bioma").items()},
            "origin": {k: inglese(v) for k, v in misure_per_gruppo(val, pred, perc, "origine").items()}}


def scrivi(testo=""):
    tqdm.write(testo, file=sys.stdout)
    sys.stdout.flush()


def prepara(conf, device, limite_train):
    semi(conf["seed"])
    ris = Risorse.carica(device)
    train = carica_split("train", ris, limite_train)
    if conf.get("target", "vicina") == "segnata":
        train = solo_segnata(train)
    modello = M1(**conf["modello"]).to(device)
    a = conf["addestramento"]
    return ris, train, modello, ottimizzatore(modello, a["lr"], a["weight_decay"])


def passo(modello, opt, b, a, bf16):
    with torch.autocast(device_type="cuda", dtype=torch.bfloat16, enabled=bf16):
        uscite = modello(b["celle"], b["testo"], b["pad"])
    loss, parti = loss_m1(*uscite, b["prima"], b["soluzioni"], b["valide"], a["pos_weight"])
    opt.zero_grad(set_to_none=True)
    loss.backward()
    nn.utils.clip_grad_norm_(modello.parameters(), a["clip"])
    opt.step()
    return loss.item(), {k: float(parti[k]) for k in ("perc", "mod", "nuovo")}


def intestazione(conf, device, modello, n_train, n_val, cartella):
    a = conf["addestramento"]
    gpu = f" ({torch.cuda.get_device_name(0)})" if device.startswith("cuda") else ""
    target = "closest correct solution" if conf.get("target", "vicina") == "vicina" else "marked solution only"
    scrivi(RIGA)
    scrivi(f"LevelEdit · M1 training   run: {cartella.name}   device: {device}{gpu}")
    scrivi(f"parameters: {sum(p.numel() for p in modello.parameters()):,}   train: {n_train:,} examples   val: {n_val:,} examples")
    scrivi(f"batch {a['batch']}   max epochs {a['epoche']}   lr {a['lr']} (warmup {a['warmup']}, cosine)   "
           f"pos_weight {a['pos_weight']}   patience {a['pazienza']}")
    scrivi(f"target: {target}   output: {cartella}")
    scrivi(RIGA)


def riga_epoca(epoca, totale, perdita, lr, tau, mis, minuti, migliore):
    return (f"Epoch {epoca:>2}/{totale} | loss {perdita:.3f} | lr {lr:.1e} | val success {mis['successo'] * 100:5.1f}% "
            f"(tau {tau}) | perception {mis['perc_celle'] * 100:5.2f}% cells, {mis['perc_stanze'] * 100:4.1f}% rooms | "
            f"unrequested {mis['non_richieste_media']:.2f}/ex | {minuti:.2f} min" + ("  * best" if migliore else ""))


def apri_file(file):
    try:
        if hasattr(os, "startfile"):
            os.startfile(file)
        else:
            subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", str(file)])
    except OSError:
        pass


def esempi_finali(modello, tau, ris, val, cartella, n, seed, apri):
    if n <= 0:
        return []
    from model.demo import mostra_esempio
    from model.render import Libreria
    lib = Libreria.carica()
    scelti = sorted(random.Random(seed).sample(range(len(val.record)), min(n, len(val.record))))
    out = []
    scrivi(f"Random validation examples ({len(scelti)}):")
    for j, i in enumerate(scelti, 1):
        e = mostra_esempio(modello, tau, ris, val, i, lib, cartella / "examples" / f"val_{i:04d}.png")
        esito = "CORRECT" if e["giusto"] else "WRONG"
        scrivi(f"  [{j}/{len(scelti)}] \"{e['frase']}\" -> {esito} "
               f"({len(e['cambiate'])} cells changed, {len(e['viste_male'])} misperceived)")
        scrivi(f"        image: {e['file']}")
        out.append({"index": i, "text": e["frase"], "correct": bool(e["giusto"]), "image": str(e["file"])})
        if apri:
            apri_file(e["file"])
    return out


def valuta_test(modello, tau, ris, cartella, limite_test):
    scrivi("Test sets (use these numbers only for final results):")
    risultati = {}
    for nome in TEST:
        es = carica_split(nome, ris, limite_test)
        uscite = predici(modello, ris, es)
        m = inglese(misure(es, griglia(*uscite, tau), uscite[0].argmax(-1)))
        risultati[nome] = {"examples": len(es.record), **m}
        scrivi(f"  {nome:<20} {len(es.record):>5} examples | success {m['success'] * 100:5.1f}% | "
               f"perception {m['perception_cells'] * 100:5.2f}% cells | unrequested {m['unrequested_per_example']:.2f}/ex")
    (cartella / "test_metrics.json").write_text(json.dumps(risultati, indent=2), encoding="utf-8")
    return risultati


def addestra(conf, device, limite_train=None, limite_val=None, esempi=2, apri=False, test=False, limite_test=None):
    inizio = time.time()
    a = conf["addestramento"]
    ris, train, modello, opt = prepara(conf, device, limite_train)
    val = carica_split("val", ris, limite_val)
    n = len(train.record)
    passi_epoca = math.ceil(n / a["batch"])
    totale = a["epoche"] * passi_epoca
    sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: fattore_lr(s, a["warmup"], totale))
    uscita = Path(conf["uscita"])
    cartella = (uscita if uscita.is_absolute() else RADICE / uscita) / f"{conf['nome']}_seed{conf['seed']}"
    cartella.mkdir(parents=True, exist_ok=True)
    (cartella / "config.yaml").write_text(yaml.safe_dump(conf, allow_unicode=True, sort_keys=False), encoding="utf-8")
    (cartella / "groups.jsonl").write_text("", encoding="utf-8")
    intestazione(conf, device, modello, n, len(val.record), cartella)
    bf16 = bool(a["bf16"]) and device.startswith("cuda")
    migliore, attesa, tempi, riepilogo = -1.0, 0, [], {}
    with open(cartella / "metrics.csv", "w", newline="", encoding="utf-8") as f:
        scrittore = None
        for epoca in range(1, a["epoche"] + 1):
            t0 = time.time()
            modello.train()
            ordine = torch.randperm(n, generator=torch.Generator().manual_seed(conf["seed"] * 1000 + epoca))
            perdite, parti = [], {"perc": [], "mod": [], "nuovo": []}
            barra = tqdm(range(0, n, a["batch"]), desc=f"Epoch {epoca}/{a['epoche']}", unit="batch", leave=False,
                         dynamic_ncols=True, disable=not sys.stderr.isatty())
            for i in barra:
                l, p = passo(modello, opt, prepara_batch(ris, train, ordine[i:i + a["batch"]]), a, bf16)
                sched.step()
                perdite.append(l)
                for k in parti:
                    parti[k].append(p[k])
                if len(perdite) % 20 == 0:
                    barra.set_postfix(loss=f"{np.mean(perdite[-20:]):.3f}", lr=f"{sched.get_last_lr()[0]:.1e}")
            uscite = predici(modello, ris, val)
            tau, mis = scegli_tau(val, uscite, conf["soglie"])
            pred, perc = griglia(*uscite, tau), uscite[0].argmax(-1)
            gruppi = gruppi_inglese(val, pred, perc)
            tempi.append((time.time() - t0) / 60)
            lr = sched.get_last_lr()[0]
            riga = {"epoch": epoca, "train_loss": float(np.mean(perdite)),
                    "train_loss_perception": float(np.mean(parti["perc"])), "train_loss_change": float(np.mean(parti["mod"])),
                    "train_loss_new_type": float(np.mean(parti["nuovo"])), "lr": lr, "tau": tau, **inglese(mis),
                    "minutes": tempi[-1]}
            if scrittore is None:
                scrittore = csv.DictWriter(f, fieldnames=list(riga))
                scrittore.writeheader()
            scrittore.writerow(riga)
            f.flush()
            with open(cartella / "groups.jsonl", "a", encoding="utf-8") as g:
                g.write(json.dumps({"epoch": epoca, "tau": tau, **gruppi}, ensure_ascii=False) + "\n")
            nuovo_migliore = mis["successo"] > migliore
            scrivi(riga_epoca(epoca, a["epoche"], riga["train_loss"], lr, tau, mis, tempi[-1], nuovo_migliore))
            if nuovo_migliore:
                migliore, attesa = mis["successo"], 0
                torch.save({"state": modello.state_dict(), "tau": tau, "epoch": epoca, "conf": conf}, cartella / "best.pt")
                riepilogo = {"best_epoch": epoca, "tau": tau, "val": inglese(mis), "groups": gruppi}
            else:
                attesa += 1
                if attesa >= a["pazienza"]:
                    scrivi(f"Early stopping: {a['pazienza']} epochs without improvement.")
                    break
    ck = torch.load(cartella / "best.pt", map_location=device, weights_only=False)
    modello.load_state_dict(ck["state"])
    modello.eval()
    v = riepilogo["val"]
    scrivi(RIGA)
    scrivi(f"Best epoch {riepilogo['best_epoch']}   tau {riepilogo['tau']}   val success {v['success'] * 100:.1f}%   "
           f"perception {v['perception_cells'] * 100:.2f}% cells   unrequested {v['unrequested_per_example']:.2f}/ex")
    for chiave in ("biome", "origin"):
        scrivi(f"  by {chiave:<6}: " + " | ".join(f"{k} {m['success'] * 100:.1f}%" for k, m in riepilogo["groups"][chiave].items()))
    riepilogo.update(parameters=sum(p.numel() for p in modello.parameters()), epochs_done=len(tempi),
                     minutes_per_epoch=sum(tempi) / len(tempi))
    scrivi(RIGA)
    riepilogo["examples"] = esempi_finali(modello, ck["tau"], ris, val, cartella, esempi, conf["seed"], apri)
    if test:
        riepilogo["test"] = valuta_test(modello, ck["tau"], ris, cartella, limite_test)
    riepilogo["total_minutes"] = (time.time() - inizio) / 60
    (cartella / "summary.json").write_text(json.dumps(riepilogo, indent=2, ensure_ascii=False), encoding="utf-8")
    scrivi(RIGA)
    scrivi(f"Done in {riepilogo['total_minutes']:.1f} min. Files in {cartella}: best.pt, metrics.csv, groups.jsonl, "
           f"summary.json{', test_metrics.json' if test else ''}{', examples/' if esempi > 0 else ''}")
    scrivi(RIGA)
    return cartella


def controllo_batch(conf, device, esempi=128, passi=300):
    a = conf["addestramento"]
    ris, es, modello, opt = prepara(conf, device, esempi)
    b = prepara_batch(ris, es, torch.arange(len(es.record)))
    bf16 = bool(a["bf16"]) and device.startswith("cuda")
    modello.train()
    perdite = [passo(modello, opt, b, a, bf16)[0] for _ in range(passi)]
    uscite = predici(modello, ris, es)
    successo = misure(es, griglia(*uscite, 0.5), uscite[0].argmax(-1))["successo"]
    return {"loss_iniziale": perdite[0], "loss_finale": perdite[-1], "successo_finale": successo}


def main():
    ap = argparse.ArgumentParser(description="Train M1 (LevelEdit).")
    ap.add_argument("--config", required=True)
    ap.add_argument("--nome")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--epoche", type=int)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--examples", type=int, default=2, help="random validation examples drawn at the end")
    ap.add_argument("--no-open", action="store_true", help="do not open the example images")
    ap.add_argument("--test", action="store_true", help="also evaluate on the test sets (final results only)")
    ap.add_argument("--controllo-batch", action="store_true")
    x = ap.parse_args()
    conf = carica_config(x.config)
    if x.nome:
        conf["nome"] = x.nome
    if x.seed is not None:
        conf["seed"] = x.seed
    if x.epoche:
        conf["addestramento"]["epoche"] = x.epoche
    if x.controllo_batch:
        print(json.dumps(controllo_batch(conf, x.device), indent=2))
    else:
        addestra(conf, x.device, esempi=x.examples, apri=not x.no_open, test=x.test)


if __name__ == "__main__":
    main()
