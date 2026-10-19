"""Motor de Inteligencia Editorial, Diagnósticos y Proyecciones Temáticas para Turno."""
from __future__ import annotations

import re
import unicodedata
import numpy as np
import pandas as pd


def _norm(text: str) -> str:
    text = (text or "").lower()
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")


TOPIC_RULES: list[tuple[str, list[str]]] = [
    (
        "Memoria, 18-O y DD.HH.",
        [
            "estallido", "18-o", "18 de octubre", "lesa humanidad", "dd.hh", "ddhh",
            "derechos humanos", "amnistia", "convencion constitucional", "torturador",
            "indulto", "cal y canto", "violencia politica", "historia de chile", "tranvia",
        ],
    ),
    (
        "Justicia, Casos y Seguridad",
        [
            "hermosilla", "vivanco", "migueles", "caso audios", "corte suprema",
            "corte de apelaciones", "juez", "ulloa", "ciper", "fiscalia", "delincuencia",
            "crimen", "carcel", "corrupcion", "chadwick",
        ],
    ),
    (
        "Internacional y Geopolitica",
        [
            "milei", "argentina", "lula", "bolsonaro", "brasil", "bukele", "el salvador",
            "trump", "estados unidos", "israel", "palestina", "antisemitismo", "bolivia",
            "la paz", "peru", "venezuela", "pedro sanchez", "america latina", "latinoamerica",
            "norteamerica", "espanoles",
        ],
    ),
    (
        "Cultura, Musica y Espectaculos",
        [
            "lollapalooza", "isabel allende", "premio planeta", "coco legrand",
            "quintanilla", "fuenzalida", "implante capilar", "bts", "the strokes",
            "roger waters", "metallica", "hetfield", "bad gyal", "taylor swift",
            "pelicula", "tom cruise", "digger", "musical", "nicolas saavedra",
            "premios cordillera", "hitster", "roce de mente", "musica chilena",
        ],
    ),
    (
        "Economia, Ciudad y Bolsillo",
        [
            "afp", "pension", "hacienda", "presupuesto", "inflacion", "empleo",
            "transporte", "rebajas de tag", "cobro de tag", "vivienda", "poduje", "urbanismo",
            "ues estatales", "universidades", "recortes", "6.000 millones", "dolares",
        ],
    ),
    (
        "Política Nacional y Gobierno",
        [
            "kast", "boric", "bachelet", "la moneda", "gobierno", "senado", "congreso",
            "oficialismo", "oposicion", "pancho vidal", "vidal", "toha", "squella",
            "paulina nunez", "carmona", "kaiser", "matthei", "partido republicano",
            "partido comunista", "partido nacional libertario", "ultraderecha",
            "progresismo", "derecha", "izquierda", "elecciones", "candidatura", "rovira",
            "mayol", "conclave", "cumbre",
        ],
    ),
    (
        "Sociedad, Tendencias y Viral",
        [
            "tarot", "sammy", "ovni", "apocalipsis", "el nino", "cambio climatico",
            "clima", "cancer", "oncologa", "tesla", "roadster", "fifa", "futbol",
            "derrumbe", "lota", "perro", "calvicie", "portadas", "buenos dias", "granizo", "temporal",
        ],
    ),
]

TOPIC_LABELS = {
    "Internacional y Geopolitica": "Internacional y Geopolítica",
    "Cultura, Musica y Espectaculos": "Cultura, Música y Espectáculos",
    "Economia, Ciudad y Bolsillo": "Economía, Ciudad y Bolsillo",
}

