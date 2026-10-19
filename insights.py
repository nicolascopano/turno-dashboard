"""Textos profundos del diagnóstico ejecutivo e informe-brief para un bot rastreador.

Todo se calcula a partir del DataFrame ya enriquecido por analytics.enrich_dataframe().
Los textos de `build_executive_bullets` usan HTML (<b>) porque se pintan dentro de cajas HTML.
El brief para el bot es texto plano (más una versión JSON).
"""
from __future__ import annotations

import re
from html import escape

import numpy as np
import pandas as pd

import analytics

MAIN_PROGRAMS = ["Turno AM", "Turno en Vivo", "Turno PM", "Turno Z"]
FATIGUE = "⚠️ Alerta de Fatiga"
UNDEREXPLOITED = "🚀 Oportunidad Sub-explotada"


# ----------------------------------------------------------------------------
# Utilidades
# ----------------------------------------------------------------------------
def _n(x) -> str:
    return f"{int(round(float(x))):,}".replace(",", ".")


def _short(text, limit: int = 90) -> str:
    t = " ".join(str(text).split())
    return t if len(t) <= limit else t[: limit - 1].rstrip() + "…"


def _q(text, limit: int = 90) -> str:
    """Titular entre comillas, seguro para HTML."""
    return f"«{escape(_short(text, limit))}»"


def _hour_label(h) -> str:
    return f"{int(h):02d}:00"


def _hours_by_platform(df: pd.DataFrame, min_n: int = 3) -> dict:
    """Mejores y peores horas de subida por plataforma (mediana del multiplicador)."""
    out = {}
    for p in ("YouTube", "Instagram"):
        sub = df[df["platform"] == p]
        if sub.empty:
            continue
        g = (
            sub.groupby("hour")
            .agg(n=("views", "count"), med=("perf_index", "median"))
            .query("n >= @min_n")
            .sort_values("med", ascending=False)
        )
        if len(g) < 3:
            out[p] = {"best": [], "worst": []}
            continue
        out[p] = {
            "best": [(int(h), float(r.med), int(r.n)) for h, r in g.head(3).iterrows()],
            "worst": [(int(h), float(r.med), int(r.n)) for h, r in g.tail(2).iloc[::-1].iterrows()],
        }
    return out


def _hook_table(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("hook_type")
        .agg(n=("views", "count"), mean=("perf_index", "mean"), med=("perf_index", "median"), debate=("debate_rate", "mean"))
        .sort_values("med", ascending=False)
    )


def _best_format_for(sub: pd.DataFrame):
    g = (
        sub.groupby(["platform", "kind"])
        .agg(n=("views", "count"), perf=("perf_index", "mean"), med_views=("views", "median"))
        .sort_values("perf", ascending=False)
    )
    solid = g[g["n"] >= 2]
    return (solid if not solid.empty else g).iloc[0], (solid if not solid.empty else g).index[0]


