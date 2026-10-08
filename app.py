import json
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title="MISTER CHAMPIONS", page_icon="🏆", layout="wide")

# ══════════════════════════════════════════════════════════════
#  RESULTADOS REALES (puntos fantasy)
#  Formato: (jornada_champions, local, visitante, pts_local, pts_visitante)
#  Ejemplo: (1, "Palop", "Fale", 71.5, 64.0),
# ══════════════════════════════════════════════════════════════
RES_ARCHIVO = Path(__file__).parent / "resultados_fantasy.json"
RESULTADOS = json.loads(RES_ARCHIVO.read_text(encoding="utf-8")) if RES_ARCHIVO.exists() else []

# ══════════════════════════════════════════════════════════════
#  CARGA DEL SORTEO
# ══════════════════════════════════════════════════════════════
ARCHIVO = Path(__file__).parent / "sorteo_fantasy.json"

if not ARCHIVO.exists():
    st.error("No encuentro `sorteo_fantasy.json`. Ejecuta primero el script de sorteos y completa "
                "los tres sorteos; el archivo debe estar en la misma carpeta que esta app.")
    st.stop()

DATOS = json.loads(ARCHIVO.read_text(encoding="utf-8"))
if not (DATOS.get("grupos") and DATOS.get("calendario")):
    st.warning("El sorteo no está completo. Termina los 3 sorteos (grupos, enfrentamientos y "
                "calendario) y recarga esta página.")
    st.stop()

GR = DATOS["grupos"]
CAL = [{k: [tuple(p) for p in fila[k]["partidos"]] for k in "AB"} for fila in DATOS["calendario"]]
LIGA = {fila["cl"]: fila["liga"] for fila in DATOS["calendario"]}
TODOS = GR["A"] + GR["B"]
RES = {(j, l, v): (pl, pv) for j, l, v, pl, pv in RESULTADOS}


# ══════════════════════════════════════════════════════════════
#  LÓGICA
# ══════════════════════════════════════════════════════════════
def fase_de(j):
    return "IDA" if j <= 5 else "VUELTA"


def partidos_de(j):
    return [(k, l, v) for k in "AB" for l, v in CAL[j - 1][k]]


def scores_de(j):
    sc = {}
    for _, l, v in partidos_de(j):
        r = RES.get((j, l, v))
        if r:
            sc[l], sc[v] = r
    return sc


def completa(j):
    return len(scores_de(j)) == 12


def ultima_con_datos():
    return max([j for j in range(1, 11) if scores_de(j)] or [0])


def jornada_actual():
    for j in range(1, 11):
        if not completa(j):
            return j
    return 10


def stats_hasta(n):
    S = {p: dict(PJ=0, G=0, E=0, P=0, Pts=0, PF=0.0, Max=0.0, N1=0, forma=[]) for p in TODOS}
    for j in range(1, n + 1):
        sc = scores_de(j)
        for _, l, v in partidos_de(j):
            r = RES.get((j, l, v))
            if not r:
                continue
            pl, pv = r
            for p, mine, other in ((l, pl, pv), (v, pv, pl)):
                s = S[p]
                s["PJ"] += 1
                s["PF"] += mine
                s["Max"] = max(s["Max"], mine)
                if mine > other:
                    s["G"] += 1; s["Pts"] += 3; s["forma"].append("G")
                elif mine == other:
                    s["E"] += 1; s["Pts"] += 1; s["forma"].append("E")
                else:
                    s["P"] += 1; s["forma"].append("P")
        if len(sc) == 12:
            top = max(sc.values())
            for p, x in sc.items():
                if x == top:
                    S[p]["N1"] += 1
    return S


def clasificacion(n):
    """Desempate: Pts ↓, Nº 1º ↓, Máx.pts ↓, puntos fantasy totales ↑ (el que menos tenga),
    y por último el orden del sorteo (el sort de Python es estable)."""
    S = stats_hasta(n)
    out = {}
    for k in "AB":
        filas = [(p, S[p]) for p in GR[k]]
        filas.sort(key=lambda x: (-x[1]["Pts"], -x[1]["N1"], -x[1]["Max"], x[1]["PF"]))
        out[k] = filas
    return out


