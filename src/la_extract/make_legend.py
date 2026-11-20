"""Legenda della conversione: categorie, oggetti del gioco ed entita' con simbolo ASCII.

Produce:
  src/la_extract/LEGEND.md                          (senza immagini del gioco: si puo' versionare)
  <out>/legend.html                                 (con le immagini del gioco: SOLO uso locale)

Uso:  python src/la_extract/make_legend.py [--rom ROM] [--ladxr DIR] [--out data/la_local/legend] [--no-html]
"""
from __future__ import annotations

import argparse
import base64
import html
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ladx  # noqa: E402

W = 10


def load():
    cats = ladx.load_json("categories.json")
    ow = ladx.load_json("objects_overworld.json")
    ind = ladx.load_json("objects_indoor.json")
    ents = ladx.load_json("entities.json")
    return cats, ow, ind, ents


RULES = [
    "Mappatura **1:1** con il gioco: ogni blocco 16x16 della stanza diventa una cella; nulla viene inventato.",
    "Unica aggiunta: il giocatore `P`, dove il gioco fa entrare Link (arrivo da warp) o accanto al varco d'ingresso.",
    "Le scale `E` sono solo quelle presenti nel gioco: se la stanza non ne ha, non ce ne sono.",
    "Bordi non chiusi: porte, varchi e corridoi sul bordo restano come nel gioco.",
    "Porte e varchi nei muri sono larghi un blocco (16 px) ma centrati tra due celle: la meta' 1 (sinistra/alto) e' il "
    "passaggio (o `D`), la meta' 2 e' muro. Stessa convenzione in tutte le stanze, quindi i varchi adiacenti restano allineati.",
    "Fuori mappa (spazio): cielo/orizzonte dell'overworld, riempimento `03` fuori dai muri, spazio attorno alle stanze piccole, "
    "roccia esterna delle caverne mai raggiungibile.",
    "Ogni room.json ha due griglie: `grid_ascii` (layout + `P` + `M`) e `grid_no_entities_ascii` (solo il layout).",
]


def pair_label(e):
    if "door_half1" in e.get("tags", []):
        return f" (meta' 1 del varco, coppia con {e['pair']})" if e.get("pair") else ""
    if "door_half2" in e.get("tags", []):
        return f" (meta' 2 del varco {e['pair']}: muro)" if e.get("pair") else ""
    return ""


def md_legend(cats, ow, ind, ents) -> str:
    cb = {c["code"]: c for c in cats["categories"]}
    L = ["# Legenda LevelEdit <- Link's Awakening DX", "",
         "Generata da `make_legend.py` a partire dai file in `mappings/`. Nessun dato grafico del gioco.", "",
         "## Regole di conversione", "", *[f"- {r}" for r in RULES], "",
         "## Categorie", "", "| Codice | Simbolo | Categoria | Attraversabile | Colore | Cosa diventa dal gioco |",
         "|---|---|---|---|---|---|"]
    for c in cats["categories"]:
        sym = "(spazio)" if c["ascii"] == " " else f"`{c['ascii']}`"
        col = "#%02X%02X%02X" % tuple(c["color"])
        L.append(f"| {c['code']} | {sym} | {c['name_it']} | {c['traversable']} | {col} | {c['from_game']} |")
    L += ["", "## Regole speciali", "", "| Tipo | Politica |", "|---|---|"]
    for k, v in cats["special_policy"].items():
        if not k.startswith("_"):
            L.append(f"| {k} | {v} |")

    def obj_table(title, objs, extra=""):
        out = ["", f"## {title}", ""]
        if extra:
            out += [extra, ""]
        out += ["| Id | Simbolo | Categoria | Nome | Tag / speciale | Physics | Celle nel gioco |", "|---|---|---|---|---|---|---|"]
        for k, e in objs.items():
            if k.startswith("_"):
                continue
            sym = "(spazio)" if e["ascii"] == " " else f"`{e['ascii']}`"
            tags = ", ".join(e.get("tags", []))
            if e.get("special"):
                tags += f" **[{e['special']}]**"
            if e.get("passage"):
                tags += " (varco)"
            tags += pair_label(e)
            out.append(f"| {k} | {sym} | {cb[e['category']]['name_it']} | {e['name']} | {tags} | {e.get('physics', '')} | {e.get('cells_in_game', '')} |")
        return out

    L += obj_table("Oggetti overworld", ow["objects"])
    L += obj_table("Oggetti interni (dungeon, caverne, case)", ind["objects"])
    L += obj_table("Color Dungeon: oggetti con significato diverso", ind["color_dungeon_overrides"])
    L += ["", "## Entita'", "", "Solo le entita' presenti nelle stanze del gioco (le altre sono in `mappings/entities.json`).", "",
          "| Id | Simbolo | Classe | Nome | Speciale | Occorrenze |", "|---|---|---|---|---|---|"]
    for k, e in ents["entities"].items():
        if e["count_in_game"] == 0:
            continue
        sym = f"`{e['ascii']}`" if e.get("ascii") else "-"
        L.append(f"| {k} | {sym} | {e['class']} | {e['name']} | {e.get('special', '')} | {e['count_in_game']} |")
    return "\n".join(L) + "\n"