ENTITY_RULES: list[tuple[str, list[str]]] = [
    ("Estallido Social / 18-O", ["estallido", "18-o", "18 de octubre", "cal y canto"]),
    ("Boric / Bachelet / Oficialismo", ["boric", "bachelet", "toha", "oficialismo", "progresismo"]),
    ("J.A. Kast / Derecha y Republicanos", ["kast", "squella", "republicano", "kaiser", "ultraderecha", "libertario"]),
    ("Pancho Vidal", ["vidal"]),
    ("Alberto Mayol", ["mayol"]),
    ("Javier Milei / Argentina", ["milei", "argentina"]),
    ("Brasil (Lula / Bolsonaro / Strokes)", ["lula", "bolsonaro", "brasil", "the strokes"]),
    ("Bukele / El Salvador", ["bukele", "el salvador"]),
    ("Caso Audios / Vivanco / Hermosilla", ["vivanco", "hermosilla", "migueles", "ulloa", "chadwick"]),
    ("Cultura Pop y Música (BTS, Waters, Swift)", ["bts", "roger waters", "metallica", "bad gyal", "taylor swift", "lollapalooza", "roce de mente", "hitster"]),
    ("TV y Figuras Chilenas (Quintanilla, Legrand, Huevo)", ["quintanilla", "coco legrand", "fuenzalida", "isabel allende", "nicolas saavedra"]),
    ("Economía, AFP y Ciudad", ["afp", "hacienda", "presupuesto", "vivienda", "poduje", "transporte", "rebajas de tag"]),
    ("Sammy Tarot / Fenómenos Pop", ["sammy", "tarot", "ovni", "apocalipsis"]),
]


def classify_topic(title: str, full_text: str) -> str:
    # El titular pesa el triple que el cuerpo para que el tema central mande
    norm_title = _norm(title)
    norm_body = _norm(full_text)
    best_topic = "Política Nacional y Gobierno"
    best_score = 0
    for topic, keywords in TOPIC_RULES:
        score = sum(3 for kw in keywords if kw in norm_title) + sum(1 for kw in keywords if kw in norm_body)
        if score > best_score:
            best_score = score
            best_topic = topic
    if best_score == 0:
        return "Sociedad, Tendencias y Viral"
    return TOPIC_LABELS.get(best_topic, best_topic)


def classify_program(text: str, platform: str, kind: str) -> str:
    norm = _norm(text)
    if "#turnoam" in norm or "turno am" in norm:
        return "Turno AM"
    if "#turnopm" in norm or "turno pm" in norm:
        return "Turno PM"
    if "#turnoz" in norm or "turno z" in norm:
        return "Turno Z"
    if "#turnoenvivo" in norm or "turno en vivo" in norm:
        return "Turno en Vivo"
    if platform == "YouTube" and kind == "Short":
        return "Shorts / Clips YT"
    if platform == "Instagram":
        return "Prensa / Feed IG"
    return "General / Otros"


def classify_hook(title: str) -> str:
    norm = _norm(title)
    polemic_words = [
        "arremete", "cuestion", "critica", "polemica", "cringe", "traicion",
        "sin filtro", "responde", "contra", "cruce", "evita", "dañar", "furia",
    ]
    explain_words = [
        "explica", "analiza", "desmenuza", "por que", "claves", "historia",
        "repasa", "lecciones", "como ", "que dejo", "que implicaria",
    ]
    if any(w in norm for w in polemic_words):
        return "Polémica / Cruce"
    if any(w in norm for w in explain_words):
        return "Explicativo / Análisis"
    if "¿" in title or "?" in title:
        return "Pregunta / Debate"
    return "Informativo / Directo"


def extract_entities(text: str) -> list[str]:
    norm = _norm(text)
    found = [label for label, kws in ENTITY_RULES if any(kw in norm for kw in kws)]
    return found or ["Agenda General"]


