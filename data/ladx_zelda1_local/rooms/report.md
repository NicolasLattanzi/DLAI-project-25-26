# Report estrazione stanze - Link's Awakening DX (U) v1.0

- Stanze estratte: **789**
- Valide: **622**
- Scartate: **167** (una stanza puo' avere piu' motivi)
- Valide che rispettano anche tutte le regole del brief (scale, bordi chiusi, max 2 porte): **7**

La griglia e' fedele 1:1 al gioco: le scale non vengono inventate e i bordi non vengono chiusi.
Le regole del brief sono solo verificate (`brief_checks` in ogni room.json).

## Regole del brief non rispettate (stanze valide)

| Regola | Stanze |
|---|---|
| `border_closed` | 611 |
| `stairs_reachable` | 486 |
| `has_stairs` | 475 |
| `max_doors_ok` | 2 |

## Motivi di scarto

| Motivo | Stanze | Significato |
|---|---|---|
| `sidescroll` | 56 | stanza a scorrimento laterale (2D), non rappresentabile dall'alto |
| `special:unmapped` | 25 | oggetti non presenti nelle tabelle di mapping |
| `no_floor_for_player` | 22 | nessuna cella di pavimento dove mettere il giocatore (es. schermate d'acqua) |
| `special:teleport` | 19 | tile/entita' speciale con politica 'discard' (vedi mappings/categories.json) |
| `special:switch` | 18 | tile/entita' speciale con politica 'discard' (vedi mappings/categories.json) |
| `special:switch_block` | 12 | tile/entita' speciale con politica 'discard' (vedi mappings/categories.json) |
| `empty_room` | 11 | stanza vuota/non usata (nessun oggetto, entita' o warp) |
| `special:color_tile` | 10 | tile/entita' speciale con politica 'discard' (vedi mappings/categories.json) |
| `special:conveyor` | 6 | tile/entita' speciale con politica 'discard' (vedi mappings/categories.json) |
| `special:tractor_device` | 3 | tile/entita' speciale con politica 'discard' (vedi mappings/categories.json) |
| `special:moving_block` | 1 | tile/entita' speciale con politica 'discard' (vedi mappings/categories.json) |

## Segnalazioni (stanze comunque valide)

| Segnalazione | Stanze |
|---|---|
| `special:hidden_stairs` | 5 |
| `special:keyhole` | 3 |
| `special:spikes` | 3 |

## Correzioni applicate

| Correzione | Stanze |
|---|---|
| `add_player` | 767 |

## Per gruppo

| Gruppo | Stanze | Valide |
|---|---|---|
| dungeons/Z1_D0_color | 22 | 9 |
| dungeons/Z1_D1 | 29 | 23 |
| dungeons/Z1_D2 | 33 | 22 |
| dungeons/Z1_D3 | 33 | 23 |
| dungeons/Z1_D4 | 36 | 25 |
| dungeons/Z1_D5 | 45 | 30 |
| dungeons/Z1_D6 | 49 | 33 |
| dungeons/Z1_D7 | 49 | 32 |
| dungeons/Z1_D8 | 55 | 35 |
| dungeons/Z1_D9 | 12 | 11 |
| indoor/bowwow_hideout | 4 | 4 |
| indoor/cave_b | 63 | 61 |
| indoor/cave_c | 18 | 16 |
| indoor/cave_water | 28 | 24 |
| indoor/doghouse | 1 | 1 |
| indoor/dream_shrine | 5 | 5 |
| indoor/ghost_house | 1 | 1 |
| indoor/house | 24 | 23 |
| indoor/kanalet | 10 | 9 |
| indoor/library | 1 | 1 |
| indoor/minigame | 3 | 0 |
| indoor/s_face_shrine | 6 | 6 |
| indoor/shop | 6 | 6 |
| overworld | 256 | 222 |

## Stanze scartate

| Stanza | Gruppo | Motivi |
|---|---|---|
| 00C | overworld | special:unmapped |
| 01A | overworld | special:unmapped |
| 01B | overworld | special:unmapped |
| 028 | overworld | special:unmapped |
| 038 | overworld | special:unmapped |
| 04C | overworld | no_floor_for_player |
| 04D | overworld | no_floor_for_player |
| 04E | overworld | no_floor_for_player |
| 04F | overworld | no_floor_for_player |
| 05F | overworld | no_floor_for_player |
| 06D | overworld | no_floor_for_player |
| 06E | overworld | no_floor_for_player |
| 06F | overworld | no_floor_for_player |
| 07C | overworld | no_floor_for_player |
| 07D | overworld | no_floor_for_player |
| 07E | overworld | no_floor_for_player |
| 07F | overworld | no_floor_for_player |
| 080 | overworld | special:unmapped |
| 084 | overworld | special:unmapped |
| 08B | overworld | special:unmapped |
| 08C | overworld | special:unmapped |
| 08D | overworld | special:unmapped |
| 08F | overworld | special:unmapped |
| 092 | overworld | special:unmapped |
| 095 | overworld | special:unmapped |
| 097 | overworld | special:unmapped |
| 09A | overworld | special:unmapped |
| 09D | overworld | special:unmapped, special:teleport |
| 0A3 | overworld | special:teleport |
| 0BC | overworld | special:unmapped |
| 0C5 | overworld | no_floor_for_player |
| 0C9 | overworld | special:teleport |
| 0F0 | overworld | special:unmapped |
| 0F9 | overworld | special:teleport |
| 100 | dungeons/Z1_D6 | empty_room |
| 111 | dungeons/Z1_D1 | special:teleport |
| 117 | dungeons/Z1_D1 | special:teleport |
| 118 | dungeons/Z1_D1 | sidescroll |
| 119 | dungeons/Z1_D1 | sidescroll |
| 11A | dungeons/Z1_D1 | sidescroll |
| 11B | dungeons/Z1_D1 | sidescroll |
| 11E | dungeons/Z1_D4 | sidescroll |
| 11F | dungeons/Z1_D4 | sidescroll |
| 124 | dungeons/Z1_D2 | special:switch |
| 126 | dungeons/Z1_D2 | special:tractor_device |
| 128 | dungeons/Z1_D2 | special:teleport |
| 136 | dungeons/Z1_D2 | special:teleport |
| 13A | dungeons/Z1_D2 | sidescroll |
| 13B | dungeons/Z1_D2 | sidescroll |
| 13C | dungeons/Z1_D2 | sidescroll |
| 13D | dungeons/Z1_D2 | sidescroll |
| 13E | dungeons/Z1_D2 | sidescroll |
| 13F | dungeons/Z1_D2 | sidescroll |
| 152 | dungeons/Z1_D3 | special:teleport |
| 154 | dungeons/Z1_D3 | special:switch |
| 155 | dungeons/Z1_D3 | special:conveyor |
| 157 | dungeons/Z1_D3 | special:conveyor |
| 158 | dungeons/Z1_D3 | special:conveyor |
| 15B | dungeons/Z1_D3 | special:conveyor |
| 15D | dungeons/Z1_D2 | empty_room |
| 15E | dungeons/Z1_D4 | sidescroll |
| 15F | dungeons/Z1_D4 | sidescroll |
| 170 | dungeons/Z1_D4 | special:teleport |
| 173 | dungeons/Z1_D4 | special:switch |
| 17A | dungeons/Z1_D4 | special:teleport |
| 17C | dungeons/Z1_D4 | sidescroll |
| 17D | dungeons/Z1_D4 | sidescroll |
| 17E | dungeons/Z1_D4 | empty_room |
| 17F | dungeons/Z1_D4 | empty_room |
| 191 | dungeons/Z1_D5 | special:switch |
| 19A | dungeons/Z1_D5 | special:teleport |
| 19D | dungeons/Z1_D5 | special:unmapped |
| 1A1 | dungeons/Z1_D5 | special:teleport |
| 1A2 | dungeons/Z1_D5 | sidescroll |
| 1A3 | dungeons/Z1_D5 | sidescroll, no_floor_for_player |
| 1A4 | dungeons/Z1_D5 | sidescroll |
| 1A5 | dungeons/Z1_D5 | sidescroll |
| 1A6 | dungeons/Z1_D5 | sidescroll |
| 1A7 | dungeons/Z1_D5 | sidescroll |
| 1A8 | dungeons/Z1_D5 | sidescroll |
| 1A9 | dungeons/Z1_D5 | sidescroll |
| 1AA | dungeons/Z1_D3 | sidescroll |
| 1AB | dungeons/Z1_D3 | sidescroll |
| 1AD | dungeons/Z1_D5 | empty_room |
| 1AE | dungeons/Z1_D5 | empty_room |
| 1AF | dungeons/Z1_D5 | empty_room |
| 1C0 | dungeons/Z1_D6 | special:switch, special:switch_block |
| 1C1 | dungeons/Z1_D6 | special:switch, special:switch_block |
| 1C5 | dungeons/Z1_D6 | special:teleport |
| 1CA | dungeons/Z1_D6 | special:tractor_device |
| 1D2 | dungeons/Z1_D6 | special:switch_block |
| 1D4 | dungeons/Z1_D6 | special:teleport |
| 1D7 | dungeons/Z1_D6 | special:switch_block |
| 1D8 | dungeons/Z1_D6 | sidescroll |
| 1D9 | dungeons/Z1_D6 | sidescroll |
| 1DA | dungeons/Z1_D6 | sidescroll |
| 1DB | dungeons/Z1_D6 | sidescroll |
| 1DC | dungeons/Z1_D6 | sidescroll |
| 1DD | dungeons/Z1_D6 | sidescroll |
| 1DE | dungeons/Z1_D6 | empty_room |
| 1DF | dungeons/Z1_D6 | empty_room |
| 1E6 | indoor/cave_water | no_floor_for_player |
| 1EB | indoor/cave_water | sidescroll |
| 1EC | indoor/cave_water | sidescroll |
| 1EF | dungeons/Z1_D3 | sidescroll |
| 1F2 | indoor/cave_water | no_floor_for_player |
| 1FF | dungeons/Z1_D3 | sidescroll, no_floor_for_player |
| 200 | indoor/cave_b | special:switch_block |
| 203 | dungeons/Z1_D7 | special:unmapped |
| 20E | dungeons/Z1_D7 | special:teleport |
| 216 | dungeons/Z1_D7 | special:moving_block, special:switch_block |
| 219 | dungeons/Z1_D7 | sidescroll |
| 21D | dungeons/Z1_D7 | special:switch, special:switch_block |
| 21E | dungeons/Z1_D7 | special:unmapped |
| 21F | dungeons/Z1_D7 | no_floor_for_player |
| 220 | dungeons/Z1_D7 | special:conveyor |
| 221 | dungeons/Z1_D7 | special:unmapped |
| 222 | dungeons/Z1_D7 | no_floor_for_player |
| 223 | dungeons/Z1_D7 | no_floor_for_player |
| 224 | dungeons/Z1_D7 | special:switch |
| 22A | dungeons/Z1_D7 | special:teleport |
| 22B | dungeons/Z1_D7 | special:unmapped, special:tractor_device |
| 22F | dungeons/Z1_D7 | empty_room |
| 236 | dungeons/Z1_D8 | special:switch_block |
| 237 | dungeons/Z1_D8 | special:switch_block |
| 23E | dungeons/Z1_D8 | special:unmapped |
| 23F | dungeons/Z1_D8 | special:teleport |
| 253 | dungeons/Z1_D8 | special:switch |
| 254 | dungeons/Z1_D9 | empty_room |
| 257 | dungeons/Z1_D8 | special:switch |
| 258 | dungeons/Z1_D8 | special:switch |
| 25D | dungeons/Z1_D8 | special:teleport |
| 260 | dungeons/Z1_D8 | sidescroll |
| 261 | dungeons/Z1_D8 | sidescroll |
| 262 | dungeons/Z1_D8 | special:unmapped |
| 263 | dungeons/Z1_D8 | sidescroll |
| 264 | dungeons/Z1_D8 | sidescroll |
| 265 | dungeons/Z1_D8 | sidescroll |
| 266 | dungeons/Z1_D8 | sidescroll |
| 267 | dungeons/Z1_D8 | sidescroll |
| 268 | dungeons/Z1_D8 | sidescroll |
| 269 | dungeons/Z1_D8 | sidescroll |
| 26A | dungeons/Z1_D8 | sidescroll |
| 26B | dungeons/Z1_D8 | sidescroll |
| 2A0 | indoor/minigame | special:conveyor |
| 2B1 | indoor/minigame | sidescroll |
| 2C0 | indoor/cave_c | sidescroll, no_floor_for_player |
| 2C1 | indoor/cave_c | sidescroll, no_floor_for_player |
| 2C3 | indoor/kanalet | special:switch |
| 2E8 | dungeons/Z1_D7 | sidescroll |
| 2E9 | indoor/house | sidescroll |
| 2F5 | indoor/minigame | sidescroll |
| 2F8 | dungeons/Z1_D7 | sidescroll |
| 2FD | indoor/cave_b | sidescroll |
| 304 | dungeons/Z1_D0_color | special:switch, special:switch_block |
| 305 | dungeons/Z1_D0_color | special:color_tile |
| 308 | dungeons/Z1_D0_color | special:switch |
| 309 | dungeons/Z1_D0_color | special:color_tile |
| 30A | dungeons/Z1_D0_color | special:color_tile, special:switch, special:switch_block |
| 30B | dungeons/Z1_D0_color | special:color_tile, special:switch |
| 30C | dungeons/Z1_D0_color | special:switch, special:switch_block |
| 30D | dungeons/Z1_D0_color | special:color_tile |
| 30E | dungeons/Z1_D0_color | special:color_tile |
| 30F | dungeons/Z1_D0_color | special:color_tile, special:switch |
| 310 | dungeons/Z1_D0_color | special:color_tile |
| 313 | dungeons/Z1_D0_color | special:color_tile |
| 315 | dungeons/Z1_D0_color | special:color_tile |
