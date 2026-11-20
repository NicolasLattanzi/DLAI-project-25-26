# Legenda LevelEdit <- Link's Awakening DX

Generata da `make_legend.py` a partire dai file in `mappings/`. Nessun dato grafico del gioco.

## Regole di conversione

- Mappatura **1:1** con il gioco: ogni blocco 16x16 della stanza diventa una cella; nulla viene inventato.
- Unica aggiunta: il giocatore `P`, dove il gioco fa entrare Link (arrivo da warp) o accanto al varco d'ingresso.
- Le scale `E` sono solo quelle presenti nel gioco: se la stanza non ne ha, non ce ne sono.
- Bordi non chiusi: porte, varchi e corridoi sul bordo restano come nel gioco.
- Porte e varchi nei muri sono larghi un blocco (16 px) ma centrati tra due celle: la meta' 1 (sinistra/alto) e' il passaggio (o `D`), la meta' 2 e' muro. Stessa convenzione in tutte le stanze, quindi i varchi adiacenti restano allineati.
- Fuori mappa (spazio): cielo/orizzonte dell'overworld, riempimento `03` fuori dai muri, spazio attorno alle stanze piccole, roccia esterna delle caverne mai raggiungibile.
- Ogni room.json ha due griglie: `grid_ascii` (layout + `P` + `M`) e `grid_no_entities_ascii` (solo il layout).

## Categorie

| Codice | Simbolo | Categoria | Attraversabile | Colore | Cosa diventa dal gioco |
|---|---|---|---|---|---|
| 0 | (spazio) | fuori mappa | False | #000000 | riempimento: cielo/orizzonte dell'overworld; riempimento a tinta unita (03) fuori dai muri delle stanze; buche attorno alle stanze piu' piccole dello schermo; roccia esterna delle caverne mai raggiungibile |
| 1 | `#` | muro | False | #606068 | muri, statue, torce, colonne, forzieri, mobili, muri bombardabili; meta' 2 (destra/basso) di ogni porta o varco largo un blocco; all'aperto alberi, rocce, scogliere, case |
| 2 | `.` | pavimento | True | #DED0AA | pavimento, gradini, acqua bassa; varchi aperti, porte a saracinesca e a senso unico, muri girevoli (meta' 1 del varco: una sola cella); all'aperto erba, sentieri |
| 3 | `~` | acqua | False | #3A70D6 | acqua profonda, buche, lava (e spuntoni come pericolo) |
| 4 | `=` | ponte | True | #A87038 | ponti di legno, ponte delle scimmie costruito |
| 5 | `D` | porta chiusa | with_key | #C82828 | porte con serratura, porta del boss, blocchi-serratura (una porta = una sola cella D: la meta' 2 e' muro) |
| 6 | `K` | chiave | True | #FAD600 | non visibile nelle stanze: le fonti di chiavi sono solo annotate nei metadati (key_sources) |
| 7 | `B` | blocco | False | #824E22 | blocchi spingibili, vasi, cristalli; all'aperto cespugli |
| 8 | `E` | scale | True | #28BE5A | solo le scale/uscite presenti nel gioco (scale verso altri piani, scale nel muro, porte di caverne/case): mai aggiunte |
| 9 | `P` | giocatore | True | #00BEFF | non nei dati della stanza: unica aggiunta alla griglia, nel punto in cui il gioco fa entrare Link (arrivo da warp) o accanto al varco d'ingresso; assente in grid_no_entities |
| 10 | `M` | nemico | False | #E200C4 | nemici, miniboss e boss (dalle entita' della stanza); assenti in grid_no_entities |

## Regole speciali

| Tipo | Politica |
|---|---|
| conveyor | discard |
| quicksand | discard |
| teleport | discard |
| switch | discard |
| switch_block | discard |
| moving_block | discard |
| tractor_device | discard |
| color_tile | discard |
| spikes | flag |
| keyhole | flag |
| hidden_stairs | flag |
| unmapped | discard |

## Oggetti overworld