def enrich_dataframe(df: pd.DataFrame, now_local: pd.Timestamp, timezone_str: str) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    out = df.copy()
    out["published_local"] = out["published_at"].dt.tz_convert(timezone_str)
    out["date_str"] = out["published_local"].dt.strftime("%d/%m")
    out["day_date"] = out["published_local"].dt.floor("D")
    out["hour"] = out["published_local"].dt.hour

    now_utc = now_local.tz_convert("UTC")
    age_h = (now_utc - out["published_at"]).dt.total_seconds() / 3600.0
    out["age_hours"] = age_h.clip(lower=0.5)
    # Velocidad efectiva en las primeras 72 horas
    out["views_per_hour"] = (out["views"] / out["age_hours"].clip(upper=72.0)).round(0)

    out["interactions"] = out["likes"] + out["comments"] + out["shares"] + out["saved"]
    views_safe = out["views"].replace(0, np.nan)
    out["engagement_rate"] = ((out["interactions"] / views_safe) * 100.0).fillna(0.0).round(2)
    out["virality_rate"] = (((out["shares"] + out["saved"]) / views_safe) * 100.0).fillna(0.0).round(2)
    out["debate_rate"] = ((out["comments"] / views_safe) * 1000.0).fillna(0.0).round(2)

    # Mediana por (plataforma, formato) para comparar manzanas con manzanas
    medians = out.groupby(["platform", "kind"])["views"].transform(lambda s: max(float(s.median()), 100.0))
    out["baseline_views"] = medians
    out["perf_index"] = (out["views"] / out["baseline_views"]).round(2)

    titles = out["title"].fillna("")
    full_txt = out.get("full_text", titles).fillna("")
    out["topic"] = [classify_topic(ti, ft) for ti, ft in zip(titles, full_txt)]
    out["program"] = [classify_program(ti + "\n" + ft, p, k) for ti, ft, p, k in zip(titles, full_txt, out["platform"], out["kind"])]
    out["hook_type"] = [classify_hook(ti) for ti in titles]
    out["entities"] = [extract_entities(ti + "\n" + ft) for ti, ft in zip(titles, full_txt)]
    return out


