"""Regole di validita' LevelEdit su una griglia 8x10 fedele al gioco.

Il layout originale della stanza NON viene modificato: porte, varchi e corridoi restano come nel gioco
e le scale NON vengono inventate. L'unica aggiunta e' il giocatore (P), nel punto in cui il gioco fa
entrare Link nella stanza (arrivo da warp) o accanto a un varco.

Regole del brief (mappings/categories.json -> "validity"), registrate in brief_checks senza toccare la griglia:
  1. un solo giocatore e almeno una scala;
  2. bordi chiusi (muro o fuori mappa); con close_border=true la griglia viene davvero chiusa;
  3. al massimo 2 porte chiuse (gruppi di celle 'D' adiacenti);
  4. scale raggiungibili dal giocatore (BFS 4-direzioni, porte = muro finche' non si raggiunge una chiave).

Modulo puro (niente ROM): lavora su liste di liste di int.
"""
from __future__ import annotations

from collections import deque

VOID, WALL, FLOOR, WATER, BRIDGE, DOOR, KEY, BLOCK, STAIRS, PLAYER, ENEMY = range(11)
H, W = 8, 10
DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))
SIDE_ORDER = {"bottom": 0, "left": 1, "right": 2, "top": 3}


def is_border(x, y):
    return x == 0 or y == 0 or x == W - 1 or y == H - 1


def side_of(x, y):
    if y == H - 1:
        return "bottom"
    if x == 0:
        return "left"
    if x == W - 1:
        return "right"
    return "top"


def inward(x, y):
    """Cella adiacente verso l'interno di una cella di bordo."""
    ix = 1 if x == 0 else (W - 2 if x == W - 1 else x)
    iy = 1 if y == 0 else (H - 2 if y == H - 1 else y)
    return ix, iy


def cells(g, cat):
    return [(x, y) for y in range(H) for x in range(W) if g[y][x] == cat]


def components(g, cat):
    """Gruppi 4-connessi di celle della categoria cat."""
    seen, out = set(), []
    for c in cells(g, cat):
        if c in seen:
            continue
        comp, stack = [], [c]
        seen.add(c)
        while stack:
            x, y = stack.pop()
            comp.append((x, y))
            for dx, dy in DIRS:
                n = (x + dx, y + dy)
                if 0 <= n[0] < W and 0 <= n[1] < H and n not in seen and g[n[1]][n[0]] == cat:
                    seen.add(n)
                    stack.append(n)
        out.append(comp)
    return out


def bfs(g, start, traversable):
    """Distanze BFS da start. Le porte diventano attraversabili solo dopo aver raggiunto una chiave."""
    trav = set(traversable)
    doors_open = False
    while True:
        dist = {start: 0}
        q = deque([start])
        got_key = False
        while q:
            x, y = q.popleft()
            if g[y][x] == KEY:
                got_key = True
            for dx, dy in DIRS:
                nx, ny = x + dx, y + dy
                if not (0 <= nx < W and 0 <= ny < H) or (nx, ny) in dist:
                    continue
                c = g[ny][nx]
                if c in trav or (doors_open and c == DOOR):
                    dist[(nx, ny)] = dist[(x, y)] + 1
                    q.append((nx, ny))
        if got_key and not doors_open and cells(g, DOOR):
            doors_open = True
            continue
        return dist


def nearest_floor(g, x, y, max_d=3, interior=True):
    best = None
    for yy in range(H):
        for xx in range(W):
            if g[yy][xx] != FLOOR or (interior and is_border(xx, yy)):
                continue
            d = abs(xx - x) + abs(yy - y)
            if d <= max_d and (best is None or (d, yy, xx) < best[0]):
                best = ((d, yy, xx), (xx, yy))
    return None if best is None else best[1]


def find_openings(grid, passage, traversable):
    """Varchi sul bordo (celle non d'angolo): kind 'door' = varco del gioco (porta, apertura, scala nel muro),
    kind 'corridor' = cella attraversabile con dietro una cella attraversabile."""
    tset = set(traversable)
    out = []
    for y in range(H):
        for x in range(W):
            if not is_border(x, y) or (x in (0, W - 1) and y in (0, H - 1)):
                continue
            ix, iy = inward(x, y)
            if passage[y][x]:
                out.append({"x": x, "y": y, "side": side_of(x, y), "kind": "door"})
            elif grid[y][x] in tset and grid[iy][ix] in tset:
                out.append({"x": x, "y": y, "side": side_of(x, y), "kind": "corridor"})
    return out


