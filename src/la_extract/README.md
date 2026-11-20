# la_extract: stanze di Link's Awakening DX → griglie LevelEdit

Estrae **tutte** le stanze di *The Legend of Zelda: Link's Awakening DX* (USA, v1.0) direttamente dalla ROM
(senza emulatore) e le converte in griglie 8×10 con le 11 categorie di LevelEdit.

> **Vincoli.** La ROM, le stanze estratte e la grafica del gioco restano **solo in locale**
> (`src/rom/`, `data/la_local/`, `third_party/` sono in `.gitignore`). Nel repository vanno solo
> gli script e i file di `mappings/` (annotazioni nostre, nessun dato grafico o di livello).

## Requisiti

- ROM `Legend of Zelda, The - Link's Awakening DX (U) (V1.0)` in `src/rom/`
  (SHA-1 `d90ac17e9bf17b6c61624ad9f05447bdb5efc01a`, verificato a ogni avvio).
- Python ≥ 3.10 con `Pillow` e `numpy`.
- [LADXR](https://github.com/daid/LADXR) clonato in `third_party/LADXR` (testato al commit `4325207e`).
- (Solo per `census.py` e per rigenerare i nomi) [LADX-Disassembly](https://github.com/zladx/LADX-Disassembly)
  in `third_party/LADX-Disassembly` (commit `2a5c2c0d`).

```powershell
git clone https://github.com/daid/LADXR.git third_party/LADXR
git -C third_party/LADXR checkout 4325207e4e55076e05f209fbdf16b860a90e42ef
git clone https://github.com/zladx/LADX-Disassembly.git third_party/LADX-Disassembly
```

## Pipeline

```powershell
python src/la_extract/extract_rooms.py --clean   # tutte le stanze -> data/la_local/rooms (circa 15 s)
python src/la_extract/make_legend.py             # LEGEND.md + data/la_local/legend/legend.html
python src/la_extract/review_sheets.py           # (controllo) stanze originali + codifica -> data/la_local/review
python src/la_extract/census.py                  # (revisione) censimento + fogli atlas in data/la_local/census
```

| File | Ruolo |
|---|---|
| `ladx.py` | accesso alla ROM tramite LADXR: oggetti 16×16 di ogni stanza, entità, warp, physics flag, posizioni, rendering |
| `mappings/categories.json` | le 11 categorie (simbolo, colore, attraversabilità), regole di validità, politica dei tile speciali, fallback |
| `mappings/objects_overworld.json` | object id overworld → categoria (228 voci, rivisti visivamente uno per uno) |
| `mappings/objects_indoor.json` | object id interni → categoria (151 voci) + differenze della Color Dungeon |
| `mappings/entities.json` | entity id → classe (nemico, boss, NPC, oggetto, meccanismo…) e categoria |
| `mappings/maps.json` | map id → nome e cartella di output |
| `validate.py` | regole 1–4, aggiunta giocatore/scale, chiusura bordi (modulo puro, senza ROM) |
| `extract_rooms.py` | estrazione completa: cartelle, JSON, immagini, `dataset.npz`, report |
| `make_legend.py` | legenda (immagine, simbolo, nome) di categorie, oggetti ed entità |
| `census.py` | censimento degli oggetti usati e fogli di revisione visiva |
| `review_sheets.py` | fogli di controllo: grafica originale con sovrapposta la codifica di ogni stanza |
| `LEGEND.md` | legenda testuale generata (senza immagini) |

## Output (`data/la_local/rooms/`)

```
rooms/
  index.json            elenco di tutte le stanze (percorso, validità, motivi, correzioni)
  dataset.npz           tutte le griglie in un unico file (vedi sotto)
  report.json / .md     conteggi, motivi di scarto, correzioni, per gruppo
  overworld/            256 schermate
    group.json, overview_original.png, overview_mapped.png
    room_0A5/ room.json, original.png, mapped.png
  dungeons/
    D1_tail_cave/ ... D8_turtle_rock/, D9_windfishs_egg/, D0_color_dungeon/
  indoor/
    house/, cave_b/, cave_c/, cave_water/, shop/, kanalet/, ...
```

- `original.png`: stanza con la grafica del gioco, 160×128 (16 px per cella).
- `mapped.png`: griglia **finale** con colori e simboli delle categorie, stessa geometria.
- `overview_*.png`: mosaico del gruppo (dungeon nella disposizione della minimappa); le stanze scartate hanno il bordo rosso.

### `room.json` (schema `leveledit_la_room/1`)

| Campo | Contenuto |
|---|---|
| `room_id`, `region`, `group`, `map_id` | identità della stanza (`region` ∈ overworld / indoor / color) |
| `position.table` | posizione (x, y) nella mappa 16×16 (overworld o tabella interni A/B) |
| `position.layout` | posizione (x, y) nella minimappa 8×8 del dungeon, se c'è |
| `valid`, `discard_reasons`, `notes`, `fixes` | stanza fedele e utilizzabile, motivi di scarto, note, aggiunte (solo `add_player`) |
| `brief_checks`, `brief_valid` | regole del brief verificate senza modificare la griglia (scale presenti/raggiungibili, bordi chiusi, max 2 porte) |
| `grid` / `grid_ascii` | **griglia finale** 8×10 (codici 0–10): layout originale 1:1 + nemici `M` + giocatore `P` (unica aggiunta, nel punto d'ingresso) |
| `grid_no_entities` / `grid_no_entities_ascii` | la stessa griglia **senza giocatore e nemici** (al loro posto il tile del layout) |
| `openings`, `doors` | varchi sul bordo (`door` = porta/apertura del gioco, `corridor` = passaggio libero) e numero di porte chiuse |
| `grid_raw` | conversione diretta (tile + entità), prima di aggiungere il giocatore |
| `grid_tiles` | solo i tile, senza entità |
| `objects`, `physics` | object id originali e physics flag del gioco (esadecimale) |
| `passage` | celle che nel gioco sono varchi verso altre stanze (porte, aperture) |
| `specials`, `unmapped` | celle/entità speciali (interruttori, nastri, teletrasporti…) |
| `entities` | entità con classe e categoria assegnata (o perché non è stata messa in griglia) |
| `key_sources`, `chest` | fonti di chiavi (forzieri con chiave piccola o del boss, chiavi che cadono) |
| `warps`, `arrivals` | uscite della stanza e punti in cui Link compare entrandovi |
| `stats` | conteggi per categoria, numero di nemici, tag |

### `dataset.npz`

`grid`, `grid_no_entities`, `grid_raw`, `grid_tiles` (N×8×10 int8), `objects` (N×8×10 uint8), `room_id`, `region`, `group`,
`map_id`, `table_x/y`, `layout`, `layout_x/y`, `valid`, `brief_valid` (bool), `notes`. Contiene **tutte** le stanze:
per l'addestramento/test filtrare con `valid` (o `brief_valid` per le sole stanze che rispettano anche le regole del brief).

## Regole di conversione (sintesi)

- La griglia viene dagli **oggetti 16×16** della stanza (non dai tile 8×8): un oggetto = una cella.
- La categoria di ogni oggetto è scelta a mano (revisione visiva degli atlanti + physics flag del gioco).
  Scelte non ovvie, tutte modificabili nei JSON:
  - i **gradini interni** (`97`, `98`, overworld `E0`) sono pavimento; `E` è riservato alle **uscite vere**
    (scale verso altri piani, scale nel muro, porte di caverne/case);
  - le **rocce sollevabili** dell'overworld sono muro (come da brief); i **cespugli** sono blocco;
  - **porte aperte, porte a saracinesca, porte a senso unico, muri girevoli e corridoi** sul bordo sono pavimento:
    il layout originale resta aperto come nel gioco. Le **porte con serratura**, la **porta del boss**
    e i **blocchi-serratura** sono `D`; i **muri bombardabili** restano muro;
  - **larghezza dei varchi**: nel gioco ogni porta/apertura nei muri è larga 16 px (un blocco) ma è centrata sul
    confine tra due celle: il gioco la disegna con due oggetti "metà muro, metà passaggio" (physics `7C`/`7D` lato
    sinistro/destro solido, `7E`/`7F` lato alto/basso solido). Nella griglia il varco occupa **una sola cella**:
    la metà 1 (sinistra/alto) è il passaggio (o `D`), la metà 2 è muro (campo `pair` nei JSON). Stessa convenzione
    in tutte le stanze, quindi i varchi di stanze adiacenti restano allineati;
  - le **buche**, la **lava** e gli **spuntoni** sono `~` (non attraversabili); l'acqua bassa è pavimento;
  - "fuori mappa" (0): cielo e orizzonte dell'overworld; il riempimento a tinta unita `03` fuori dai muri
    (angoli e lati delle stanze dei dungeon); le buche attorno alle stanze più piccole dello schermo;
    nelle caverne e nelle case, la roccia esterna mai raggiungibile (vedi sotto).
- **Analisi di connettività tra stanze** (caverne e case, `categories.json` → `exterior`): partendo dai punti in cui
  il gioco fa comparire Link (arrivi dei warp) si visitano le celle non-muro, passando tra le stanze con la stessa regola del gioco
  (`room_transition.asm`: minimappa 8×8 per dungeon/Color Dungeon/caverne `0x0A`, id ±1/±16 per gli altri interni).
  Le zone mai raggiunte che toccano il bordo dello schermo sono l'esterno della stanza e diventano 0. Nei dungeon non si
  applica, perché molte zone si raggiungono con meccanismi non modellati (blocchi a interruttore, cadute dall'alto).
- Entità: nemici, miniboss e boss diventano `M` (solo su pavimento). Statue o telefoni diventano muro,
  le statue e i pezzi sollevabili diventano blocco. NPC, oggetti ed eventi vengono ignorati, ma restano annotati.
- Tile e entità speciali (`special_policy`): interruttori, blocchi a interruttore, nastri, sabbie mobili,
  teletrasporti, blocchi mobili, piastrelle colorate → stanza scartata; spuntoni, serrature e scale nascoste → solo segnalati.

## Validità (da `categories.json`)

1. **Bordi: il layout originale non viene toccato.** Porte e varchi sul bordo restano come nel gioco e sono elencati in `openings`.
   La regola del brief "bordi chiusi" resta disponibile con `validity.close_border = true` (ogni cella di bordo
   diversa da muro o "fuori mappa" diventa muro).
2. Giocatore (unica aggiunta alla griglia): nel punto d'arrivo di un warp, se esiste; altrimenti nella cella interna accanto a
   un varco (prima porte e aperture, poi corridoi). Tra più candidati si preferisce quello da cui si raggiungono le scale del gioco.
3. **Scale: mai inventate.** Se la stanza non ne ha, `brief_checks.has_stairs = false`. La vecchia regola del brief
   (scale sulla cella più lontana) si riattiva solo con `validity.add_stairs = true`.
4. Porte chiuse contate come gruppi di celle `D`; le porte bloccano la BFS finché non si raggiunge una chiave.
   I nemici non bloccano la BFS (`bfs_enemies_passable`): si muovono e si sconfiggono.

`valid` = stanza fedele e utilizzabile. Sono scartate le stanze a scorrimento laterale, vuote o non usate, con tile speciali
da scartare, o senza pavimento per il giocatore. Le regole del brief (scale, bordi chiusi, max 2 porte) sono solo
verificate in `brief_checks`; `brief_valid` = `valid` + tutte le regole del brief rispettate.
I dettagli e i numeri sono in `report.md`.
