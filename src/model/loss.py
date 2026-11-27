import torch
import torch.nn.functional as F


def loss_m1(percezione, modifica, nuovo, prima, soluzioni, valide, pos_weight):
    percezione, modifica, nuovo = percezione.float(), modifica.float(), nuovo.float()
    B, K, C = soluzioni.shape
    l_perc = F.cross_entropy(percezione.reshape(B * C, -1), prima.reshape(-1), reduction="none").reshape(B, C).mean(1)
    cambia = (soluzioni >= 0).float()
    peso = torch.tensor(pos_weight, dtype=torch.float32, device=modifica.device)
    l_mod = F.binary_cross_entropy_with_logits(modifica[:, None, :].expand(B, K, C), cambia, pos_weight=peso, reduction="none").mean(2)
    logp = F.log_softmax(nuovo, -1)[:, None].expand(B, K, C, nuovo.shape[-1])
    lp = logp.gather(3, soluzioni.long().clamp(min=0).unsqueeze(3)).squeeze(3)
    l_nuovo = -(lp * cambia).sum(2) / cambia.sum(2).clamp(min=1)
    totale = (l_mod + l_nuovo).masked_fill(~valide, float("inf"))
    k = totale.argmin(1)
    scelto = totale.gather(1, k[:, None]).squeeze(1)
    loss = (l_perc + scelto).mean()
    parti = {
        "perc": l_perc.mean().detach(),
        "mod": l_mod.gather(1, k[:, None]).mean().detach(),
        "nuovo": l_nuovo.gather(1, k[:, None]).mean().detach(),
        "k": k,
    }
    return loss, parti