# ══════════════════════════════════════════════════════════════
#  ESTILO
# ══════════════════════════════════════════════════════════════
CSS = """
<style>
.stApp{background:radial-gradient(circle at 50% -10%,#16357e 0,#08142f 45%,#040a1a 100%);color:#fff}
header[data-testid="stHeader"]{background:transparent}
.block-container{padding-top:1.2rem;max-width:1250px}
h1,h2,h3,h4,p,span,label,div{color:inherit}
.title{text-align:center;font-size:38px;font-weight:900;letter-spacing:4px;color:#f5c518;
text-shadow:0 0 22px #f5c51866;margin:0}
.subtitle{text-align:center;color:#9fb3e8;letter-spacing:3px;font-size:13px;margin-bottom:12px}
.hero{border-radius:20px;padding:22px 26px;margin:8px 0 16px;border:1px solid #ffffff25;
background:repeating-linear-gradient(90deg,#0f6b3a 0,#0f6b3a 60px,#12794300 60px,#127943 120px);
background-color:#0f6b3a;box-shadow:0 10px 40px #000a;position:relative;overflow:hidden}
.hero:after{content:"";position:absolute;left:50%;top:-20%;width:2px;height:140%;background:#ffffff40}
.hero .h1{font-size:44px;font-weight:900;letter-spacing:2px;text-shadow:0 3px 12px #000}
.hero .h2{font-size:16px;color:#e8fff0;letter-spacing:1px}
.bar{height:10px;border-radius:6px;background:#00000055;margin-top:12px;overflow:hidden}
.bar div{height:100%;background:linear-gradient(90deg,#ffd84d,#f2a900)}
.gtitle{font-weight:900;letter-spacing:3px;padding:6px 14px;border-radius:10px;margin:8px 0;display:inline-block}
.gA{background:#2f80ed}.gB{background:#eb5757}
.match{display:flex;align-items:center;gap:8px;background:#ffffff0f;border:1px solid #ffffff1a;
border-radius:14px;padding:10px 12px;margin:7px 0}
.match .t{flex:1;font-weight:700;font-size:16px}
.match .l{text-align:right}.match .r{text-align:left}
.match .sc{min-width:130px;text-align:center;font-weight:900;font-size:20px;background:#000000aa;
border-radius:10px;padding:4px 8px;color:#f5c518}
.match .sc.pend{color:#7f8fb8;font-size:14px}
.win{color:#4dff9a}.lose{color:#ff9a9a;opacity:.8}.draw{color:#ffd84d}
.jrow{border-radius:16px;padding:10px 14px;margin:12px 0;background:#ffffff0a;border:1px solid #ffffff18}
.jrow.ida{border-left:6px solid #2f80ed}.jrow.vuelta{border-left:6px solid #f2994a}
.jrow.actual{box-shadow:0 0 0 2px #f5c518,0 0 24px #f5c51855}
.jhead{font-weight:800;letter-spacing:1px;margin-bottom:4px}
.badge{font-size:11px;padding:2px 9px;border-radius:12px;margin-left:8px;color:#111;font-weight:800}
.b-ida{background:#6aa8ff}.b-vuelta{background:#ffb066}.b-act{background:#f5c518}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media(max-width:800px){.grid{grid-template-columns:1fr}}
.cm{font-size:14px;display:flex;justify-content:space-between;gap:6px;padding:3px 0;border-bottom:1px solid #ffffff10}
.cm b{color:#f5c518}
table.cl{width:100%;border-collapse:collapse;font-size:14px;margin-bottom:6px}
table.cl th{background:#f5c51822;color:#f5c518;padding:7px 5px;font-size:12px;text-align:center;letter-spacing:1px}
table.cl td{padding:7px 5px;text-align:center;border-bottom:1px solid #ffffff14;background:#ffffff08}
table.cl td.n{text-align:left;font-weight:800}
table.cl tr.q td:first-child{border-left:5px solid #27ae60}
table.cl tr.x td:first-child{border-left:5px solid #eb5757}
table.cl td.pts{font-weight:900;font-size:16px;color:#f5c518}
.up{color:#4dff9a;font-size:11px}.dn{color:#ff6b6b;font-size:11px}
.dot{display:inline-block;width:11px;height:11px;border-radius:50%;margin:0 1px}
.dG{background:#27ae60}.dE{background:#f2c94c}.dP{background:#eb5757}
.leyenda{font-size:12px;color:#9fb3e8;margin-bottom:10px}
div[data-baseweb="tab-list"]{gap:6px}
button[data-baseweb="tab"]{background:#ffffff12;border-radius:14px 14px 0 0;padding:8px 18px}
button[aria-selected="true"]{background:#f5c518 !important;color:#111 !important}
button[aria-selected="true"] p{color:#111 !important;font-weight:800}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def html(s):
    st.markdown(s, unsafe_allow_html=True)


def match_html(j, l, v):
    r = RES.get((j, l, v))
    if not r:
        return f'<div class="match"><div class="t l">{l}</div><div class="sc pend">vs</div><div class="t r">{v}</div></div>'
    pl, pv = r
    cl, cv = ("win", "lose") if pl > pv else (("lose", "win") if pv > pl else ("draw", "draw"))
    return (f'<div class="match"><div class="t l {cl}">{l}</div>'
            f'<div class="sc">{pl:g} - {pv:g}</div><div class="t r {cv}">{v}</div></div>')


def cm_html(j, l, v):
    r = RES.get((j, l, v))
    mid = f"<b>{r[0]:g} - {r[1]:g}</b>" if r else "<span style='color:#7f8fb8'>vs</span>"
    return f'<div class="cm"><span>{l}</span>{mid}<span>{v}</span></div>'


def tabla_html(k, n):
    actual = clasificacion(n)[k]
    previa = None
    if n >= 2:
        previa = {p: i for i, (p, _) in enumerate(clasificacion(n - 1)[k])}
    h = ('<table class="cl"><tr><th>#</th><th style="text-align:left">EQUIPO</th><th>PTS</th><th>Nº 1º</th>'
         '<th>MÁX.PTS</th><th>G</th><th>P</th><th>E</th><th>PJ</th><th>RACHA</th></tr>')
    for i, (p, s) in enumerate(actual):
        flecha = ""
        if previa is not None:
            d = previa[p] - i
            flecha = f'<span class="up">▲{d}</span>' if d > 0 else (f'<span class="dn">▼{-d}</span>' if d < 0 else "")
        racha = "".join(f'<span class="dot d{x}"></span>' for x in s["forma"][-5:]) or "–"
        medalla = "👑 " if (i == 0 and s["PJ"] > 0) else ""
        h += (f'<tr class="{"q" if i < 4 else "x"}"><td>{i + 1} {flecha}</td><td class="n">{medalla}{p}</td>'
              f'<td class="pts">{s["Pts"]}</td><td>{s["N1"]}</td><td>{s["Max"]:g}</td>'
              f'<td>{s["G"]}</td><td>{s["P"]}</td><td>{s["E"]}</td><td>{s["PJ"]}</td><td>{racha}</td></tr>')
    return h + "</table>"


def mostrar_clasificacion(n):
    c1, c2 = st.columns(2)
    for col, k in zip((c1, c2), "AB"):
        with col:
            html(f'<span class="gtitle g{k}">GRUPO {k}</span>')
            html(tabla_html(k, n))
    html('<div class="leyenda">🟩 Clasifican los 4 primeros · 🟥 Eliminados · '
         'Nº 1º = veces que fue el mejor de los 12 en una jornada · Máx.pts = mejor puntuación fantasy<br>'
         '<b>Desempate:</b> Puntos → Nº 1º → Máx.pts → puntos fantasy totales (gana el que tiene <u>menos</u>) '
         '→ orden del sorteo</div>')


# ══════════════════════════════════════════════════════════════
#  PÁGINA
# ══════════════════════════════════════════════════════════════
html('<div class="title">🏆 FANTASY CHAMPIONS LEAGUE</div>'
     '<div class="subtitle">FASE DE GRUPOS · IDA Y VUELTA · PASAN LOS 4 PRIMEROS</div>')

ACT = jornada_actual()
ULT = ultima_con_datos()

tab1, tab2, tab3, tab4 = st.tabs(["⚽ Jornada actual", "📅 Calendario", "🏆 Clasificación", "📊 Resumen de jornadas"])

# ───────── JORNADA ACTUAL ─────────
with tab1:
    j = st.selectbox("Ver jornada", list(range(1, 11)), index=ACT - 1,
                     format_func=lambda x: f"Jornada {x}" + ("  ·  ACTUAL" if x == ACT else ""))
    jugados = sum(1 for _, l, v in partidos_de(j) if (j, l, v) in RES)
    estado = "✅ Completada" if jugados == 6 else ("🔴 En juego" if jugados else "⏳ Pendiente")
    html(f'<div class="hero"><div class="h1">JORNADA {j}</div>'
         f'<div class="h2">Liga J{LIGA[j]} · {fase_de(j)} · {estado} · {jugados}/6 partidos con resultado</div>'
         f'<div class="bar"><div style="width:{jugados / 6 * 100:.0f}%"></div></div></div>')
    c1, c2 = st.columns(2)
    for col, k in zip((c1, c2), "AB"):
        with col:
            html(f'<span class="gtitle g{k}">GRUPO {k}</span>')
            html("".join(match_html(j, l, v) for l, v in CAL[j - 1][k]))
    sc = scores_de(j)
    if sc:
        mejor = max(sc, key=sc.get)
        html(f'<div class="leyenda">⭐ Mejor puntuación de la jornada: <b style="color:#f5c518">{mejor}</b> con {sc[mejor]:g} pts</div>')
    st.markdown("### 🏆 Clasificación actual")
    mostrar_clasificacion(ULT)

# ───────── CALENDARIO ─────────
with tab2:
    html('<div class="leyenda">Formato: Local – Visitante · Resultado en puntos fantasy · La jornada resaltada es la actual</div>')
    for j in range(1, 11):
        f = fase_de(j)
        css = "ida" if f == "IDA" else "vuelta"
        extra = " actual" if j == ACT else ""
        badges = f'<span class="badge b-{css}">{f}</span>' + ('<span class="badge b-act">ACTUAL</span>' if j == ACT else "")
        cols = ""
        for k in "AB":
            cols += f'<div><span class="gtitle g{k}" style="font-size:12px">GRUPO {k}</span>'
            cols += "".join(cm_html(j, l, v) for l, v in CAL[j - 1][k]) + "</div>"
        html(f'<div class="jrow {css}{extra}"><div class="jhead">JORNADA {j} · LIGA J{LIGA[j]} {badges}</div>'
             f'<div class="grid">{cols}</div></div>')

# ───────── CLASIFICACIÓN ─────────
with tab3:
    n = st.select_slider("Clasificación tras…", options=list(range(0, max(ULT, 1) + 1)), value=ULT,
                         format_func=lambda x: "Inicial (sorteo)" if x == 0 else f"Jornada {x}")
    mostrar_clasificacion(n)
    if ULT >= 1:
        st.markdown("### 📈 Evolución de puntos de liga")
        c1, c2 = st.columns(2)
        for col, k in zip((c1, c2), "AB"):
            with col:
                datos = {p: [stats_hasta(x)[p]["Pts"] for x in range(0, ULT + 1)] for p in GR[k]}
                st.caption(f"Grupo {k}")
                st.line_chart(pd.DataFrame(datos, index=range(0, ULT + 1)))

# ───────── RESUMEN ─────────
with tab4:
    filas = []
    for j in range(1, ULT + 1):
        sc = scores_de(j)
        if not sc:
            continue
        mejor, peor = max(sc, key=sc.get), min(sc, key=sc.get)
        dif = [(abs(a - b), l, v, a, b) for _, l, v in partidos_de(j) if (j, l, v) in RES
                for a, b in [RES[(j, l, v)]]]
        d = max(dif)
        filas.append({
            "Jornada": f"J{j} (Liga J{LIGA[j]})",
            "Fase": fase_de(j),
            "👑 Mejor": f"{mejor} ({sc[mejor]:g})",
            "🥶 Peor": f"{peor} ({sc[peor]:g})",
            "Media": round(sum(sc.values()) / len(sc), 1),
            "💥 Mayor goleada": f"{d[1]} {d[3]:g} - {d[4]:g} {d[2]}",
            "Estado": "Completa" if completa(j) else "En juego",
        })
    if filas:
        st.dataframe(pd.DataFrame(filas), hide_index=True, width="stretch")
        medias = pd.DataFrame({"Media de puntos": [f["Media"] for f in filas]},
                                index=[f["Jornada"].split(" ")[0] for f in filas])
        st.markdown("#### Media de puntos por jornada")
        st.bar_chart(medias)
    else:
        st.info("Todavía no hay resultados. Cuando se añadan aparecerá aquí el resumen.")