# ----------------------------------------------------------------------------
# 1. Diagnóstico ejecutivo profundo
# ----------------------------------------------------------------------------
def build_executive_bullets(
    df: pd.DataFrame, topic_df: pd.DataFrame, entity_df: pd.DataFrame, bets: list[dict], days: int
) -> list[dict]:
    bullets: list[dict] = []
    if df.empty or topic_df.empty:
        return bullets

    def add(title: str, status: str, detail: str) -> None:
        bullets.append({"title": title, "status": status, "detail": detail})

    n = len(df)
    views_total = int(df["views"].sum())
    sp = {
        p: {
            "n": int((df["platform"] == p).sum()),
            "views": int(df.loc[df["platform"] == p, "views"].sum()),
            "avg": float(df.loc[df["platform"] == p, "views"].mean()) if (df["platform"] == p).any() else 0.0,
        }
        for p in ("YouTube", "Instagram")
    }

    # --- Panorama general -----------------------------------------------------
    parts = [
        f"En los últimos <b>{days} días</b> Turno publicó <b>{n}</b> piezas (≈{n / days:.0f} por día): "
        f"{sp['YouTube']['n']} en YouTube y {sp['Instagram']['n']} en Instagram. Acumulan <b>{_n(views_total)}</b> vistas, "
        f"con una mediana de <b>{_n(df['views'].median())}</b> vistas por pieza."
    ]
    if sp["YouTube"]["n"] and sp["Instagram"]["n"]:
        ig_v = sp["Instagram"]["views"] / max(views_total, 1) * 100
        ig_n = sp["Instagram"]["n"] / n * 100
        parts.append(
            f"Instagram concentra el <b>{ig_v:.0f}%</b> de las vistas con el {ig_n:.0f}% de las piezas "
            f"({_n(sp['Instagram']['avg'])} vistas por pieza frente a {_n(sp['YouTube']['avg'])} en YouTube). "
            "Las «vistas» se miden distinto en cada red, por eso el análisis compara cada pieza contra su propio formato (multiplicador «x»)."
        )
    sv = int(df["shares"].sum() + df["saved"].sum())
    parts.append(
        f"Generaron {_n(df['likes'].sum())} likes, {_n(df['comments'].sum())} comentarios y {_n(sv)} compartidos/guardados "
        f"(engagement promedio {df['engagement_rate'].mean():.2f}% sobre las vistas)."
    )
    young = int((df["age_hours"] < 24).sum())
    if young:
        parts.append(f"{young} piezas tienen menos de 24 h y siguen sumando vistas: sus cifras actuales subestiman su resultado final.")
    add("Panorama del período", "info", " ".join(parts))

    # --- Momentum 48 h vs 48 h previas ---------------------------------------
    recent = df[df["age_hours"] <= 48]
    prev = df[(df["age_hours"] > 48) & (df["age_hours"] <= 96)]
    if len(recent) >= 3 and len(prev) >= 3:
        r_med, p_med = float(recent["perf_index"].median()), float(prev["perf_index"].median())
        ratio = r_med / max(p_med, 0.01)
        if min(len(recent), len(prev)) < 10:
            status = "info"
            verdict = (
                "con tan pocas piezas en una de las ventanas (por ejemplo un fin de semana con menos producción) "
                "la comparación no es concluyente"
            )
        elif ratio >= 1.1:
            status, verdict = "ok", "el contenido reciente está rindiendo mejor que el de los dos días previos"
        elif ratio <= 0.8:
            status, verdict = "warn", "el contenido reciente rinde por debajo del de los dos días previos"
        else:
            status, verdict = "info", "el rendimiento reciente se mantiene en línea con el de los dos días previos"
        add(
            "Momentum: últimas 48 h vs. 48 h anteriores",
            status,
            f"Últimas 48 h: <b>{len(recent)}</b> piezas ({len(recent) / 2:.0f}/día) con multiplicador mediano <b>{r_med:.2f}x</b>. "
            f"48 h anteriores: <b>{len(prev)}</b> piezas ({len(prev) / 2:.0f}/día) con <b>{p_med:.2f}x</b>. "
            f"Lectura: {verdict}. Considera que lo más reciente aún no madura, así que una caída leve puede ser solo efecto de tiempo.",
        )

    # --- Plataformas y formatos ----------------------------------------------
    lines = []
    flags = []
    for p in ("YouTube", "Instagram"):
        sub = df[df["platform"] == p]
        if sub.empty:
            continue
        g = (
            sub.groupby("kind")
            .agg(n=("views", "count"), med=("views", "median"), avg=("views", "mean"), tot=("views", "sum"))
            .sort_values("med", ascending=False)
        )
        listed = "; ".join(f"{k}: {int(r.n)} piezas, mediana {_n(r.med)}" for k, r in g.iterrows())
        lines.append(f"<b>{p}</b> → {listed}.")
        for k, r in g.iterrows():
            share_n = r.n / len(sub) * 100
            share_v = r.tot / max(sub["views"].sum(), 1) * 100
            if r.n >= 8 and share_v < share_n * 0.5:
                flags.append(f"{k} ocupa el {share_n:.0f}% de las piezas de {p} pero aporta solo el {share_v:.0f}% de sus vistas")
    if lines:
        add(
            "Plataformas y formatos: dónde rinde cada cosa",
            "warn" if flags else "info",
            " ".join(lines) + (f" <b>Desbalance:</b> {'; '.join(flags)}." if flags else ""),
        )

    # --- Tema líder -----------------------------------------------------------
    lead = topic_df.iloc[0]
    sub = df[df["topic"] == lead["topic"]]
    fmt_row, (fp, fk) = _best_format_for(sub)
    top_hook = _hook_table(sub).index[0]
    top_piece = sub.sort_values("views", ascending=False).iloc[0]
    sv_t = int(sub["shares"].sum() + sub["saved"].sum())
    add(
        f"Tema líder: {lead['topic']}",
        "ok",
        f"Rinde <b>{lead['perf_score']:.2f}x</b> sobre lo normal: {int(lead['pieces'])} piezas ({lead['share_volume']:.0f}% del esfuerzo) "
        f"generan el <b>{lead['share_views']:.0f}%</b> de las vistas. Promedio {_n(lead['avg_views'])} vistas por pieza y el 25% mejor supera {_n(lead['p75_views'])}. "
        f"Su combinación más eficaz es <b>{fp} · {fk}</b> (mediana {_n(fmt_row['med_views'])} vistas) con ángulo <b>{escape(top_hook)}</b>. "
        f"Pieza de referencia: {_q(top_piece['title'])} con {_n(top_piece['views'])} vistas. "
        f"Genera {lead['avg_debate']:.1f} comentarios por cada 1.000 vistas y {_n(sv_t)} compartidos/guardados.",
    )

    # --- Temas sub-explotados -------------------------------------------------
    under = topic_df[topic_df["quadrant"] == UNDEREXPLOITED].head(3)
    if under.empty:
        add(
            "Temas sub-explotados",
            "info",
            "No hay temas claramente sub-explotados: lo que mejor rinde ya recibe un volumen proporcional de piezas.",
        )
    else:
        items = []
        for _, r in under.iterrows():
            s = df[df["topic"] == r["topic"]].sort_values("views", ascending=False).iloc[0]
            items.append(
                f"<b>{escape(r['topic'])}</b> ({r['perf_score']:.2f}x; {int(r['pieces'])} piezas = {r['share_volume']:.0f}% del esfuerzo, "
                f"pero {r['share_views']:.0f}% de las vistas; referencia: {_q(s['title'], 70)}, {_n(s['views'])} vistas)"
            )
        add(
            "Temas sub-explotados: dar más pauta",
            "ok",
            "Rinden por encima del promedio con poco espacio en la parrilla: " + "; ".join(items) + ".",
        )

    # --- Fatiga o sobreproducción --------------------------------------------
    fat = topic_df[topic_df["quadrant"] == FATIGUE]
    if fat.empty:
        fat = topic_df[(topic_df["perf_score"] < 1.0) & (topic_df["share_volume"] >= topic_df["share_volume"].median())]
    if fat.empty:
        add("Fatiga y sobreproducción", "ok", "Sin señales de fatiga: ningún tema de alto volumen rinde por debajo del promedio del canal.")
    else:
        r = fat.sort_values("share_volume", ascending=False).iloc[0]
        add(
            f"Fatiga de volumen en: {r['topic']}",
            "warn",
            f"Absorbe el <b>{r['share_volume']:.0f}%</b> de las piezas ({int(r['pieces'])}) pero rinde <b>{r['perf_score']:.2f}x</b> "
            f"y aporta el {r['share_views']:.0f}% de las vistas. Conviene publicar menos piezas de este tema y más selectivas "
            "(ángulos de cruce, polémica o protagonistas calientes) en lugar de repetir cobertura.",
        )

    # --- Protagonistas --------------------------------------------------------
    if not entity_df.empty:
        top_e = entity_df.head(4)
        listed = "; ".join(
            f"<b>{escape(r['entities'])}</b> ({r['perf_score']:.2f}x, {int(r['pieces'])} piezas, {_n(r['avg_views'])} vistas prom.)"
            for _, r in top_e.iterrows()
        )
        extra = []
        deb = entity_df.sort_values("avg_debate", ascending=False).iloc[0]
        extra.append(f"Mayor debate: <b>{escape(deb['entities'])}</b> con {deb['avg_debate']:.1f} comentarios por cada 1.000 vistas")
        weak = entity_df[(entity_df["pieces"] >= 4) & (entity_df["perf_score"] < 0.9)].sort_values("perf_score").head(1)
        if not weak.empty:
            w = weak.iloc[0]
            extra.append(f"posible desgaste en <b>{escape(w['entities'])}</b> ({w['perf_score']:.2f}x tras {int(w['pieces'])} piezas)")
        add("Protagonistas y conceptos calientes", "ok", f"Mueven más audiencia que el promedio: {listed}. " + "; ".join(extra) + ".")

    # --- Ángulos de titulación -----------------------------------------------
    ht = _hook_table(df)
    if len(ht) >= 2:
        listed = "; ".join(
            f"<b>{escape(k)}</b>: {int(r.n)} piezas, mediana {r.med:.2f}x, {r.debate:.1f} com/1K" for k, r in ht.iterrows()
        )
        best, worst = ht.index[0], ht.index[-1]
        add(
            "Ángulos de titulación",
            "info",
            f"{listed}. El ángulo más eficaz es <b>{escape(best)}</b> y el más débil <b>{escape(worst)}</b> "
            f"(brecha de {ht.iloc[0]['med'] - ht.iloc[-1]['med']:.2f}x en la mediana). "
            "Clasificación automática según palabras del titular; úsala como orientación, no como regla.",
        )

    # --- Programas de YouTube -------------------------------------------------
    yt = df[df["platform"] == "YouTube"]
    if not yt.empty:
        prog = (
            yt.groupby("program")
            .agg(n=("views", "count"), avg=("views", "mean"), med=("perf_index", "median"))
            .sort_values("avg", ascending=False)
        )
        prog = prog[prog.index.isin(MAIN_PROGRAMS + ["Shorts / Clips YT"])]
        if not prog.empty:
            listed = []
            for k, r in prog.iterrows():
                best = yt[yt["program"] == k].sort_values("views", ascending=False).iloc[0]
                listed.append(
                    f"<b>{escape(k)}</b>: {int(r.n)} piezas, {_n(r.avg)} vistas prom. ({r.med:.2f}x); mejor: {_q(best['title'], 60)} ({_n(best['views'])})"
                )
            add("Programas y franjas en YouTube", "info", "; ".join(listed) + ".")

    # --- Horarios -------------------------------------------------------------
    hrs = _hours_by_platform(df)
    h_parts = []
    for p, d in hrs.items():
        if d["best"]:
            best = ", ".join(f"{_hour_label(h)} ({m:.2f}x, {c} piezas)" for h, m, c in d["best"])
            worst = ", ".join(f"{_hour_label(h)} ({m:.2f}x)" for h, m, _ in d["worst"])
            h_parts.append(f"<b>{p}</b> rinde mejor cuando se publica a las {best}; peor a las {worst}.")
    if h_parts:
        add("Mejores horarios de publicación", "info", " ".join(h_parts) + " Horas locales de subida; solo se consideran horas con al menos 3 piezas.")

    # --- Viralidad y debate ---------------------------------------------------
    big = df[df["views"] >= 5000]
    vir = big[(big["shares"] + big["saved"]) > 0].sort_values("virality_rate", ascending=False).head(3)
    deb = big.sort_values("debate_rate", ascending=False).head(3)
    v_parts = []
    if not vir.empty:
        v_parts.append(
            "Más compartidas/guardadas por vista: "
            + "; ".join(f"{_q(r['title'], 65)} ({r['virality_rate']:.1f}%)" for _, r in vir.iterrows())
            + "."
        )
    if not deb.empty:
        v_parts.append(
            "Más debate (comentarios por 1.000 vistas): "
            + "; ".join(f"{_q(r['title'], 65)} ({r['debate_rate']:.1f})" for _, r in deb.iterrows())
            + "."
        )
    if v_parts:
        add("Viralidad y conversación", "info", " ".join(v_parts))

    # --- Concentración y piezas flojas ---------------------------------------
    srt = df["views"].sort_values(ascending=False)
    top5 = srt.head(5).sum() / max(srt.sum(), 1) * 100
    k10 = max(int(np.ceil(len(srt) * 0.1)), 1)
    top10 = srt.head(k10).sum() / max(srt.sum(), 1) * 100
    low = float((df["perf_index"] < 0.5).mean() * 100)
    status = "warn" if top10 >= 50 else "info"
    add(
        "Dependencia de piezas virales",
        status,
        f"Las 5 piezas más vistas aportan el <b>{top5:.0f}%</b> de las vistas y el 10% superior ({k10} piezas) el <b>{top10:.0f}%</b>. "
        f"{low:.0f}% de las piezas rinde menos de la mitad de lo normal para su formato. "
        + (
            "El resultado depende de pocos golpes grandes: conviene sostener una base constante de piezas sólidas."
            if status == "warn"
            else "La audiencia está razonablemente repartida entre muchas piezas."
        ),
    )

    # --- Recomendación operativa ---------------------------------------------
    recs = []
    if bets:
        b = bets[0]
        recs.append(
            f"Apuesta principal: <b>{escape(b['topic'])}</b> en <b>{b['platform']} · {b['kind']}</b> con ángulo <b>{escape(b['hook'])}</b> "
            f"(proyección {_n(b['proj_low'])}–{_n(b['proj_high'])} vistas)."
        )
    if not under.empty:
        recs.append("Dar más pauta a: " + "; ".join(escape(t) for t in under["topic"]) + ".")
    if not fat.empty:
        recs.append(f"Reducir repetición en: {escape(fat.sort_values('share_volume', ascending=False).iloc[0]['topic'])}.")
    if not entity_df.empty:
        recs.append("Buscar ángulos con: " + "; ".join(escape(e) for e in entity_df.head(3)["entities"]) + ".")
    for p, d in hrs.items():
        if d["best"]:
            recs.append(f"Publicar lo importante de {p} cerca de las {_hour_label(d['best'][0][0])}.")
    if recs:
        add("Recomendación operativa", "ok", "<br>".join("• " + r for r in recs))

    return bullets


