def griglia(pred):
    pred = list(pred)
    if len(pred) == 80 and all(isinstance(c, str) for c in pred):
        return [pred[i * 10:(i + 1) * 10] for i in range(8)]
    if len(pred) == 8 and all(len(r) == 10 for r in pred):
        return [list(r) for r in pred]
    raise ValueError("la predizione deve essere 8x10 codici o una lista piatta di 80")


def piatta(pred):
    return [c for riga in griglia(pred) for c in riga]


def soluzioni(record):
    out = []
    for s in record["solutions"]:
        g = list(record["before"])
        for y, x, c in s["changes"]:
            g[y * 10 + x] = c
        out.append(g)
    return out


def is_correct(record, prediction, verifica=None):
    p = piatta(prediction)
    if p in soluzioni(record):
        return True
    if record.get("solutions_truncated", False) and verifica is not None:
        return bool(verifica(record, griglia(p)))
    return False