def compute_topic_diagnostics(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    total_pieces = max(len(df), 1)
    total_views = max(int(df["views"].sum()), 1)
    channel_mean_perf = max(float(df["perf_index"].mean()), 0.01)
    channel_med_perf = max(float(df["perf_index"].median()), 0.01)

    grouped = (
        df.groupby("topic", as_index=False)
        .agg(
            pieces=("views", "count"),
            total_views=("views", "sum"),
            avg_views=("views", "mean"),
            p75_views=("views", lambda s: float(np.percentile(s, 75))),
            median_perf=("perf_index", lambda s: float(s.median()) / channel_med_perf),
            mean_perf=("perf_index", lambda s: float(s.mean()) / channel_mean_perf),
            avg_eng=("engagement_rate", "mean"),
            avg_debate=("debate_rate", "mean"),
            total_shares=("shares", "sum"),
            total_saved=("saved", "sum"),
        )
    )
    grouped["share_volume"] = (grouped["pieces"] / total_pieces * 100.0).round(1)
    grouped["share_views"] = (grouped["total_views"] / total_views * 100.0).round(1)
    grouped["perf_score"] = ((grouped["median_perf"] * 0.55) + (grouped["mean_perf"] * 0.45)).round(2)
    # Brecha de eficiencia normalizada por plataforma/formato
    norm_share = (grouped["pieces"] * grouped["perf_score"]) / max(float((grouped["pieces"] * grouped["perf_score"]).sum()), 1.0) * 100.0
    grouped["efficiency_gap"] = (norm_share - grouped["share_volume"]).round(1)
    grouped["avg_views"] = grouped["avg_views"].round(0).astype(int)
    grouped["p75_views"] = grouped["p75_views"].round(0).astype(int)

    med_vol = float(grouped["share_volume"].median())

    def _quadrant(row) -> str:
        score = row["perf_score"]
        vol = row["share_volume"]
        if score >= 1.05 and vol >= med_vol:
            return "🌟 Motor de Audiencia"
        if score >= 1.05 and vol < med_vol:
            return "🚀 Oportunidad Sub-explotada"
        if score < 0.92 and vol >= med_vol:
            return "⚠️ Alerta de Fatiga"
        return "⚖️ Pilar Estable"

    grouped["quadrant"] = grouped.apply(_quadrant, axis=1)
    return grouped.sort_values("perf_score", ascending=False).reset_index(drop=True)


def compute_entity_ranking(df: pd.DataFrame, min_pieces: int = 2) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    channel_mean_perf = max(float(df["perf_index"].mean()), 0.01)
    channel_med_perf = max(float(df["perf_index"].median()), 0.01)
    exploded = df.explode("entities")
    exploded = exploded[exploded["entities"] != "Agenda General"]
    if exploded.empty:
        return pd.DataFrame()

    agg = (
        exploded.groupby("entities", as_index=False)
        .agg(
            pieces=("views", "count"),
            total_views=("views", "sum"),
            avg_views=("views", "mean"),
            median_perf=("perf_index", lambda s: float(s.median()) / channel_med_perf),
            mean_perf=("perf_index", lambda s: float(s.mean()) / channel_mean_perf),
            avg_eng=("engagement_rate", "mean"),
            avg_debate=("debate_rate", "mean"),
            best_title=("title", lambda s: s.iloc[0]),
        )
    )
    agg = agg[agg["pieces"] >= min_pieces].copy()
    agg["perf_score"] = ((agg["median_perf"] * 0.5) + (agg["mean_perf"] * 0.5)).round(2)
    agg["avg_views"] = agg["avg_views"].round(0).astype(int)
    return agg.sort_values(["perf_score", "total_views"], ascending=False).reset_index(drop=True)


def generate_projections_and_actions(df: pd.DataFrame, topic_df: pd.DataFrame, entity_df: pd.DataFrame) -> dict:
    """Genera proyecciones de pauta (apuestas) y cruces pendientes entre YT e IG. El diagnóstico ejecutivo vive en insights.py."""
    result = {
        "recommended_bets": [],
        "cross_platform_gaps": [],
    }
    if df.empty or topic_df.empty:
        return result

    # 2. Proyecciones temáticas (Apuestas recomendadas para las próximas 24-48h)
    candidates = topic_df[topic_df["perf_score"] >= 1.0].head(3)
    if candidates.empty:
        candidates = topic_df.head(3)

    for _, trow in candidates.iterrows():
        t_name = trow["topic"]
        sub = df[df["topic"] == t_name]
        # Mejor formato para este tema
        fmt_grp = sub.groupby(["platform", "kind"], as_index=False).agg(
            n=("views", "count"), perf=("perf_index", "mean"), p50=("views", "median"), p85=("views", lambda s: float(np.percentile(s, 85)))
        ).sort_values("perf", ascending=False)
        best_fmt = fmt_grp.iloc[0]
        # Mejor ángulo para este tema
        best_hook = sub.groupby("hook_type")["perf_index"].mean().idxmax()
        # Ejemplo real más exitoso
        top_example = sub.sort_values("views", ascending=False).iloc[0]

        low_proj = int(max(best_fmt["p50"], 1000))
        high_proj = int(max(best_fmt["p85"], low_proj * 1.4))

        result["recommended_bets"].append(
            {
                "topic": t_name,
                "quadrant": trow["quadrant"],
                "platform": best_fmt["platform"],
                "kind": best_fmt["kind"],
                "hook": best_hook,
                "mult": float(trow["perf_score"]),
                "proj_low": low_proj,
                "proj_high": high_proj,
                "example_title": top_example["title"],
                "example_views": int(top_example["views"]),
            }
        )

    # 3. Oportunidades de reciclaje / cruce entre plataformas (hits en IG que no están en YT o viceversa)
    recent_hits = df[df["perf_index"] >= 1.6].sort_values("perf_index", ascending=False)
    for _, hit in recent_hits.head(8).iterrows():
        other_plat = "YouTube" if hit["platform"] == "Instagram" else "Instagram"
        other_df = df[df["platform"] == other_plat]
        hit_ents = set(hit["entities"]) - {"Agenda General"}
        # Ver si el mismo tema/entidad tuvo un hit reciente en la otra plataforma
        overlap = False
        if hit_ents and not other_df.empty:
            for ents in other_df[other_df["perf_index"] >= 1.3]["entities"]:
                if hit_ents.intersection(ents):
                    overlap = True
                    break
        if not overlap:
            target_fmt = "Short o Corte de #TurnoEnVivo" if other_plat == "YouTube" else "Carrusel o Reel de impacto"
            result["cross_platform_gaps"].append(
                {
                    "from_platform": hit["platform"],
                    "from_kind": hit["kind"],
                    "to_platform": other_plat,
                    "to_format": target_fmt,
                    "title": hit["title"],
                    "views": int(hit["views"]),
                    "perf_index": float(hit["perf_index"]),
                    "topic": hit["topic"],
                    "url": hit["url"],
                }
            )
        if len(result["cross_platform_gaps"]) >= 4:
            break

    return result