# ----------------------------------------------------------------------------
# 2. Informe para bot rastreador
# ----------------------------------------------------------------------------
_STOP = set(
    """
    para como pero porque sobre entre desde hasta cuando donde aunque tambien
    esta este estos estas esto esos esas ellos ellas cada tras ante bajo segun
    luego antes despues ahora hace hacia durante mientras tiene tienen tuvo
    fue fueron sera seran puede pueden debe deben haber habia hacer ser
    mas muy menos todo todos toda todas otro otra otros otras mismo misma
    quien quienes cual cuales cuanto cuantos
    turnoenvivo turnoam turnopm turnoz turno explica analiza analizamos repasa
    repasamos desmenuza responde arremete revela reveló dijo dice dicen
    segun nuevo nueva nuevos nuevas video short vivo
    """.split()
)


def _norm_kw(text: str) -> str:
    return analytics._norm(text)


def _topic_keywords(sub: pd.DataFrame, label: str, top: int = 8) -> list[str]:
    kws = []
    for name, rules in analytics.TOPIC_RULES:
        if analytics.TOPIC_LABELS.get(name, name) == label:
            kws = rules
            break
    if not kws or sub.empty:
        return []
    texts = [_norm_kw(f"{t}\n{f}") for t, f in zip(sub["title"].fillna(""), sub["full_text"].fillna(""))]
    counts = {kw: sum(1 for tx in texts if kw in tx) for kw in kws}
    ranked = [k for k, c in sorted(counts.items(), key=lambda kv: -kv[1]) if c > 0]
    return [k.strip() for k in ranked[:top]]


