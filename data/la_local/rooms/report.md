# Report estrazione stanze - Link's Awakening DX (U) v1.0

- Stanze estratte: **789**
- Valide: **605**
- Scartate: **184** (una stanza puo' avere piu' motivi)
- Valide che rispettano anche tutte le regole del brief (scale, bordi chiusi, max 2 porte): **8**

La griglia e' fedele 1:1 al gioco: le scale non vengono inventate e i bordi non vengono chiusi.
Le regole del brief sono solo verificate (`brief_checks` in ogni room.json).

## Regole del brief non rispettate (stanze valide)

| Regola | Stanze |
|---|---|
| `border_closed` | 595 |
| `stairs_reachable` | 443 |
| `has_stairs` | 430 |
| `max_doors_ok` | 1 |

## Motivi di scarto

| Motivo | Stanze | Significato |
|---|---|---|
| `sidescroll` | 56 | stanza a scorrimento laterale (2D), non rappresentabile dall'alto |
| `special:switch_block` | 47 | tile/entita' speciale con politica 'discard' (vedi mappings/categories.json) |
| `special:switch` | 29 | tile/entita' speciale con politica 'discard' (vedi mappings/categories.json) |
| `special:teleport` | 21 | tile/entita' speciale con politica 'discard' (vedi mappings/categories.json) |
| `no_floor_for_player` | 19 | nessuna cella di pavimento dove mettere il giocatore (es. schermate d'acqua) |
| `empty_room` | 10 | stanza vuota/non usata (nessun oggetto, entita' o warp) |
| `special:color_tile` | 8 | tile/entita' speciale con politica 'discard' (vedi mappings/categories.json) |
| `special:conveyor` | 7 | tile/entita' speciale con politica 'discard' (vedi mappings/categories.json) |
| `special:tractor_device` | 4 | tile/entita' speciale con politica 'discard' (vedi mappings/categories.json) |
| `special:moving_block` | 2 | tile/entita' speciale con politica 'discard' (vedi mappings/categories.json) |
| `special:quicksand` | 1 | tile/entita' speciale con politica 'discard' (vedi mappings/categories.json) |

## Segnalazioni (stanze comunque valide)

| Segnalazione | Stanze |
|---|---|
| `special:spikes` | 8 |
| `special:hidden_stairs` | 6 |
| `special:keyhole` | 5 |

## Correzioni applicate

| Correzione | Stanze |
|---|---|
| `add_player` | 770 |

## Per gruppo

| Gruppo | Stanze | Valide |
|---|---|---|
| dungeons/D0_color_dungeon | 22 | 10 |
| dungeons/D1_tail_cave | 29 | 22 |
| dungeons/D2_bottle_grotto | 33 | 16 |
| dungeons/D3_key_cavern | 31 | 19 |
| dungeons/D4_anglers_tunnel | 38 | 24 |
| dungeons/D5_catfishs_maw | 45 | 31 |
| dungeons/D6_face_shrine | 49 | 24 |
| dungeons/D7_eagles_tower | 49 | 17 |
| dungeons/D8_turtle_rock | 60 | 40 |
| dungeons/D9_windfishs_egg | 7 | 7 |
| indoor/bowwow_hideout | 4 | 4 |
| indoor/cave_b | 63 | 61 |
| indoor/cave_c | 18 | 16 |
| indoor/cave_water | 28 | 24 |
| indoor/doghouse | 1 | 1 |
| indoor/dream_shrine | 5 | 5 |
| indoor/ghost_house | 1 | 1 |
| indoor/house | 27 | 26 |
| indoor/kanalet | 10 | 9 |
| indoor/library | 1 | 1 |
| indoor/minigame | 3 | 0 |
| indoor/s_face_shrine | 6 | 6 |
| indoor/shop | 3 | 3 |
| overworld | 256 | 238 |

## Stanze scartate

| Stanza | Gruppo | Motivi |
|---|---|---|
| 001 | overworld | special:teleport |
| 02C | overworld | special:teleport |
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
| 095 | overworld | special:teleport |
| 0CE | overworld | special:quicksand, special:teleport |
| 0D9 | overworld | no_floor_for_player |
| 0EC | overworld | special:teleport |
| 100 | dungeons/D6_face_shrine | empty_room |
| 111 | dungeons/D1_tail_cave | special:teleport |
| 113 | dungeons/D1_tail_cave | special:switch |
| 117 | dungeons/D1_tail_cave | special:teleport |
| 118 | dungeons/D1_tail_cave | sidescroll |
| 119 | dungeons/D1_tail_cave | sidescroll |
| 11A | dungeons/D1_tail_cave | sidescroll |
| 11B | dungeons/D1_tail_cave | sidescroll |
| 11E | dungeons/D4_anglers_tunnel | sidescroll |
| 11F | dungeons/D4_anglers_tunnel | sidescroll |
| 122 | dungeons/D2_bottle_grotto | special:switch, special:switch_block |
| 123 | dungeons/D2_bottle_grotto | special:switch_block |
| 124 | dungeons/D2_bottle_grotto | special:switch |
| 126 | dungeons/D2_bottle_grotto | special:tractor_device |
| 128 | dungeons/D2_bottle_grotto | special:teleport |
| 132 | dungeons/D2_bottle_grotto | special:switch_block |
| 133 | dungeons/D2_bottle_grotto | special:switch, special:switch_block |
| 136 | dungeons/D2_bottle_grotto | special:teleport |
| 138 | dungeons/D2_bottle_grotto | special:switch, special:switch_block |
| 139 | dungeons/D2_bottle_grotto | special:switch, special:switch_block |
| 13A | dungeons/D2_bottle_grotto | sidescroll |
| 13B | dungeons/D2_bottle_grotto | sidescroll |
| 13C | dungeons/D2_bottle_grotto | sidescroll |
| 13D | dungeons/D2_bottle_grotto | sidescroll |
| 13E | dungeons/D2_bottle_grotto | sidescroll |
| 13F | dungeons/D2_bottle_grotto | sidescroll |
| 145 | dungeons/D3_key_cavern | special:teleport |
| 14C | dungeons/D3_key_cavern | special:switch_block |
| 150 | dungeons/D3_key_cavern | special:switch_block |
| 152 | dungeons/D3_key_cavern | special:teleport |
| 153 | dungeons/D3_key_cavern | special:tractor_device |
| 154 | dungeons/D3_key_cavern | special:switch |
| 155 | dungeons/D3_key_cavern | special:conveyor |
| 157 | dungeons/D3_key_cavern | special:conveyor |
| 158 | dungeons/D3_key_cavern | special:conveyor |
| 15B | dungeons/D3_key_cavern | special:conveyor |
| 15D | dungeons/D2_bottle_grotto | empty_room |
| 15E | dungeons/D4_anglers_tunnel | sidescroll |
| 15F | dungeons/D4_anglers_tunnel | sidescroll |
| 161 | dungeons/D4_anglers_tunnel | special:moving_block |
| 164 | dungeons/D4_anglers_tunnel | special:teleport |
| 173 | dungeons/D4_anglers_tunnel | special:switch |
| 17A | dungeons/D4_anglers_tunnel | special:teleport |
| 17C | dungeons/D4_anglers_tunnel | sidescroll |
| 17D | dungeons/D4_anglers_tunnel | sidescroll |
| 17E | dungeons/D4_anglers_tunnel | empty_room |
| 17F | dungeons/D4_anglers_tunnel | empty_room |
| 191 | dungeons/D5_catfishs_maw | special:switch |
| 193 | dungeons/D5_catfishs_maw | special:teleport |
| 1A1 | dungeons/D5_catfishs_maw | special:teleport |
| 1A2 | dungeons/D5_catfishs_maw | sidescroll |
| 1A3 | dungeons/D5_catfishs_maw | sidescroll, no_floor_for_player |
| 1A4 | dungeons/D5_catfishs_maw | sidescroll |
| 1A5 | dungeons/D5_catfishs_maw | sidescroll |
| 1A6 | dungeons/D5_catfishs_maw | sidescroll |
| 1A7 | dungeons/D5_catfishs_maw | sidescroll |
| 1A8 | dungeons/D5_catfishs_maw | sidescroll |
| 1A9 | dungeons/D5_catfishs_maw | sidescroll |
| 1AA | dungeons/D3_key_cavern | sidescroll |
| 1AB | dungeons/D3_key_cavern | sidescroll |
| 1AD | dungeons/D5_catfishs_maw | empty_room |
| 1AE | dungeons/D5_catfishs_maw | empty_room |
| 1AF | dungeons/D5_catfishs_maw | empty_room |
| 1B0 | dungeons/D6_face_shrine | special:switch, special:switch_block |
| 1B1 | dungeons/D6_face_shrine | special:switch, special:switch_block |
| 1B2 | dungeons/D6_face_shrine | special:switch_block |
| 1B3 | dungeons/D6_face_shrine | special:switch |
| 1B4 | dungeons/D6_face_shrine | special:switch_block |
| 1B6 | dungeons/D6_face_shrine | special:switch |
| 1B8 | dungeons/D6_face_shrine | special:switch_block |
| 1C0 | dungeons/D6_face_shrine | special:switch, special:switch_block |
| 1C1 | dungeons/D6_face_shrine | special:switch, special:switch_block |
| 1C5 | dungeons/D6_face_shrine | special:teleport |
| 1C8 | dungeons/D6_face_shrine | special:switch, special:switch_block |
| 1CA | dungeons/D6_face_shrine | special:tractor_device |
| 1D2 | dungeons/D6_face_shrine | special:switch_block |
| 1D4 | dungeons/D6_face_shrine | special:teleport |
| 1D5 | dungeons/D6_face_shrine | special:conveyor |
| 1D7 | dungeons/D6_face_shrine | special:switch_block |
| 1D8 | dungeons/D6_face_shrine | sidescroll |
| 1D9 | dungeons/D6_face_shrine | sidescroll |
| 1DA | dungeons/D6_face_shrine | sidescroll |
| 1DB | dungeons/D6_face_shrine | sidescroll |
| 1DC | dungeons/D6_face_shrine | sidescroll |
| 1DD | dungeons/D6_face_shrine | sidescroll |
| 1DE | dungeons/D6_face_shrine | empty_room |
| 1DF | dungeons/D6_face_shrine | empty_room |
| 1E6 | indoor/cave_water | no_floor_for_player |
| 1EB | indoor/cave_water | sidescroll |
| 1EC | indoor/cave_water | sidescroll |
| 1EF | dungeons/D4_anglers_tunnel | sidescroll |
| 1F2 | indoor/cave_water | no_floor_for_player |
| 1FF | dungeons/D4_anglers_tunnel | sidescroll, no_floor_for_player |
| 200 | indoor/cave_b | special:switch_block |
| 201 | dungeons/D7_eagles_tower | special:switch_block |
| 202 | dungeons/D7_eagles_tower | special:switch_block |
| 205 | dungeons/D7_eagles_tower | special:switch_block |
| 206 | dungeons/D7_eagles_tower | special:switch_block |
| 207 | dungeons/D7_eagles_tower | special:switch_block |
| 208 | dungeons/D7_eagles_tower | special:switch, special:switch_block |
| 209 | dungeons/D7_eagles_tower | special:switch_block |
| 20A | dungeons/D7_eagles_tower | special:switch_block |
| 20B | dungeons/D7_eagles_tower | special:switch_block |
| 20C | dungeons/D7_eagles_tower | special:switch_block |
| 20E | dungeons/D7_eagles_tower | special:teleport |
| 212 | dungeons/D7_eagles_tower | special:switch_block |
| 215 | dungeons/D7_eagles_tower | special:switch_block |
| 216 | dungeons/D7_eagles_tower | special:moving_block, special:switch_block |
| 219 | dungeons/D7_eagles_tower | special:switch_block |
| 21A | dungeons/D7_eagles_tower | special:switch, special:switch_block |
| 21D | dungeons/D7_eagles_tower | special:switch, special:switch_block |
| 21E | dungeons/D7_eagles_tower | special:switch_block |
| 220 | dungeons/D7_eagles_tower | special:conveyor |
| 221 | dungeons/D7_eagles_tower | special:switch_block |
| 222 | dungeons/D7_eagles_tower | special:switch_block |
| 224 | dungeons/D7_eagles_tower | special:switch |
| 225 | dungeons/D7_eagles_tower | special:switch_block |
| 226 | dungeons/D7_eagles_tower | special:switch_block |
| 228 | dungeons/D7_eagles_tower | special:teleport |
| 229 | dungeons/D7_eagles_tower | special:switch_block |
| 22A | dungeons/D7_eagles_tower | special:switch_block |
| 22B | dungeons/D7_eagles_tower | special:switch_block |
| 22D | dungeons/D7_eagles_tower | special:switch_block |
| 22F | dungeons/D7_eagles_tower | empty_room |
| 236 | dungeons/D8_turtle_rock | special:switch_block |
| 237 | dungeons/D8_turtle_rock | special:switch_block |
| 23F | dungeons/D8_turtle_rock | special:teleport |
| 252 | dungeons/D8_turtle_rock | special:switch |
| 253 | dungeons/D8_turtle_rock | special:switch |
| 258 | dungeons/D8_turtle_rock | special:switch |
| 25C | dungeons/D8_turtle_rock | special:tractor_device |
| 25D | dungeons/D8_turtle_rock | special:teleport |
| 260 | dungeons/D8_turtle_rock | sidescroll |
| 261 | dungeons/D8_turtle_rock | sidescroll |
| 262 | dungeons/D8_turtle_rock | sidescroll |
| 263 | dungeons/D8_turtle_rock | sidescroll |
| 264 | dungeons/D8_turtle_rock | sidescroll |
| 265 | dungeons/D8_turtle_rock | sidescroll |
| 266 | dungeons/D8_turtle_rock | sidescroll |
| 267 | dungeons/D8_turtle_rock | sidescroll |
| 268 | dungeons/D8_turtle_rock | sidescroll |
| 269 | dungeons/D8_turtle_rock | sidescroll |
| 26A | dungeons/D8_turtle_rock | sidescroll |
| 26B | dungeons/D8_turtle_rock | sidescroll |
| 2A0 | indoor/minigame | special:conveyor |
| 2B1 | indoor/minigame | sidescroll |
| 2C0 | indoor/cave_c | sidescroll, no_floor_for_player |
| 2C1 | indoor/cave_c | sidescroll, no_floor_for_player |
| 2C3 | indoor/kanalet | special:switch |
| 2E8 | dungeons/D7_eagles_tower | sidescroll |
| 2E9 | indoor/house | sidescroll |
| 2F5 | indoor/minigame | sidescroll |
| 2F8 | dungeons/D7_eagles_tower | sidescroll |
| 2FD | indoor/cave_b | sidescroll |
| 304 | dungeons/D0_color_dungeon | special:switch, special:switch_block |
| 308 | dungeons/D0_color_dungeon | special:switch |
| 309 | dungeons/D0_color_dungeon | special:color_tile |
| 30A | dungeons/D0_color_dungeon | special:switch |
| 30B | dungeons/D0_color_dungeon | special:color_tile, special:switch |
| 30D | dungeons/D0_color_dungeon | special:color_tile |
| 30E | dungeons/D0_color_dungeon | special:color_tile |
| 30F | dungeons/D0_color_dungeon | special:switch |
| 310 | dungeons/D0_color_dungeon | special:color_tile |
| 313 | dungeons/D0_color_dungeon | special:color_tile |
| 314 | dungeons/D0_color_dungeon | special:color_tile |
| 315 | dungeons/D0_color_dungeon | special:color_tile |