| Id | Simbolo | Categoria | Nome | Tag / speciale | Physics | Celle nel gioco |
|---|---|---|---|---|---|---|
| 00 | (spazio) | fuori mappa | sky | sky | 01 | 147 |
| 03 | `.` | pavimento | dirt |  | 00 | 1107 |
| 04 | `.` | pavimento | short grass |  | 00 | 3771 |
| 05 | `#` | muro | Wind Fish's Egg | egg | 01 | 1 |
| 06 | `#` | muro | Wind Fish's Egg | egg | 01 | 1 |
| 07 | `#` | muro | Wind Fish's Egg | egg | 01 | 1 |
| 08 | `.` | pavimento | ground decoration (leaves/sand marks) |  | 00 | 579 |
| 09 | `.` | pavimento | rocky ground |  | 00 | 177 |
| 0A | `.` | pavimento | tall grass (cuttable) | grass | 06 | 957 |
| 0B | `.` | pavimento | path |  | 00 | 270 |
| 0C | `.` | pavimento | paved tiles |  | 00 | 144 |
| 0D | `.` | pavimento | decorative paving |  | 00 | 77 |
| 0E | `~` | acqua | deep water | deep_water | 07 | 1261 |
| 0F | `.` | pavimento | water bank (walkable shore edge) | shore | 00 | 28 |
| 10 | `.` | pavimento | water bank (walkable shore edge) | shore | 00 | 25 |
| 11 | `.` | pavimento | water bank (walkable shore edge) | shore | 00 | 27 |
| 12 | `.` | pavimento | water bank (walkable shore edge) | shore | 00 | 31 |
| 13 | `.` | pavimento | water bank (walkable shore edge) | shore | 00 | 6 |
| 14 | `.` | pavimento | water bank (walkable shore edge) | shore | 00 | 9 |
| 15 | `.` | pavimento | water bank (walkable shore edge) | shore | 00 | 8 |
| 16 | `.` | pavimento | water bank (walkable shore edge) | shore | 00 | 11 |
| 17 | `.` | pavimento | water bank (walkable shore edge) | shore | 00 | 10 |
| 18 | `.` | pavimento | water bank (walkable shore edge) | shore | 00 | 11 |
| 19 | `.` | pavimento | water bank (walkable shore edge) | shore | 00 | 12 |
| 1A | `.` | pavimento | water bank (walkable shore edge) | shore | 00 | 15 |
| 1B | `.` | pavimento | shallow water | shallow_water | 05 | 289 |
| 1C | (spazio) | fuori mappa | sky above sea horizon | sky | 01 | 17 |
| 1D | `#` | muro | cliff dropping into the sea | cliff | 01 | 21 |
| 1E | `.` | pavimento | shallow waves | shallow_water | 05 | 50 |
| 1F | `~` | acqua | sea (ocean edge) | sea | 04 | 108 |
| 20 | `#` | muro | liftable rock | rock, liftable | 30 | 88 |
| 21 | `#` | muro | dense foliage | tree | 01 | 8 |
| 23 | `.` | pavimento | sand with decoration |  | 00 | 3 |
| 24 | `.` | pavimento | sand with decoration |  | 00 | 19 |
| 25 | `#` | muro | tree (top-left) | tree | 01 | 400 |
| 26 | `#` | muro | tree (top-right) | tree | 01 | 418 |
| 27 | `#` | muro | tree (bottom-left) | tree | 01 | 406 |
| 28 | `#` | muro | tree (bottom-right) | tree | 01 | 413 |
| 29 | `#` | muro | tree (overlap left) | tree | 01 | 209 |
| 2A | `#` | muro | tree (overlap right) | tree | 01 | 191 |
| 2B | `#` | muro | cliff / raised ground edge | cliff | 01 | 70 |
| 2C | `#` | muro | cliff / raised ground edge | cliff | 01 | 408 |
| 2D | `#` | muro | cliff / raised ground edge | cliff | 01 | 71 |
| 2E | `#` | muro | cliff / raised ground edge | cliff | 01 | 94 |
| 2F | `#` | muro | cliff / raised ground edge | cliff | 01 | 804 |
| 30 | `.` | pavimento | swamp plants in shallow water | shallow_water | 05 | 23 |
| 31 | `#` | muro | cliff / raised ground edge | cliff | 01 | 39 |
| 32 | `#` | muro | cliff / raised ground edge | cliff | 01 | 37 |
| 33 | `#` | muro | cliff / raised ground edge | cliff | 01 | 60 |
| 34 | `#` | muro | cliff / raised ground edge | cliff | 01 | 58 |
| 35 | `#` | muro | cliff / raised ground edge | cliff | 01 | 14 |
| 36 | `#` | muro | cliff / raised ground edge | cliff | 01 | 14 |
| 37 | `#` | muro | cliff / raised ground edge | cliff | 01 | 518 |
| 38 | `#` | muro | cliff / raised ground edge | cliff | 01 | 527 |
| 39 | `#` | muro | cliff / raised ground edge | cliff | 01 | 82 |
| 3A | `#` | muro | cliff / raised ground edge | cliff | 01 | 1055 |
| 3B | `#` | muro | cliff / raised ground edge | cliff | 01 | 96 |
| 3C | `#` | muro | cliff / raised ground edge | cliff | 01 | 85 |
| 3D | `#` | muro | cliff / raised ground edge | cliff | 01 | 91 |
| 3E | `#` | muro | cliff / raised ground edge | cliff | 01 | 55 |
| 3F | `#` | muro | cliff / raised ground edge | cliff | 01 | 74 |
| 40 | `#` | muro | shop / building front | building | 01 | 3 |
| 41 | `#` | muro | shop / building front | building | 01 | 2 |
| 42 | `#` | muro | shop / building front | building | 01 | 3 |
| 43 | `#` | muro | ledge (jump down only) | ledge | 10 | 3 |
| 44 | `.` | pavimento | flowers |  | 00 | 241 |
| 45 | `#` | muro | phone booth (tree) | building | 01 | 8 |
| 48 | `#` | muro | cliff / raised ground edge | cliff | 01 | 63 |
| 49 | `#` | muro | cliff / raised ground edge | cliff | 01 | 62 |
| 4A | `#` | muro | ledge (jump down only) | ledge | 10 | 27 |
| 4B | `#` | muro | cliff / raised ground edge | cliff | 01 | 7 |
| 4C | `#` | muro | cliff / raised ground edge | cliff | 01 | 2 |
| 4D | `#` | muro | cliff / raised ground edge | cliff | 01 | 30 |
| 4E | `#` | muro | cliff / raised ground edge | cliff | 01 | 104 |
| 4F | `#` | muro | tree cluster | tree | 01 | 9 |
| 50 | `#` | muro | cliff / raised ground edge | cliff | 01 | 60 |
| 51 | `#` | muro | thorny vines |  | 01 | 142 |
| 52 | `#` | muro | fence / building wall | building | 01 | 34 |
| 54 | `#` | muro | keyhole (dungeon key slot) | keyhole **[keyhole]** | C0 | 2 |
| 55 | `#` | muro | building part | building | 01 | 10 |
| 56 | `#` | muro | building part | building | 01 | 10 |
| 57 | `#` | muro | building part | building | 01 | 7 |
| 58 | `#` | muro | building part | building | 01 | 7 |
| 59 | `#` | muro | building part | building | 01 | 10 |
| 5A | `#` | muro | building part | building | 01 | 11 |
| 5B | `#` | muro | building part | building | 01 | 45 |
| 5C | `B` | blocco | bush (cuttable) | bush | 30 | 307 |
| 5D | `#` | muro | cliff / raised ground edge | cliff | 01 | 14 |
| 5E | `#` | muro | weather vane base |  | 01 | 1 |
| 5F | `#` | muro | building part | building | 01 | 5 |
| 60 | `#` | muro | building part | building | 01 | 10 |
| 61 | `#` | muro | well |  | 01 | 4 |
| 62 | `#` | muro | fence posts |  | 01 | 65 |
| 63 | `#` | muro | Wind Fish's Egg | egg | 01 | 1 |
| 64 | `#` | muro | Wind Fish's Egg | egg | 01 | 1 |
| 65 | `#` | muro | Wind Fish's Egg | egg | 01 | 1 |
| 66 | `#` | muro | building part | building | 01 | 2 |
| 67 | `#` | muro | building part | building | 01 | 1 |
| 68 | `#` | muro | building part | building | 01 | 1 |
| 69 | `#` | muro | cactus (hurts) |  | 01 | 17 |
| 6A | `#` | muro | building part | building | 01 | 2 |
| 6B | `#` | muro | building part | building | 01 | 2 |
| 6C | `#` | muro | building part | building | 01 | 3 |
| 6E | `#` | muro | rounded stone block | stone_block | 60 | 136 |
| 6F | `#` | muro | owl statue | statue | 01 | 9 |
| 70 | `#` | muro | keyhole (dungeon key slot) | keyhole **[keyhole]** | C0 | 1 |
| 71 | `#` | muro | Wind Fish's Egg | egg | 01 | 1 |
| 72 | `#` | muro | castle wall | building | 01 | 4 |
| 73 | `#` | muro | castle wall | building | 01 | 4 |
| 74 | `#` | muro | castle wall | building | 01 | 12 |
| 75 | `#` | muro | castle wall | building | 01 | 1 |
| 76 | `#` | muro | castle wall | building | 01 | 1 |
| 78 | `=` | ponte | wooden bridge | bridge | 08 | 11 |
| 79 | `=` | ponte | wooden bridge | bridge | 08 | 11 |
| 7A | `=` | ponte | wooden bridge | bridge | 08 | 38 |
| 7B | `~` | acqua | hole in bridge | pit | 50 | 9 |
| 7C | (spazio) | fuori mappa | clouds / sky over the sea | sky | 01 | 29 |
| 7D | (spazio) | fuori mappa | clouds / sky over the sea | sky | 01 | 29 |
| 7E | (spazio) | fuori mappa | clouds / sky over the sea | sky | 01 | 8 |
| 7F | `#` | muro | Wind Fish's Egg | egg | 01 | 1 |
| 80 | `#` | muro | cliff corner (top-left) | cliff | 01 | 10 |
| 81 | `#` | muro | cliff corner (top-right) | cliff | 01 | 10 |
| 82 | `#` | muro | forest tree part | tree | 01 | 62 |
| 83 | `#` | muro | forest tree part | tree | 01 | 48 |
| 84 | `#` | muro | forest tree part | tree | 01 | 58 |
| 85 | `#` | muro | forest tree part | tree | 01 | 58 |
| 86 | `#` | muro | forest tree part | tree | 01 | 65 |
| 87 | `#` | muro | forest tree part | tree | 01 | 71 |
| 88 | `#` | muro | forest tree part | tree | 01 | 15 |
| 89 | `#` | muro | forest tree part | tree | 01 | 13 |
| 8A | `#` | muro | forest tree part | tree | 01 | 9 |
| 8B | `#` | muro | forest tree part | tree | 01 | 9 |
| 8C | `#` | muro | forest tree part | tree | 01 | 18 |
| 8D | `#` | muro | forest tree part | tree | 01 | 17 |
| 8E | `#` | muro | forest tree part | tree | 01 | 15 |
| 8F | `#` | muro | forest tree part | tree | 01 | 15 |
| 90 | `#` | muro | forest tree part | tree | 01 | 22 |
| 91 | `#` | muro | weather vane top |  | 01 | 1 |
| 92 | `#` | muro | forest tree part | tree | 01 | 3 |
| 93 | `#` | muro | brick wall (village/castle) | building | 01 | 50 |
| 94 | `#` | muro | brick wall (village/castle) | building | 01 | 7 |
| 95 | `#` | muro | brick wall (village/castle) | building | 01 | 7 |
| 96 | `#` | muro | brick wall (village/castle) | building | 01 | 50 |
| 97 | `#` | muro | brick wall (village/castle) | building | 01 | 7 |
| 98 | `#` | muro | brick wall (village/castle) | building | 01 | 7 |
| 99 | `#` | muro | brick wall (village/castle) | building | 01 | 69 |
| 9A | `#` | muro | brick wall (village/castle) | building | 01 | 64 |
| 9B | `#` | muro | brick wall (village/castle) | building | 01 | 11 |
| 9C | `#` | muro | brick wall (village/castle) | building | 01 | 11 |
| 9D | `#` | muro | brick wall (village/castle) | building | 01 | 11 |
| 9E | `#` | muro | brick wall (village/castle) | building | 01 | 11 |
| 9F | `#` | muro | brick wall (village/castle) | building | 01 | 2 |
| A0 | `#` | muro | stone face block | stone_block | 60 | 10 |
| A1 | `#` | muro | brick wall (village/castle) | building |  | 0 |
| A2 | `#` | muro | brick wall (village/castle) | building | 01 | 6 |
| A3 | `#` | muro | brick wall (village/castle) | building | 01 | 2 |
| A4 | `.` | pavimento | castle gateway floor |  | 00 | 3 |
| A5 | `#` | muro | castle gate part | building | 01 | 3 |
| A6 | `#` | muro | castle gate part | building | 01 | 3 |
| A7 | `#` | muro | castle gate part | building | 01 | 3 |
| A8 | `#` | muro | castle gate part | building | 01 | 3 |
| A9 | `#` | muro | Wind Fish's Egg | egg | 01 | 1 |
| AA | `#` | muro | Wind Fish's Egg | egg | 01 | 1 |
| AB | `#` | muro | building part | building | 01 | 3 |
| AC | `#` | muro | building part | building | 01 | 3 |
| AD | `#` | muro | building part | building | 01 | 2 |
| AE | `#` | muro | building part | building | 01 | 2 |
| AF | `#` | muro | building part | building | 01 | 2 |
| B0 | `#` | muro | building part | building | 01 | 2 |
| B1 | `#` | muro | building part | building | 01 | 2 |
| B2 | `#` | muro | building part | building | 01 | 2 |
| B3 | `.` | pavimento | decorative floor tile |  | 00 | 24 |
| B6 | `#` | muro | rock wall / statue |  | 01 | 221 |
| B7 | `#` | muro | rock wall / statue |  | 01 | 174 |
| B8 | `#` | muro | building part | building | 01 | 19 |
| B9 | `.` | pavimento | decorative floor tile |  | 00 | 72 |
| BA | `#` | muro | bombable cave wall | bombable (varco) | 99 | 7 |
| BB | `#` | muro | giant skull rock |  | 01 | 1 |
| BC | `#` | muro | giant skull rock |  | 01 | 1 |
| BD | `#` | muro | giant skull rock |  | 01 | 1 |
| BE | `#` | muro | giant skull rock |  | 01 | 1 |
| BF | `#` | muro | Wind Fish's Egg | egg | 01 | 1 |
| C0 | `#` | muro | keyhole (dungeon key slot) | keyhole **[keyhole]** | C0 | 2 |
| C2 | `#` | muro | closed gate |  | 01 | 2 |
| C3 | `#` | muro | cave/tree entrance structure |  | 01 | 1 |
| C4 | `#` | muro | gravestone |  | 01 | 16 |
| C5 | `#` | muro | gravestone |  | 01 | 6 |
| C6 | `E` | scale | stairs in the ground | stairs_down | 09 | 13 |
| C8 | `#` | muro | stone pillar / rock |  | 60 | 140 |
| CA | `#` | muro | rocks in water |  | 01 | 43 |
| CD | `#` | muro | statue / big tree part |  | 01 | 100 |
| CE | `#` | muro | statue / big tree part |  | 01 | 100 |
| CF | `.` | pavimento | quicksand (pulls Link) | quicksand **[quicksand]** | F4 | 11 |
| D0 | `.` | pavimento | quicksand (pulls Link) | quicksand **[quicksand]** | F5 | 11 |
| D1 | `.` | pavimento | quicksand (pulls Link) | quicksand **[quicksand]** | F6 | 12 |
| D2 | `.` | pavimento | quicksand (pulls Link) | quicksand **[quicksand]** | F7 | 12 |
| D3 | `B` | blocco | bush hiding stairs | bush | 30 | 73 |
| D4 | `#` | muro | signpost |  | 60 | 37 |
| D6 | `#` | muro | building part | building | 01 | 1 |
| D7 | `#` | muro | cave entrance structure |  | 01 | 2 |
| D8 | `#` | muro | monkey bridge anchor (top) |  | 01 | 1 |
| D9 | `~` | acqua | monkey bridge gap (not built yet: water) |  | 07 | 1 |
| DA | `#` | muro | monkey bridge anchor (bottom) |  | 01 | 1 |
| DB | `=` | ponte | monkey bridge (built) | bridge | 08 | 5 |
| DC | `.` | pavimento | ground under weather vane |  | 00 | 1 |
| DD | `#` | muro | cliff / raised ground edge | cliff | 01 | 10 |
| DE | `#` | muro | cliff / raised ground edge | cliff | 01 | 8 |
| E0 | `.` | pavimento | steps between cliff levels | steps | 02 | 96 |
| E1 | `E` | scale | rocky cave entrance (exit) | exit, cave_door | 03 | 49 |
| E2 | `E` | scale | house door (exit) | exit, house_door | 03 | 24 |
| E3 | `E` | scale | cave entrance (exit) | exit, cave_door | 03 | 8 |
| E4 | `#` | muro | tree with face / stump |  | 01 | 3 |
| E5 | `~` | acqua | deep sea | sea | 01 | 101 |
| E6 | `#` | muro | rock edge (8x8 collision) | fine_collision | 81 | 1 |
| E7 | `E` | scale | castle door (exit) | exit, house_door | 03 | 1 |
| E8 | `~` | acqua | hole in the ground | pit | 50 | 121 |
| E9 | `~` | acqua | waterfall |  | 01 | 81 |
| EA | `#` | muro | cliff / raised ground edge | cliff | 01 | 5 |
| EB | `~` | acqua | deep water (river) | deep_water | 07 | 314 |
| EC | `~` | acqua | deep water (river) | deep_water | 07 | 39 |
| ED | `~` | acqua | deep water (river) | deep_water | 07 | 166 |
| EE | `~` | acqua | deep water (river) | deep_water | 07 | 103 |
| EF | `~` | acqua | drop into the sea / pit | pit | 50 | 84 |
| F0 | `#` | muro | ledge (jump in one direction) | ledge | D1 | 7 |
| F1 | `#` | muro | rock / cliff piece | cliff | 01 | 5 |
| F2 | `#` | muro | rock / cliff piece | cliff | 01 | 5 |
| F3 | `#` | muro | ledge (jump in one direction) | ledge | D0 | 7 |
| F4 | `#` | muro | rock / cliff piece | cliff | 01 | 5 |