def _entity_terms(sub: pd.DataFrame, label: str, top: int = 5) -> list[str]:
    kws = next((r for name, r in analytics.ENTITY_RULES if name == label), [])
    if not kws or sub.empty:
        return []
    texts = [_norm_kw(f"{t}\n{f}") for t, f in zip(sub["title"].fillna(""), sub["full_text"].fillna(""))]
    counts = {kw: sum(1 for tx in texts if kw in tx) for kw in kws}
    ranked = [k for k, c in sorted(counts.items(), key=lambda kv: -kv[1]) if c > 0]
    return ranked[:top]


def _hot_terms(df: pd.DataFrame, top: int = 15) -> list[str]:
    hits = df[df["perf_index"] >= 1.3]
    counts: dict[str, int] = {}
    for title in hits["title"].fillna(""):
        seen = set()
        for w in re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9\-]{5,}", title):
            lw = _norm_kw(w)
            if lw in _STOP or lw.isdigit() or lw in seen:
                continue
            seen.add(lw)
            counts[lw] = counts.get(lw, 0) + 1
    return [w for w, c in sorted(counts.items(), key=lambda kv: -kv[1]) if c >= 2][:top]


def _priority(score: float) -> str:
    if score >= 1.2:
        return "ALTA"
    if score >= 0.95:
        return "MEDIA"
    return "BAJA"


