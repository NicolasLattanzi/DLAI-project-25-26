# LevelEdit - Deep Learning & AI project

In questa repository presentiamo un progetto la cui idea base consiste nel capire se un modello sia in grado di cambiare il layout di un ambiente 2D di un videogioco a parte da una istruzione data. 

Abbiamo usato due giochi per costruire il dataset: *The Legend of Zelda* e *The Legend of Zelda: Link's Awakening*. 

Il modello riceve in input un'istruzione in inglese e la rappresentazione visiva della stanza (160×128 RGB) sotto forma di vettori DINOv3 (uno per ciascuna delle 80 patch $16 \times 16$, di dimensione 384): a partire da questi embedding visivi, dovrà riconoscere/ricostruire la codifica in simboli delle caselle e applicare la modifica richiesta sulla griglia (10×8). 

**Composizione del dataset:** 5.485 in totale (`rooms.jsonl` e `images.npz`), composte da 999 stanze effettivamente utilizzabili prese da *Link's Awakening* e *Zelda 1* (suddivise in 686 train, 99 val, 193 test e 21 scartate perché con immagini identiche) più 4.507 stanze generate dalle 999 per il train.


## File e avvio rapido

Nella radice di `data/dataset/` si trovano i file principali del dataset:
* `dataset_train.jsonl`, `dataset_val.jsonl`, `dataset_test_main.jsonl`, `dataset_test_compositional.jsonl`, `dataset_test_length.jsonl`, `dataset_test_ambiguous.jsonl`
* `rooms.jsonl` e `images.npz`
* `features_dinov3_s16.json` (e `features_dinov3_s16.npy` da generare/verificare in locale secondo `LEGGIMI_DINOv3.txt`)
* `split.json`, `tiles_trainval/` e `LEGGIMI.txt`



## Fonti e licenze

| Fonte                                                                                            | Versione                                                                                         |
| ------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------ |
| ROM *Link's Awakening DX* (U) v1.0 (GBC)                                                         | SHA-1 `d90ac17e9bf17b6c61624ad9f05447bdb5efc01a` (verificato a ogni avvio da `extract_rooms.py`) |
| [LADXR](https://github.com/daid/LADXR)                                                           | commit `4325207e`                                                                                |
| [LADX-Zelda1](https://github.com/daid/LADX-Zelda1) (daid)                                        | commit `4854999`                                                                                 |
| [LADX-Hackers-Toolbox](https://github.com/daid/LADX-Hackers-Toolbox) (daid)                      | commit `78b5d64`                                                                                 |
| [LADX-Disassembly](https://github.com/zladx/LADX-Disassembly) (ZLADX)                            | commit `2a5c2c0d`                                                                                |
| Qwen/Qwen2.5-7B-Instruct                                                                         | licenza Apache-2.0                                                                               |
| `facebook/dinov3-vits16-pretrain-lvd1689m`, revisione `114c1379950215c8b35dfcd4e90a5c251dde0d32` | licenza Meta DINOv3, repo *gated* (accesso manuale)                                              |