import csv
import json

import torch

from model.model import M1
from model.train import addestra, carica_config, controllo_batch, fattore_lr, ottimizzatore


def test_fattore_lr():
    assert fattore_lr(0, 1000, 18000) == 0.0 and fattore_lr(1000, 1000, 18000) == 1.0
    assert abs(fattore_lr(9500, 1000, 18000) - 0.5) < 1e-9 and fattore_lr(18000, 1000, 18000) < 1e-9


def test_gruppi_senza_weight_decay():
    m = M1()
    opt = ottimizzatore(m, 3e-4, 0.05)
    con, senza = opt.param_groups
    assert con["weight_decay"] == 0.05 and senza["weight_decay"] == 0.0
    ids_senza = {id(p) for p in senza["params"]}
    for mod in m.modules():
        if isinstance(mod, (torch.nn.LayerNorm, torch.nn.Embedding)):
            assert all(id(p) in ids_senza for p in mod.parameters())


def test_soglie_arrivano_al_punto_neutro_del_peso():
    for f in ("configs/model_conf.yaml", "configs/model_conf_segnata.yaml"):
        c = carica_config(f)
        w = c["addestramento"]["pos_weight"]
        assert max(c["soglie"]) >= w / (w + 1)


def conf_piccola(tmp_path):
    c = carica_config("configs/model_conf.yaml")
    c["addestramento"].update(batch=16, epoche=2, warmup=2)
    c["uscita"] = str(tmp_path)
    return c


def test_run_piccolo_scrive_tutto_ed_e_riproducibile(tmp_path):
    a = addestra(conf_piccola(tmp_path / "a"), "cpu", limite_train=64, limite_val=32)
    b = addestra(conf_piccola(tmp_path / "b"), "cpu", limite_train=64, limite_val=32)
    for f in ("config.yaml", "metrics.csv", "best.pt", "summary.json"):
        assert (a / f).exists()
    assert len(list((a / "examples").glob("*.png"))) == 2

    def righe(p):
        with open(p / "metrics.csv", encoding="utf-8") as f:
            return [{k: v for k, v in r.items() if k != "minutes"} for r in csv.DictReader(f)]

    assert len(righe(a)) == 2 and righe(a) == righe(b)
    assert {"epoch", "train_loss", "tau", "success", "perception_cells", "unrequested_per_example"} <= set(righe(a)[0])


def test_misure_per_gruppo_a_ogni_epoca(tmp_path):
    p = addestra(conf_piccola(tmp_path), "cpu", limite_train=64, limite_val=32, esempi=0)
    with open(p / "groups.jsonl", encoding="utf-8") as f:
        righe = [json.loads(r) for r in f]
    assert [r["epoch"] for r in righe] == [1, 2]
    assert set(righe[0]) == {"epoch", "tau", "biome", "origin"} and righe[0]["origin"]


def test_valutazione_sul_test_solo_se_chiesta(tmp_path):
    senza = addestra(conf_piccola(tmp_path / "a"), "cpu", limite_train=32, limite_val=16, esempi=0)
    assert not (senza / "test_metrics.json").exists()
    con = addestra(conf_piccola(tmp_path / "b"), "cpu", limite_train=32, limite_val=16, esempi=0, test=True, limite_test=8)
    r = json.loads((con / "test_metrics.json").read_text(encoding="utf-8"))
    assert set(r) == {"test_main", "test_compositional", "test_length", "test_ambiguous"}
    assert all(0 <= v["success"] <= 1 and v["examples"] == 8 for v in r.values())


def test_controllo_batch_impara(tmp_path):
    r = controllo_batch(conf_piccola(tmp_path), "cpu", esempi=8, passi=60)
    assert 6 < r["loss_iniziale"] < 10 and r["loss_finale"] < r["loss_iniziale"] / 2