def build_tracker_brief(
    df: pd.DataFrame,
    topic_df: pd.DataFrame,
    entity_df: pd.DataFrame,
    bets: list[dict],
    days: int,
    now_local: pd.Timestamp,
    timezone_str: str,
) -> tuple[str, dict]:
    """Devuelve (texto_plano, dict_json) con el informe para un bot rastreador."""
    if df.empty or topic_df.empty:
        return "", {}

    topics = []
    for _, r in topic_df.iterrows():
        sub = df[df["topic"] == r["topic"]]
        fmt_row, (fp, fk) = _best_format_for(sub)
        topics.append(
            {
                "tema": r["topic"],
                "prioridad": _priority(float(r["perf_score"])) if r["quadrant"] != FATIGUE else "BAJA",
                "diagnostico": r["quadrant"].split(" ", 1)[-1],
                "multiplicador": round(float(r["perf_score"]), 2),
                "piezas": int(r["pieces"]),
                "pct_esfuerzo": round(float(r["share_volume"]), 1),
                "pct_vistas": round(float(r["share_views"]), 1),
                "vistas_promedio": int(r["avg_views"]),
                "formato_ideal": f"{fp} · {fk}",
                "angulo_ideal": _hook_table(sub).index[0],
                "palabras_clave": _topic_keywords(sub, r["topic"]),
            }
        )

    entities = []
    for _, r in entity_df.head(10).iterrows():
        sub = df[df["entities"].apply(lambda e: r["entities"] in e)]
        entities.append(
            {
                "protagonista_o_concepto": r["entities"],
                "multiplicador": round(float(r["perf_score"]), 2),
                "piezas": int(r["pieces"]),
                "vistas_promedio": int(r["avg_views"]),
                "comentarios_por_mil_vistas": round(float(r["avg_debate"]), 1),
                "terminos_de_busqueda": _entity_terms(sub, r["entities"]),
            }
        )

    ht = _hook_table(df)
    angles = [
        {"angulo": k, "piezas": int(r.n), "multiplicador_mediano": round(float(r.med), 2), "comentarios_por_mil_vistas": round(float(r.debate), 1)}
        for k, r in ht.iterrows()
    ]

    formats = []
    fg = (
        df.groupby(["platform", "kind"])
        .agg(n=("views", "count"), med=("views", "median"))
        .sort_values("med", ascending=False)
        .head(6)
    )
    for (p, k), r in fg.iterrows():
        formats.append({"red": p, "formato": k, "piezas": int(r.n), "vistas_mediana": int(r.med)})

    hours = {
        p: [f"{_hour_label(h)} ({m:.2f}x)" for h, m, _ in d["best"]] for p, d in _hours_by_platform(df).items() if d["best"]
    }

    pool = df[df["age_hours"] >= 6]
    pool = pool if len(pool) >= 8 else df
    refs = [
        {
            "red": r["platform"],
            "formato": r["kind"],
            "titular": _short(r["title"], 140),
            "vistas": int(r["views"]),
            "multiplicador": round(float(r["perf_index"]), 2),
            "tema": r["topic"],
        }
        for _, r in pool.sort_values("perf_index", ascending=False).head(8).iterrows()
    ]

    already = [_short(t, 100) for t in df[df["age_hours"] <= 24].sort_values("published_at", ascending=False)["title"].head(12)]

    data = {
        "generado": f"{now_local:%Y-%m-%d %H:%M} ({timezone_str})",
        "ventana_analisis_dias": days,
        "piezas_analizadas": int(len(df)),
        "temas": topics,
        "protagonistas_calientes": entities,
        "angulos": angles,
        "formatos_fuertes": formats,
        "mejores_horarios": hours,
        "terminos_frecuentes_en_piezas_exitosas": _hot_terms(df),
        "piezas_de_referencia": refs,
        "ya_publicado_ultimas_24h": already,
    }

    # ---------------- texto plano ----------------
    L: list[str] = []
    L.append("INFORME DE RASTREO EDITORIAL — TURNO (@turnoenvivo)")
    L.append(f"Generado: {data['generado']} · Basado en {data['piezas_analizadas']} piezas de YouTube e Instagram de los últimos {days} días.")
    L.append("")
    L.append("CONTEXTO DEL MEDIO")
    L.append(
        "Turno es un canal chileno de streaming de noticias en vivo, política, debate y humor, con programas "
        "(Turno AM, Turno en Vivo, Turno PM, Turno Z) y contenido breve para Instagram y YouTube Shorts. "
        "Audiencia principal: Chile. Tono: análisis político directo, cultura pop y temas de conversación."
    )
    L.append(
        "Nota de lectura: «multiplicador» (x) = cuántas veces rinde un tema o pieza sobre la mediana de su mismo formato y red. "
        "1.00x es lo normal; sobre 1.20x es fuerte; bajo 0.90x es débil."
    )
    L.append("")
    L.append("TU MISIÓN")
    L.append(
        "Rastrea en internet noticias, declaraciones, polémicas, anuncios y tendencias recientes (idealmente de las últimas 24–48 horas) "
        "que calcen con los temas y protagonistas de este informe, para que el equipo de Turno decida qué cubrir hoy y mañana. "
        "Prioriza Chile; incluye hechos internacionales solo si afectan a Chile o a los protagonistas listados."
    )
    L.append("")
    L.append("1) TEMAS A RASTREAR (de mayor a menor prioridad)")
    for i, t in enumerate(topics, 1):
        L.append(
            f"{i}. {t['tema']} — prioridad {t['prioridad']} ({t['diagnostico']}; {t['multiplicador']:.2f}x; "
            f"{t['piezas']} piezas = {t['pct_esfuerzo']:.0f}% del esfuerzo → {t['pct_vistas']:.0f}% de las vistas)"
        )
        L.append(f"   Formato que mejor funciona: {t['formato_ideal']} · Ángulo: {t['angulo_ideal']}")
        if t["palabras_clave"]:
            L.append(f"   Palabras clave de búsqueda: {', '.join(t['palabras_clave'])}")
    L.append("")
    L.append("2) PROTAGONISTAS Y CONCEPTOS CALIENTES (buscar noticias recientes sobre ellos)")
    for e in entities:
        terms = f" · búsqueda: {', '.join(e['terminos_de_busqueda'])}" if e["terminos_de_busqueda"] else ""
        L.append(
            f"- {e['protagonista_o_concepto']}: {e['multiplicador']:.2f}x, {e['piezas']} piezas, "
            f"{_n(e['vistas_promedio'])} vistas prom., {e['comentarios_por_mil_vistas']:.1f} comentarios/1K vistas{terms}"
        )
    L.append("")
    sub_topics = [t["tema"] for t in topics if t["diagnostico"].startswith("Oportunidad")]
    fat_topics = [t["tema"] for t in topics if t["diagnostico"].startswith("Alerta")]
    L.append("3) PRIORIDADES ESPECIALES")
    L.append("- Temas sub-explotados (buscar con más intensidad): " + ("; ".join(sub_topics) if sub_topics else "ninguno destacado"))
    L.append("- Temas saturados (buscar solo hechos nuevos o ángulos distintos): " + ("; ".join(fat_topics) if fat_topics else "ninguno destacado"))
    L.append("")
    L.append("4) QUÉ TIPO DE CONTENIDO FUNCIONA (para elegir los hallazgos)")
    for a in angles:
        L.append(f"- Ángulo «{a['angulo']}»: {a['multiplicador_mediano']:.2f}x mediano, {a['comentarios_por_mil_vistas']:.1f} comentarios/1K vistas")
    for f in formats[:4]:
        L.append(f"- {f['red']} · {f['formato']}: mediana de {_n(f['vistas_mediana'])} vistas ({f['piezas']} piezas)")
    if hours:
        L.append("- Mejores horas de publicación: " + "; ".join(f"{p}: {', '.join(v)}" for p, v in hours.items()))
    L.append("")
    L.append("5) EJEMPLOS DE PIEZAS QUE FUNCIONARON (busca hechos de la misma naturaleza)")
    for r in refs:
        L.append(f"- [{r['red']} · {r['formato']}] «{r['titular']}» — {_n(r['vistas'])} vistas ({r['multiplicador']:.2f}x) · {r['tema']}")
    terms = data["terminos_frecuentes_en_piezas_exitosas"]
    if terms:
        L.append("")
        L.append("6) TÉRMINOS FRECUENTES EN TITULARES EXITOSOS: " + ", ".join(terms))
    if already:
        L.append("")
        L.append("7) YA PUBLICADO EN LAS ÚLTIMAS 24 H (no lo propongas de nuevo salvo que haya un hecho nuevo)")
        for t in already:
            L.append(f"- {t}")
    L.append("")
    L.append("CÓMO RESPONDER")
    L.append("- Entrega hasta 15 hallazgos ordenados por prioridad, de lo más urgente a lo menos.")
    L.append(
        "- Para cada uno: titular; fuente y URL; fecha y hora de publicación; tema (de la lista 1); protagonista (de la lista 2); "
        "por qué calza con lo que funciona en Turno; formato y ángulo sugeridos; urgencia (cubrir hoy / esta semana)."
    )
    L.append("- Criterios para priorizar: recencia (menos de 48 h), potencial de debate o conflicto, protagonista caliente, posibilidad de cubrirlo en vivo.")
    L.append("- Verifica los hechos y cita la fuente original. Distingue claramente entre información confirmada, rumor y opinión. No inventes datos ni URLs.")
    L.append("- Si no encuentras nada relevante para un tema, dilo en vez de forzar un resultado.")

    return "\n".join(L), data