def b64png(img, scale=3):
    from PIL import Image
    img = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def html_legend(g, cats, ow, ind, ents) -> str:
    from PIL import Image, ImageDraw
    cb = {c["code"]: c for c in cats["categories"]}
    # primo esempio di ogni oggetto (stanze non a scorrimento laterale)
    first = {}
    for r in ladx.all_room_ids():
        d = g.room(r)
        if d["sidescroll"]:
            continue
        for i, o in enumerate(d["objects"]):
            first.setdefault((d["region"], o), (r, i))

    def crop(region, obj_hex):
        ex = first.get((region, int(obj_hex, 16)))
        if ex is None:
            return None
        r, i = ex
        x, y = i % W, i // W
        return g.render(r).crop((x * 16, y * 16, x * 16 + 16, y * 16 + 16))

    def swatch(code):
        c = cb[code]
        img = Image.new("RGB", (16, 16), tuple(c["color"]))
        if c["ascii"].strip():
            lum = 0.299 * c["color"][0] + 0.587 * c["color"][1] + 0.114 * c["color"][2]
            ImageDraw.Draw(img).text((5, 2), c["ascii"], fill=(0, 0, 0) if lum > 140 else (255, 255, 255))
        return img

    def badge(code):
        c = cb[code]
        col = "#%02X%02X%02X" % tuple(c["color"])
        lum = 0.299 * c["color"][0] + 0.587 * c["color"][1] + 0.114 * c["color"][2]
        fg = "#000" if lum > 140 else "#fff"
        sym = "&nbsp;" if c["ascii"] == " " else html.escape(c["ascii"])
        return f'<span class="b" style="background:{col};color:{fg}">{sym}</span>'

    H = ["<!doctype html><html lang='it'><head><meta charset='utf-8'><title>Legenda LA -> LevelEdit</title>",
         "<meta name='viewport' content='width=device-width,initial-scale=1'>",
         "<style>body{font-family:system-ui,sans-serif;margin:16px;background:#fafafa;color:#222}"
         "table{border-collapse:collapse;margin:8px 0 24px}td,th{border:1px solid #ddd;padding:3px 6px;font-size:13px;vertical-align:middle}"
         "th{background:#eee;position:sticky;top:0}img{image-rendering:pixelated;display:block}"
         ".b{display:inline-block;min-width:22px;text-align:center;font:bold 14px monospace;border-radius:3px;padding:2px 0}"
         ".ex{display:flex;gap:4px;flex-wrap:wrap}.sp{color:#b00;font-weight:bold}code{font-size:12px}"
         "nav a{margin-right:12px}</style></head><body>",
         "<h1>Legenda: Link's Awakening DX &rarr; LevelEdit</h1>",
         "<p>Uso locale: contiene grafica del gioco, non pubblicare.</p>",
         "<h2>Regole di conversione</h2><ul>" + "".join(
             "<li>" + html.escape(r).replace("`", "").replace("**", "") + "</li>" for r in RULES) + "</ul>",
         "<nav><a href='#cat'>Categorie</a><a href='#ow'>Overworld</a><a href='#in'>Interni</a><a href='#col'>Color Dungeon</a><a href='#ent'>Entit&agrave;</a></nav>",
         "<h2 id='cat'>Categorie</h2><table><tr><th>Immagine</th><th>Simbolo</th><th>Codice</th><th>Nome</th><th>Attraversabile</th><th>Esempi dal gioco</th></tr>"]
    for c in cats["categories"]:
        exs = []
        for region, table in (("overworld", ow["objects"]), ("indoor", ind["objects"])):
            for k, e in table.items():
                if e["category"] == c["code"] and len(exs) < 10 and "door_half2" not in e.get("tags", []):
                    im = crop(region, k)
                    if im:
                        exs.append(f"<img title='{region} {k}: {html.escape(e['name'])}' src='{b64png(im, 2)}'>")
        H.append(f"<tr><td><img src='{b64png(swatch(c['code']), 3)}'></td><td>{badge(c['code'])}</td><td>{c['code']}</td>"
                 f"<td><b>{c['name_it']}</b> ({c['id']})<br><small>{html.escape(c['from_game'])}</small></td>"
                 f"<td>{c['traversable']}</td><td><div class='ex'>{''.join(exs)}</div></td></tr>")
    H.append("</table>")

    def obj_section(anchor, title, region, objs):
        H.append(f"<h2 id='{anchor}'>{title}</h2><table><tr><th>Immagine</th><th>Simbolo</th><th>Id</th><th>Nome</th>"
                 "<th>Categoria</th><th>Tag</th><th>Speciale</th><th>Physics</th><th>Celle</th></tr>")
        for k, e in objs.items():
            if k.startswith("_"):
                continue
            im = crop(region, k)
            img = f"<img src='{b64png(im, 3)}'>" if im else "-"
            tags = ", ".join(e.get("tags", [])) + (" (varco)" if e.get("passage") else "") + pair_label(e)
            sp = f"<span class='sp'>{e['special']}</span>" if e.get("special") else ""
            note = f"<br><small>{html.escape(e['note'])}</small>" if e.get("note") else ""
            dis = f"<br><code>{e['disasm']}</code>" if e.get("disasm") else ""
            H.append(f"<tr><td>{img}</td><td>{badge(e['category'])}</td><td><code>{k}</code></td>"
                     f"<td>{html.escape(e['name'])}{dis}{note}</td><td>{cb[e['category']]['name_it']}</td><td>{tags}</td>"
                     f"<td>{sp}</td><td>{e.get('physics', '')}</td><td>{e.get('cells_in_game', '')}</td></tr>")
        H.append("</table>")

    obj_section("ow", "Oggetti overworld", "overworld", ow["objects"])
    obj_section("in", "Oggetti interni (dungeon, caverne, case)", "indoor", ind["objects"])
    obj_section("col", "Color Dungeon: oggetti con significato diverso", "color", ind["color_dungeon_overrides"])
    H.append("<h2 id='ent'>Entit&agrave;</h2><p>Le entit&agrave; sono sprite: qui senza immagine. "
             "Classi che entrano in griglia: nemici/miniboss/boss &rarr; M, oggetti solidi &rarr; muro, sollevabili &rarr; blocco.</p>"
             "<table><tr><th>Simbolo</th><th>Id</th><th>Nome</th><th>Classe</th><th>Speciale</th><th>Occorrenze</th></tr>")
    for k, e in ents["entities"].items():
        if e["count_in_game"] == 0:
            continue
        b = badge(e["category"]) if e.get("category") is not None else "-"
        sp = f"<span class='sp'>{e['special']}</span>" if e.get("special") else ""
        H.append(f"<tr><td>{b}</td><td><code>{k}</code></td><td>{e['name']}</td><td>{e['class']}</td><td>{sp}</td><td>{e['count_in_game']}</td></tr>")
    H.append("</table></body></html>")
    return "\n".join(H)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rom")
    ap.add_argument("--ladxr")
    ap.add_argument("--out", default=str(ladx.DEFAULT_OUT / "legend"))
    ap.add_argument("--no-html", action="store_true")
    args = ap.parse_args()
    cats, ow, ind, ents = load()
    md = md_legend(cats, ow, ind, ents)
    (ladx.PKG_DIR / "LEGEND.md").write_text(md, encoding="utf-8")
    print("scritto", ladx.PKG_DIR / "LEGEND.md")
    if not args.no_html:
        g = ladx.Game(args.rom, args.ladxr)
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        (out / "legend.html").write_text(html_legend(g, cats, ow, ind, ents), encoding="utf-8")
        print("scritto", out / "legend.html")


if __name__ == "__main__":
    main()