## Oggetti interni (dungeon, caverne, case)

| Id | Simbolo | Categoria | Nome | Tag / speciale | Physics | Celle nel gioco |
|---|---|---|---|---|---|---|
| 00 | `.` | pavimento | floor (sand/earth variant) |  | 00 | 553 |
| 01 | `~` | acqua | pit | pit | 50 | 767 |
| 03 | (spazio) | fuori mappa | blank filler outside the room (flat color) | filler | 00 | 911 |
| 05 | `.` | pavimento | floor (cave ground) |  | 00 | 1383 |
| 06 | `~` | acqua | lava | lava | 0B | 273 |
| 07 | `.` | pavimento | floor (checkered) |  | 00 | 332 |
| 08 | `#` | muro | open doorway, bottom wall (right half) | open_door, door_half2 (meta' 2 del varco 8C: muro) | 7D | 28 |
| 09 | `.` | pavimento | open doorway, left wall (top half) | open_door, door_half1 (varco) (meta' 1 del varco, coppia con 0A) | 7E | 18 |
| 0A | `#` | muro | open doorway, left wall (bottom half) | open_door, door_half2 (meta' 2 del varco 09: muro) | 7F | 18 |
| 0B | `.` | pavimento | open doorway, right wall (top half) | open_door, door_half1 (varco) (meta' 1 del varco, coppia con 0C) | 7E | 16 |
| 0C | `#` | muro | open doorway, right wall (bottom half) | open_door, door_half2 (meta' 2 del varco 0B: muro) | 7F | 16 |
| 0D | `.` | pavimento | floor (standard dungeon floor) |  | 00 | 9357 |
| 0E | `~` | acqua | deep water | deep_water | 07 | 352 |
| 0F | `.` | pavimento | floor (patterned tiles) |  | 00 | 1803 |
| 10 | `#` | muro | raised-floor border, side/corner (8x8 collision) | fine_collision | 81 | 145 |
| 11 | `#` | muro | raised-floor border, side/corner (8x8 collision) | fine_collision | 80 | 150 |
| 12 | `#` | muro | raised-floor border, side/corner (8x8 collision) | fine_collision | 82 | 216 |
| 13 | `#` | muro | raised-floor border, side/corner (8x8 collision) | fine_collision | 83 | 202 |
| 14 | `#` | muro | raised-floor border, side/corner (8x8 collision) | fine_collision | 84 | 25 |
| 15 | `#` | muro | raised-floor border, side/corner (8x8 collision) | fine_collision | 85 | 21 |
| 16 | `#` | muro | raised-floor border, side/corner (8x8 collision) | fine_collision | 86 | 24 |
| 17 | `#` | muro | raised-floor border, side/corner (8x8 collision) | fine_collision | 87 | 21 |
| 1B | `.` | pavimento | shallow water | shallow_water | 05 | 783 |
| 1C | `~` | acqua | pit dropping to the floor below | pit, pit_warp | 51 | 146 |
| 1D | `~` | acqua | pit dropping to the floor below | pit, pit_warp | 51 | 22 |
| 1E | `~` | acqua | pit dropping to the floor below | pit, pit_warp | 51 | 17 |
| 1F | `~` | acqua | pit dropping to the floor below | pit, pit_warp | 51 | 18 |
| 20 | `B` | blocco | liftable pot | liftable | 30 | 431 |
| 21 | `#` | muro | wall (top) |  | D3 | 2462 |
| 22 | `#` | muro | wall (bottom) |  | D2 | 2455 |
| 23 | `#` | muro | wall (left) |  | D0 | 1988 |
| 24 | `#` | muro | wall (right) |  | D1 | 2016 |
| 25 | `#` | muro | wall outer corner (top-left) |  | 01 | 612 |
| 26 | `#` | muro | wall outer corner (top-right) |  | 01 | 619 |
| 27 | `#` | muro | wall outer corner (bottom-left) |  | 01 | 507 |
| 28 | `#` | muro | wall outer corner (bottom-right) |  | 01 | 500 |
| 29 | `#` | muro | wall inner corner |  | 01 | 416 |
| 2A | `#` | muro | wall inner corner |  | 01 | 428 |
| 2B | `#` | muro | wall inner corner |  | 01 | 309 |
| 2C | `#` | muro | wall inner corner |  | 01 | 306 |
| 2D | `D` | porta chiusa | locked key door, top wall (half 1) | key_door, door_half1 (varco) (meta' 1 del varco, coppia con 2E) | 90 | 10 |
| 2E | `#` | muro | locked key door, top wall (half 2) | key_door, door_half2 (meta' 2 del varco 2D: muro) | 90 | 10 |
| 2F | `D` | porta chiusa | locked key door, bottom wall (half 1) | key_door, door_half1 (varco) (meta' 1 del varco, coppia con 30) | 91 | 9 |
| 30 | `#` | muro | locked key door, bottom wall (half 2) | key_door, door_half2 (meta' 2 del varco 2F: muro) | 91 | 9 |
| 31 | `D` | porta chiusa | locked key door, left wall (half 1) | key_door, door_half1 (varco) (meta' 1 del varco, coppia con 32) | 92 | 10 |
| 32 | `#` | muro | locked key door, left wall (half 2) | key_door, door_half2 (meta' 2 del varco 31: muro) | 92 | 10 |
| 33 | `D` | porta chiusa | locked key door, right wall (half 1) | key_door, door_half1 (varco) (meta' 1 del varco, coppia con 34) | 93 | 9 |
| 34 | `#` | muro | locked key door, right wall (half 2) | key_door, door_half2 (meta' 2 del varco 33: muro) | 93 | 9 |
| 35 | `.` | pavimento | shutter door, top wall (half 1) | shutter_door, door_half1 (varco) (meta' 1 del varco, coppia con 36) | D3 | 46 |
| 36 | `#` | muro | shutter door, top wall (half 2) | shutter_door, door_half2 (meta' 2 del varco 35: muro) | D3 | 46 |
| 37 | `.` | pavimento | shutter door, bottom wall (half 1) | shutter_door, door_half1 (varco) (meta' 1 del varco, coppia con 38) | D2 | 38 |
| 38 | `#` | muro | shutter door, bottom wall (half 2) | shutter_door, door_half2 (meta' 2 del varco 37: muro) | D2 | 38 |
| 39 | `.` | pavimento | shutter door, left wall (half 1) | shutter_door, door_half1 (varco) (meta' 1 del varco, coppia con 3A) | D0 | 28 |
| 3A | `#` | muro | shutter door, left wall (half 2) | shutter_door, door_half2 (meta' 2 del varco 39: muro) | D0 | 28 |
| 3B | `.` | pavimento | shutter door, right wall (half 1) | shutter_door, door_half1 (varco) (meta' 1 del varco, coppia con 3C) | D1 | 32 |
| 3C | `#` | muro | shutter door, right wall (half 2) | shutter_door, door_half2 (meta' 2 del varco 3B: muro) | D1 | 32 |
| 3D | `.` | pavimento | bombed passage (vertical, open) | bombed_passage (varco) | 00 | 4 |
| 3E | `.` | pavimento | bombed passage (horizontal, open) | bombed_passage (varco) | 00 | 2 |
| 3F | `#` | muro | bombable cracked wall (top) | bombable (varco) | 99 | 3 |
| 40 | `#` | muro | bombable cracked wall (bottom) | bombable (varco) | 9A | 7 |
| 41 | `#` | muro | bombable cracked wall (left) | bombable (varco) | 9B | 5 |
| 42 | `#` | muro | bombable cracked wall (right) | bombable (varco) | 9C | 3 |
| 43 | `.` | pavimento | open doorway, top wall (left half) | open_door, door_half1 (varco) (meta' 1 del varco, coppia con 44) | 7C | 8 |
| 44 | `#` | muro | open doorway, top wall (right half) | open_door, door_half2 (meta' 2 del varco 43: muro) | 7D | 8 |
| 45 | `.` | pavimento | one-way door, top wall (half 1) | one_way_door, door_half1 (varco) (meta' 1 del varco, coppia con 46) | 01 | 7 |
| 46 | `#` | muro | one-way door, top wall (half 2) | one_way_door, door_half2 (meta' 2 del varco 45: muro) | 01 | 7 |
| 47 | `#` | muro | hidden bombable wall (top) | bombable, hidden (varco) | 99 | 8 |
| 48 | `#` | muro | hidden bombable wall (bottom) | bombable, hidden (varco) | 9A | 3 |
| 49 | `#` | muro | hidden bombable wall (left) | bombable, hidden (varco) | 9B | 3 |
| 4A | `#` | muro | hidden bombable wall (right) | bombable, hidden (varco) | 9C | 5 |
| 4E | `B` | blocco | crystal rock (breakable with Pegasus Boots dash) | removable | 60 | 15 |
| 4F | `B` | blocco | crystal rock (breakable with Pegasus Boots dash) | removable | 60 | 10 |
| 86 | `#` | muro | stone statue (pair) | statue | 01 | 3 |
| 87 | `#` | muro | stone statue | statue | 01 | 12 |
| 88 | `B` | blocco | crystal rock (breakable with Pegasus Boots dash) | removable | 60 | 17 |
| 8B | `#` | muro | decorative solid tile |  | 01 | 8 |
| 8C | `.` | pavimento | open doorway, bottom wall (left half) | open_door, door_half1 (varco) (meta' 1 del varco, coppia con 08) | 7C | 28 |
| 8D | `.` | pavimento | floor pad/marking |  | 00 | 10 |
| 8E | `B` | blocco | pot hiding a floor switch | liftable **[switch]** | 30 | 3 |
| 90 | `#` | muro | wall ornament |  | 01 | 2 |
| 93 | `#` | muro | raised-floor border, outer corner (8x8 collision) | fine_collision | 88 | 16 |
| 94 | `#` | muro | raised-floor border, outer corner (8x8 collision) | fine_collision | 89 | 12 |
| 95 | `#` | muro | raised-floor border, outer corner (8x8 collision) | fine_collision | 8A | 10 |
| 96 | `#` | muro | raised-floor border, outer corner (8x8 collision) | fine_collision | 8B | 8 |
| 97 | `.` | pavimento | wide steps between floor levels | steps | 0A | 44 |
| 98 | `.` | pavimento | steps between floor levels | steps | 02 | 63 |
| 99 | `#` | muro | furniture (cabinet) | furniture | 01 | 44 |
| 9A | `#` | muro | furniture (lower part of a dresser/cabinet) | furniture | 7E | 44 |
| 9B | `#` | muro | furniture (bed/sofa) | furniture | 01 | 15 |
| 9C | `#` | muro | furniture (bed/sofa) | furniture | 01 | 13 |
| 9E | `.` | pavimento | ladder/hookshot-bridge marker | ladder | 00 | 2 |
| 9F | `.` | pavimento | ladder/hookshot-bridge marker | ladder | 00 | 1 |
| A0 | `#` | muro | treasure chest (closed) | chest | 60 | 83 |
| A1 | `#` | muro | treasure chest (open) | chest | 60 | 21 |
| A2 | `E` | scale | staircase in wall (exit to another floor) | exit | 03 | 4 |
| A3 | `E` | scale | staircase in wall (exit to another floor) | exit | 03 | 12 |
| A4 | `D` | porta chiusa | boss door (nightmare key), half 1 | boss_door, door_half1 (varco) (meta' 1 del varco, coppia con A5) | 98 | 8 |
| A5 | `#` | muro | boss door (nightmare key), half 2 | boss_door, door_half2 (meta' 2 del varco A4: muro) | 98 | 8 |
| A6 | `#` | muro | stone block (immovable) | stone_block | 60 | 486 |
| A7 | `B` | blocco | pushable block | pushable | 60 | 147 |
| A8 | `E` | scale | staircase in wall (exit to another floor) | exit | 03 | 2 |
| A9 | `B` | blocco | bombable block | removable | 30 | 14 |
| AA | `.` | pavimento | floor switch | switch **[switch]** | 00 | 5 |
| AB | `#` | muro | torch (unlit) | torch | 01 | 40 |
| AC | `#` | muro | torch (lit) | torch | 01 | 246 |
| AE | `~` | acqua | pit (edge variant) | pit | 50 | 202 |
| AF | `~` | acqua | pit (edge variant) | pit | 50 | 219 |
| B0 | `~` | acqua | pit (edge variant) | pit | 50 | 254 |
| B1 | `.` | pavimento | flip wall / rotating door (half 1) | flip_wall, door_half1 (varco) (meta' 1 del varco, coppia con B2) | 7C | 7 |
| B2 | `#` | muro | flip wall / rotating door (half 2) | flip_wall, door_half2 (meta' 2 del varco B1: muro) | 7D | 7 |
| B3 | `.` | pavimento | dungeon entrance: floor |  | 00 | 14 |
| B4 | `.` | pavimento | dungeon entrance: floor |  | 00 | 26 |
| B5 | `.` | pavimento | dungeon entrance: floor |  | 00 | 14 |
| B6 | `#` | muro | dungeon entrance: frame (8x8 collision) | fine_collision | 8B | 12 |
| B7 | `.` | pavimento | dungeon entrance: archway walkway (8x8 collision) | fine_collision, dungeon_entrance, door_half1 (meta' 1 del varco, coppia con B8) | 8A | 12 |
| B8 | `#` | muro | dungeon entrance: archway walkway (8x8 collision) | fine_collision, dungeon_entrance, door_half2 (meta' 2 del varco B7: muro) | 8B | 12 |
| B9 | `#` | muro | dungeon entrance: frame (8x8 collision) | fine_collision | 8A | 12 |
| BA | `#` | muro | dungeon entrance: frame |  | 01 | 12 |
| BB | `.` | pavimento | dungeon entrance doorway (half 1) | dungeon_entrance, door_half1 (varco) (meta' 1 del varco, coppia con BC) | 7C | 12 |
| BC | `#` | muro | dungeon entrance doorway (half 2) | dungeon_entrance, door_half2 (meta' 2 del varco BB: muro) | 7D | 12 |
| BD | `#` | muro | dungeon entrance: frame |  | 01 | 12 |
| BE | `E` | scale | stairs down | stairs_down | 00 | 43 |
| BF | `E` | scale | hidden stairs down (appear after an event) | stairs_down **[hidden_stairs]** | 00 | 6 |
| C0 | `#` | muro | one-eyed statue | statue | 01 | 252 |
| C1 | `.` | pavimento | exit doorway to outside, bottom wall (half 1) | exit_door, door_half1 (varco) (meta' 1 del varco, coppia con C2) | 7C | 72 |
| C2 | `#` | muro | exit doorway to outside, bottom wall (half 2) | exit_door, door_half2 (meta' 2 del varco C1: muro) | 7D | 72 |
| C5 | `#` | muro | furniture (bed) | furniture | 01 | 29 |
| C6 | `#` | muro | furniture (bed) | furniture | 01 | 29 |
| C7 | `#` | muro | wall with ornament (top) |  | D3 | 235 |
| C8 | `#` | muro | wall with ornament (bottom) |  | D2 | 90 |
| C9 | `#` | muro | wall with ornament (left) |  | D0 | 65 |
| CA | `#` | muro | wall with ornament (right) |  | D1 | 52 |
| CB | `E` | scale | stairs up | stairs_up | 08 | 44 |
| CD | `#` | muro | minigame counter (end) | counter | 7E | 9 |
| CE | `#` | muro | statue / counter decoration | statue | 01 | 39 |
| CF | `.` | pavimento | conveyor belt (down) | conveyor **[conveyor]** | F0 | 28 |
| D0 | `.` | pavimento | conveyor belt (up) | conveyor **[conveyor]** | F1 | 28 |
| D1 | `.` | pavimento | conveyor belt (right) | conveyor **[conveyor]** | F2 | 37 |
| D2 | `.` | pavimento | conveyor belt (left) | conveyor **[conveyor]** | F3 | 40 |
| D3 | `#` | muro | minigame counter (border) | counter | 7F | 7 |
| D4 | `~` | acqua | spikes | spikes **[spikes]** | E0 | 50 |
| DA | `.` | pavimento | floor (studded tiles) |  | 00 | 48 |
| DB | `.` | pavimento | switch block (lowered) | switch_block **[switch_block]** | 04 | 225 |
| DC | `#` | muro | switch block (raised) | switch_block **[switch_block]** | 04 | 226 |
| DD | `B` | blocco | crystal (breakable with sword) | removable | 30 | 60 |
| DE | `D` | porta chiusa | keyhole block (opens with small key) | keyhole_block | 01 | 17 |
| DF | `.` | pavimento | floor (cracked/textured) |  | 00 | 1195 |
| E7 | `.` | pavimento | floor art (Wind Fish's Egg) |  | 00 | 1 |
| E8 | `.` | pavimento | floor art (Wind Fish's Egg) |  | 00 | 1 |
| E9 | `.` | pavimento | floor art (Wind Fish's Egg) |  | 00 | 1 |
| EA | `.` | pavimento | floor art (Wind Fish's Egg) |  | 00 | 1 |

## Color Dungeon: oggetti con significato diverso

| Id | Simbolo | Categoria | Nome | Tag / speciale | Physics | Celle nel gioco |
|---|---|---|---|---|---|---|
| 50 | `.` | pavimento | color tile (changes color when stepped on) | color_tile **[color_tile]** |  |  |
| 51 | `.` | pavimento | color tile (changes color when stepped on) | color_tile **[color_tile]** |  |  |
| 52 | `.` | pavimento | color tile (changes color when stepped on) | color_tile **[color_tile]** |  |  |
| 53 | `.` | pavimento | color tile (changes color when stepped on) | color_tile **[color_tile]** |  |  |
| 54 | `.` | pavimento | color tile (changes color when stepped on) | color_tile **[color_tile]** |  |  |
| 55 | `.` | pavimento | color tile (changes color when stepped on) | color_tile **[color_tile]** |  |  |
| 56 | `.` | pavimento | color tile (changes color when stepped on) | color_tile **[color_tile]** |  |  |
| 57 | `.` | pavimento | color tile (changes color when stepped on) | color_tile **[color_tile]** |  |  |
| 58 | `.` | pavimento | floor art (Color Dungeon) |  |  |  |
| 59 | `.` | pavimento | floor art (Color Dungeon) |  |  |  |
| 5A | `~` | acqua | floor art (Color Dungeon) | pit |  |  |
| 5B | `.` | pavimento | floor art (Color Dungeon) |  |  |  |
| 5C | `.` | pavimento | floor art (Color Dungeon) |  |  |  |
| 5D | `.` | pavimento | floor art (Color Dungeon) |  |  |  |
| 5E | `.` | pavimento | floor art (Color Dungeon) |  |  |  |
| 5F | `~` | acqua | floor art (Color Dungeon) | pit |  |  |
| 60 | `.` | pavimento | floor art (Color Dungeon) |  |  |  |
| 61 | `.` | pavimento | floor art (Color Dungeon) |  |  |  |
| 62 | `.` | pavimento | floor art (Color Dungeon) |  |  |  |
| 63 | `.` | pavimento | floor art (Color Dungeon) |  |  |  |
| 64 | `~` | acqua | floor art (Color Dungeon) | pit |  |  |
| 65 | `.` | pavimento | floor art (Color Dungeon) |  |  |  |
| 66 | `.` | pavimento | floor art (Color Dungeon) |  |  |  |

## Entita'

Solo le entita' presenti nelle stanze del gioco (le altre sono in `mappings/entities.json`).

| Id | Simbolo | Classe | Nome | Speciale | Occorrenze |
|---|---|---|---|---|---|
| 09 | `M` | enemy | OCTOROCK |  | 19 |
| 0B | `M` | enemy | MOBLIN |  | 72 |
| 0D | `M` | enemy | TEKTITE |  | 19 |
| 0E | `M` | enemy | LEEVER |  | 18 |
| 0F | `M` | enemy | ARMOS_STATUE |  | 21 |
| 10 | `M` | enemy | HIDING_GHINI |  | 11 |
| 11 | `M` | enemy | GIANT_GHINI |  | 1 |
| 12 | `M` | enemy | GHINI |  | 4 |
| 14 | `M` | enemy | MOBLIN_SWORD |  | 21 |
| 15 | `M` | enemy | ANTI_FAIRY |  | 13 |
| 16 | `M` | enemy | SPARK_COUNTER_CLOCKWISE |  | 31 |
| 17 | `M` | enemy | SPARK_CLOCKWISE |  | 25 |
| 18 | `M` | enemy | POLS_VOICE |  | 6 |
| 19 | `M` | enemy | KEESE |  | 81 |
| 1A | `M` | enemy | STALFOS_AGGRESSIVE |  | 12 |
| 1B | `M` | enemy | GEL |  | 42 |
| 1C | `M` | enemy | MINI_GEL |  | 12 |
| 1E | `M` | enemy | STALFOS_EVASIVE |  | 15 |
| 1F | `M` | enemy | GIBDO |  | 5 |
| 20 | `M` | enemy | HARDHAT_BEETLE |  | 14 |
| 21 | `M` | enemy | WIZROBE |  | 18 |
| 23 | `M` | enemy | LIKE_LIKE |  | 14 |
| 24 | `M` | enemy | IRON_MASK |  | 16 |
| 27 | `M` | enemy | SPIKE_TRAP |  | 36 |
| 28 | `M` | enemy | MIMIC |  | 18 |
| 29 | `M` | enemy | MINI_MOLDORM |  | 9 |
| 2A | `M` | enemy | LASER |  | 10 |
| 2C | `M` | enemy | SPIKED_BEETLE |  | 10 |
| 2D | - | item | DROPPABLE_HEART |  | 53 |
| 2E | - | item | DROPPABLE_RUPEE |  | 17 |
| 2F | - | item | DROPPABLE_FAIRY |  | 14 |
| 30 | - | key_source | KEY_DROP_POINT |  | 3 |
| 31 | - | item | SWORD |  | 1 |
| 35 | - | item | HEART_PIECE |  | 9 |
| 37 | - | item | DROPPABLE_ARROWS |  | 8 |
| 38 | - | item | DROPPABLE_BOMBS |  | 17 |
| 39 | - | item | INSTRUMENT_OF_THE_SIRENS |  | 8 |
| 3A | - | item | SLEEPY_TOADSTOOL |  | 1 |
| 3B | - | item | DROPPABLE_MAGIC_POWDER |  | 4 |
| 3C | - | key_source | HIDING_SLIME_KEY |  | 1 |
| 3D | - | item | DROPPABLE_SECRET_SEASHELL |  | 16 |
| 3E | - | npc | MARIN |  | 3 |
| 3F | - | npc | RACOON |  | 2 |
| 40 | - | npc | WITCH |  | 1 |
| 41 | - | event | OWL_EVENT |  | 15 |
| 42 | `#` | solid_object | OWL_STATUE |  | 25 |
| 43 | - | mechanism | SEASHELL_MANSION_TREES |  | 2 |
| 44 | - | npc | YARNA_TALKING_BONES |  | 2 |
| 45 | `M` | enemy | BOULDERS |  | 2 |
| 46 | - | mechanism | MOVING_BLOCK_LEFT_TOP | moving_block | 2 |
| 47 | - | mechanism | MOVING_BLOCK_LEFT_BOTTOM | moving_block | 2 |
| 48 | - | mechanism | MOVING_BLOCK_BOTTOM_LEFT | moving_block | 1 |
| 49 | - | mechanism | MOVING_BLOCK_BOTTOM_RIGHT | moving_block | 1 |
| 4A | - | mechanism | COLOR_DUNGEON_BOOK |  | 1 |
| 4D | - | npc | SHOP_OWNER |  | 1 |
| 4F | - | npc | TRENDY_GAME_OWNER |  | 1 |
| 50 | `M` | enemy | BOO_BUDDY |  | 2 |
| 51 | - | npc | KNIGHT |  | 1 |
| 52 | - | mechanism | TRACTOR_DEVICE | tractor_device | 3 |
| 53 | - | mechanism | TRACTOR_DEVICE_REVERSE | tractor_device | 1 |
| 54 | - | npc | FISHERMAN_FISHING_GAME |  | 2 |
| 55 | `M` | enemy | BOUNCING_BOMBITE |  | 7 |
| 56 | `M` | enemy | TIMER_BOMBITE |  | 3 |
| 57 | `M` | enemy | PAIRODD |  | 9 |
| 59 | `M` | boss | MOLDORM |  | 1 |
| 5A | `M` | boss | FACADE |  | 1 |
| 5B | `M` | boss | SLIME_EYE |  | 1 |
| 5C | `M` | boss | GENIE |  | 1 |
| 5D | `M` | boss | SLIME_EEL |  | 1 |
| 5E | `M` | miniboss | GHOMA |  | 2 |
| 5F | `M` | miniboss | MASTER_STALFOS |  | 4 |
| 60 | `M` | miniboss | DODONGO_SNAKE |  | 6 |
| 61 | - | mechanism | WARP | teleport | 21 |
| 62 | `M` | boss | HOT_HEAD |  | 1 |
| 63 | `M` | boss | EVIL_EAGLE |  | 1 |
| 65 | `M` | boss | ANGLER_FISH |  | 1 |
| 66 | - | mechanism | CRYSTAL_SWITCH | switch | 18 |
| 69 | - | mechanism | MOVING_BLOCK_MOVER | moving_block | 2 |
| 6A | - | npc | RAFT_RAFT_OWNER |  | 2 |
| 6C | - | npc | CUCCO |  | 8 |
| 6D | - | npc | BOW_WOW |  | 2 |
| 6E | - | npc | BUTTERFLY |  | 39 |
| 6F | - | npc | DOG |  | 3 |
| 70 | - | npc | KID_70 |  | 1 |
| 71 | - | npc | KID_71 |  | 1 |
| 72 | - | npc | KID_72 |  | 1 |
| 73 | - | npc | KID_73 |  | 2 |
| 74 | - | npc | PAPAHLS_WIFE |  | 1 |
| 75 | - | npc | GRANDMA_ULRIRA |  | 2 |
| 76 | - | npc | MR_WRITE |  | 2 |
| 77 | - | npc | GRANDPA_ULRIRA |  | 1 |
| 78 | - | npc | YIP_YIP |  | 2 |
| 79 | - | npc | MADAM_MEOWMEOW |  | 1 |
| 7A | `M` | enemy | CROW |  | 13 |
| 7B | - | npc | CRAZY_TRACY |  | 1 |
| 7C | `M` | enemy | GIANT_GOPONGA_FLOWER |  | 2 |
| 7E | `M` | enemy | GOPONGA_FLOWER |  | 8 |
| 7F | `M` | miniboss | TURTLE_ROCK_HEAD |  | 1 |
| 80 | `#` | solid_object | TELEPHONE |  | 9 |
| 81 | `M` | miniboss | ROLLING_BONES |  | 2 |
| 82 | - | enemy_part | ROLLING_BONES_BAR |  | 2 |
| 83 | `#` | solid_object | DREAM_SHRINE_BED |  | 1 |
| 84 | - | npc | BIG_FAIRY |  | 5 |
| 85 | - | npc | MR_WRITES_BIRD |  | 2 |
| 86 | - | item | FLOATING_ITEM |  | 47 |
| 87 | `M` | miniboss | DESERT_LANMOLA |  | 1 |
| 88 | `M` | miniboss | ARMOS_KNIGHT |  | 1 |
| 89 | `M` | miniboss | HINOX |  | 3 |
| 8A | - | mechanism | TILE_GLINT_SHOWN |  | 1 |
| 8B | - | mechanism | TILE_GLINT_HIDDEN |  | 1 |
| 8E | `M` | miniboss | CUE_BALL |  | 2 |
| 8F | `M` | enemy | MASKED_MIMIC_GORIYA |  | 5 |
| 90 | `M` | enemy | THREE_OF_A_KIND |  | 9 |
| 91 | `M` | enemy | ANTI_KIRBY |  | 2 |
| 92 | `M` | miniboss | SMASHER |  | 2 |
| 93 | `M` | enemy | MAD_BOMBER |  | 1 |
| 94 | - | mechanism | KANALET_BOMBABLE_WALL |  | 2 |
| 95 | - | npc | RICHARD |  | 1 |
| 96 | - | npc | RICHARD_FROG |  | 4 |
| 97 | - | mechanism | DIVE_SPOT |  | 3 |
| 98 | `B` | liftable_object | HORSE_PIECE |  | 10 |
| 99 | `M` | enemy | WATER_TEKTITE |  | 34 |
| 9A | `M` | enemy | FLYING_TILES |  | 3 |
| 9B | `M` | enemy | HIDING_GEL |  | 172 |
| 9C | `M` | enemy | STAR |  | 14 |
| 9D | `B` | liftable_object | LIFTABLE_STATUE |  | 15 |
| 9E | `M` | enemy | FIREBALL_SHOOTER |  | 21 |
| 9F | `M` | enemy | GOOMBA |  | 33 |
| A0 | `M` | enemy | PEAHAT |  | 22 |
| A1 | `M` | enemy | SNAKE |  | 15 |
| A2 | `M` | enemy | PIRANHA_PLANT |  | 4 |
| A3 | - | sidescroll | SIDE_VIEW_PLATFORM_HORIZONTAL |  | 4 |
| A4 | - | sidescroll | SIDE_VIEW_PLATFORM_VERTICAL |  | 4 |
| A5 | - | sidescroll | SIDE_VIEW_PLATFORM |  | 2 |
| A6 | - | sidescroll | SIDE_VIEW_WEIGHTS |  | 6 |
| A7 | `#` | solid_object | SMASHABLE_PILLAR |  | 4 |
| A9 | `M` | enemy | BLOOPER |  | 4 |
| AA | `M` | enemy | CHEEP_CHEEP_HORIZONTAL |  | 2 |
| AB | `M` | enemy | CHEEP_CHEEP_VERTICAL |  | 2 |
| AC | `M` | enemy | CHEEP_CHEEP_JUMPING |  | 4 |
| AD | - | npc | KIKI_THE_MONKEY |  | 1 |
| AE | `M` | enemy | WINGED_OCTOROK |  | 13 |
| AF | - | item | TRADING_ITEM |  | 2 |
| B0 | `M` | enemy | PINCER |  | 10 |
| B1 | - | mechanism | HOLE_FILLER |  | 4 |
| B2 | `M` | enemy | BEETLE_SPAWNER |  | 1 |
| B3 | - | npc | HONEYCOMB |  | 1 |
| B4 | - | npc | TARIN |  | 1 |
| B5 | - | npc | BEAR |  | 1 |
| B6 | - | npc | PAPAHL |  | 2 |
| B7 | - | npc | MERMAID |  | 1 |
| B8 | - | npc | FISHERMAN_UNDER_BRIDGE |  | 1 |
| B9 | `M` | enemy | BUZZ_BLOB |  | 13 |
| BA | `M` | enemy | BOMBER |  | 14 |
| BB | `M` | enemy | BUSH_CRAWLER |  | 18 |
| BC | `M` | miniboss | GRIM_CREEPER |  | 1 |
| BD | `M` | enemy | VIRE |  | 4 |
| BE | `M` | miniboss | BLAINO |  | 1 |
| BF | `M` | enemy | ZOMBIE |  | 3 |
| C0 | `#` | solid_object | MAZE_SIGNPOST |  | 5 |
| C1 | - | npc | MARIN_AT_THE_SHORE |  | 1 |
| C2 | - | npc | MARIN_AT_TAL_TAL_HEIGHTS |  | 1 |
| C3 | - | npc | MAMU_AND_FROGS |  | 3 |
| C4 | - | npc | WALRUS |  | 1 |
| C5 | `M` | enemy | URCHIN |  | 6 |
| C6 | `M` | enemy | SAND_CRAB |  | 3 |
| C7 | - | npc | MANBO_AND_FISHES |  | 3 |
| CA | - | npc | MAD_BATTER |  | 3 |
| CB | `M` | enemy | ZORA |  | 13 |
| CC | `M` | enemy | FISH |  | 16 |
| CD | - | npc | BANANAS_SCHULE_SALE |  | 6 |
| CE | `#` | solid_object | MERMAID_STATUE |  | 1 |
| CF | - | npc | SEASHELL_MANSION |  | 1 |
| D0 | - | npc | ANIMAL_D0 |  | 3 |
| D1 | - | npc | ANIMAL_D1 |  | 1 |
| D2 | - | npc | ANIMAL_D2 |  | 1 |
| D3 | - | npc | BUNNY_D3 |  | 4 |
| D6 | - | sidescroll | SIDE_VIEW_POT |  | 3 |
| D7 | `M` | enemy | THWIMP |  | 7 |
| D8 | `M` | enemy | THWOMP |  | 2 |
| D9 | `M` | enemy | THWOMP_RAMMABLE |  | 1 |
| DA | `M` | enemy | PODOBOO |  | 11 |
| DB | `M` | enemy | GIANT_BUBBLE |  | 2 |
| DC | - | event | FLYING_ROOSTER_EVENTS |  | 3 |
| DD | - | mechanism | BOOK |  | 8 |
| DE | - | event | EGG_SONG_EVENT |  | 1 |
| E0 | - | npc | MONKEY |  | 1 |
| E1 | - | npc | WITCH_RAT |  | 3 |
| E2 | `M` | enemy | FLAME_SHOOTER |  | 1 |
| E3 | `M` | enemy | POKEY |  | 4 |
| E4 | `M` | miniboss | MOBLIN_KING |  | 1 |
| E5 | - | item | FLOATING_ITEM_2 |  | 38 |
| E6 | `M` | boss | FINAL_NIGHTMARE |  | 1 |
| E7 | - | mechanism | KANALET_CASTLE_GATE_SWITCH | switch | 1 |
| E9 | `B` | liftable_object | COLOR_SHELL_RED |  | 2 |
| EA | `B` | liftable_object | COLOR_SHELL_GREEN |  | 3 |
| EB | `B` | liftable_object | COLOR_SHELL_BLUE |  | 1 |
| EC | `M` | enemy | COLOR_GHOUL_RED |  | 4 |
| ED | `M` | enemy | COLOR_GHOUL_GREEN |  | 5 |
| EE | `M` | enemy | COLOR_GHOUL_BLUE |  | 1 |
| EF | - | mechanism | ROTOSWITCH_RED | switch | 7 |
| F0 | - | mechanism | ROTOSWITCH_YELLOW | switch | 1 |
| F1 | - | mechanism | ROTOSWITCH_BLUE | switch | 9 |
| F2 | `M` | enemy | FLYING_HOPPER_BOMBS |  | 4 |
| F3 | `M` | enemy | HOPPER |  | 3 |
| F4 | `M` | miniboss | AVALAUNCH |  | 1 |
| F6 | `M` | boss | COLOR_GUARDIAN_BLUE |  | 1 |
| F7 | `M` | boss | COLOR_GUARDIAN_RED |  | 1 |
| F8 | `M` | miniboss | GIANT_BUZZ_BLOB |  | 1 |
| F9 | `M` | enemy | HARDHIT_BEETLE |  | 1 |
| FA | - | npc | PHOTOGRAPHER |  | 5 |