def fix_and_validate(grid_raw, passage, arrivals, cfg):
    """Ritorna dict con grid, fixes, notes, reasons (vuoto => valida), openings.

    grid_raw : 8x10 categorie (tile + entita')
    passage  : 8x10 bool, True se l'oggetto e' un varco verso un'altra stanza (porta, apertura...)
    arrivals : lista di (x, y) celle dove il gioco fa comparire Link entrando da un warp
    cfg      : dict "validity" + "traversable" (lista codici) [+ "bfs_traversable"]
    """
    g = [list(r) for r in grid_raw]
    fixes, notes, reasons = [], [], []
    trav = cfg["traversable"]
    bfs_trav = cfg.get("bfs_traversable", trav)
    allowed = set(cfg.get("border_allowed", [VOID, WALL]))
    close = cfg.get("close_border", False)

    openings = find_openings(grid_raw, passage, trav)

    # --- regola 2 (solo se richiesta): chiusura dei bordi --------------------------------
    if close:
        closed = 0
        for y in range(H):
            for x in range(W):
                if is_border(x, y) and g[y][x] not in allowed:
                    if g[y][x] == STAIRS and cfg.get("move_border_stairs_inward", True):
                        ix, iy = inward(x, y)
                        if g[iy][ix] == FLOOR:
                            g[iy][ix] = STAIRS
                            fixes.append({"type": "move_stairs_inward", "from": [x, y], "to": [ix, iy]})
                    g[y][x] = cfg.get("border_fill", WALL)
                    closed += 1
        if closed:
            fixes.append({"type": "close_border", "cells": closed})

    # --- regola 1a: un solo giocatore --------------------------------------------------
    players = cells(g, PLAYER)
    for x, y in players[1:]:
        g[y][x] = FLOOR
        fixes.append({"type": "remove_extra_player", "x": x, "y": y})
    if not players:
        # candidati: punti d'arrivo dei warp, poi celle interne accanto ai varchi (porte prima dei corridoi,
        # lati in ordine basso/sinistra/destra/alto). Si preferisce il candidato da cui si raggiungono
        # le scale gia' presenti, poi il punto d'arrivo vero del gioco, poi porte e corridoi, e a parita'
        # quello che raggiunge l'area piu' grande.
        cands = []
        for k, (ax, ay) in enumerate(arrivals):
            p = nearest_floor(g, ax, ay)
            if p:
                cands.append(((0, k), p, "warp_arrival"))
        for o in sorted(openings, key=lambda o: (o["kind"] != "door", SIDE_ORDER[o["side"]], o["y"], o["x"])):
            ix, iy = inward(o["x"], o["y"])
            p = (ix, iy) if g[iy][ix] == FLOOR else nearest_floor(g, ix, iy, max_d=1)
            if p:
                cands.append(((1 if o["kind"] == "door" else 2, len(cands)), p, "border_opening"))
        best = None
        stairs0 = cells(g, STAIRS)
        for prio, p, src in cands:
            dist = bfs(g, p, bfs_trav)
            reaches = any(s in dist for s in stairs0)
            # priorita': raggiunge le scale esistenti > arrivo da warp > porta > corridoio > area piu' grande
            key = (not reaches, prio[0], -len(dist), prio[1])
            if best is None or key < best[0]:
                best = (key, p, src)
        if best is None:
            p = nearest_floor(g, 4, 3, max_d=99)
            if p:
                best = (None, p, "fallback_center")
                notes.append("nessun ingresso trovato: giocatore sul pavimento piu' vicino al centro")
        if best is None:
            reasons.append("no_floor_for_player")
        else:
            _, (px, py), src = best
            g[py][px] = PLAYER
            fixes.append({"type": "add_player", "x": px, "y": py, "source": src})

    players = cells(g, PLAYER)
    stairs = cells(g, STAIRS)
    stairs_reachable = None
    if players and stairs:
        dist = bfs(g, players[0], bfs_trav)
        stairs_reachable = any(s in dist for s in stairs)
    # Le scale NON vengono inventate (mappatura 1:1 con il gioco): se mancano lo si registra soltanto.
    if stairs == [] and cfg.get("add_stairs", False) and players:
        dist = bfs(g, players[0], bfs_trav)
        cand = [(d, c) for c, d in dist.items() if g[c[1]][c[0]] == FLOOR and not is_border(*c)]
        if cand:
            d, (sx, sy) = max(cand, key=lambda t: (t[0], -t[1][1], -t[1][0]))
            g[sy][sx] = STAIRS
            fixes.append({"type": "add_stairs", "x": sx, "y": sy, "bfs_distance": d})
            stairs, stairs_reachable = [(sx, sy)], True

    # --- regola 3: porte (una porta = un gruppo di celle D adiacenti) --------------------
    n_doors = len(components(g, DOOR))

    # Regole del brief, solo registrate (la griglia resta fedele al gioco)
    border_closed = all(g[y][x] in allowed for y in range(H) for x in range(W) if is_border(x, y))
    brief = {
        "one_player": len(cells(g, PLAYER)) == 1,
        "has_stairs": bool(stairs),
        "stairs_reachable": stairs_reachable,
        "border_closed": border_closed,
        "max_doors_ok": n_doors <= cfg.get("max_doors", 2),
    }
    brief["all_ok"] = all(v is True for v in brief.values())
    if len(cells(g, PLAYER)) != 1 and "no_floor_for_player" not in reasons:
        reasons.append("player_count")
    return {"grid": g, "fixes": fixes, "notes": notes, "reasons": sorted(set(reasons)),
            "openings": openings, "doors": n_doors, "brief_checks": brief}
