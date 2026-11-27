import torch
from torch import nn


class Blocco(nn.Module):
    def __init__(self, d, teste, mlp, dropout):
        super().__init__()
        self.ln1 = nn.LayerNorm(d)
        self.self_att = nn.MultiheadAttention(d, teste, dropout=dropout, batch_first=True)
        self.ln2 = nn.LayerNorm(d)
        self.cross_att = nn.MultiheadAttention(d, teste, dropout=dropout, batch_first=True)
        self.ln3 = nn.LayerNorm(d)
        self.mlp = nn.Sequential(nn.Linear(d, mlp), nn.GELU(), nn.Dropout(dropout), nn.Linear(mlp, d))

    def forward(self, x, t, pad):
        a = self.ln1(x)
        x = x + self.self_att(a, a, a, need_weights=False)[0]
        a = self.ln2(x)
        x = x + self.cross_att(a, t, t, key_padding_mask=pad, need_weights=False)[0]
        return x + self.mlp(self.ln3(x))


class M1(nn.Module):
    def __init__(self, d=384, blocchi=6, teste=6, mlp=1536, dropout=0.1, tipi=29, d_celle=384, d_testo=768, bozza=False):
        super().__init__()
        self.celle_ln = nn.LayerNorm(d_celle)
        self.celle_proj = nn.Linear(d_celle, d)
        self.riga = nn.Embedding(8, d)
        self.colonna = nn.Embedding(10, d)
        self.testo_proj = nn.Linear(d_testo, d)
        self.bozza = nn.Embedding(tipi + 1, d) if bozza else None
        self.blocchi = nn.ModuleList(Blocco(d, teste, mlp, dropout) for _ in range(blocchi))
        self.ln_fin = nn.LayerNorm(d)
        self.percezione = nn.Linear(d, tipi)
        self.modifica = nn.Linear(d, 1)
        self.nuovo = nn.Linear(d, tipi)

    def forward(self, celle, testo, pad, bozza=None):
        k = torch.arange(celle.shape[1], device=celle.device)
        x = self.celle_proj(self.celle_ln(celle)) + self.riga(k // 10) + self.colonna(k % 10)
        if bozza is not None:
            x = x + self.bozza(bozza)
        t = self.testo_proj(testo)
        for b in self.blocchi:
            x = b(x, t, pad)
        x = self.ln_fin(x)
        return self.percezione(x), self.modifica(x).squeeze(-1), self.nuovo(x)
