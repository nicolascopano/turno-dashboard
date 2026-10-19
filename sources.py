"""Obtención de datos: YouTube Data API v3, Instagram Graph API y modo DEMO.

Devuelve un DataFrame estandarizado con columnas:
platform, kind, title, full_text, url, thumbnail, published_at (UTC),
views, reach, likes, comments, shares, saved, duration_sec
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import random
import re

import pandas as pd
import requests

import config

COLUMNS = [
    "platform",
    "kind",
    "title",
    "full_text",
    "url",
    "thumbnail",
    "published_at",
    "views",
    "reach",
    "likes",
    "comments",
    "shares",
    "saved",
    "duration_sec",
]

YT = "https://www.googleapis.com/youtube/v3"
IG = "https://graph.instagram.com/v21.0"


def _empty() -> pd.DataFrame:
    return pd.DataFrame(columns=COLUMNS)


def _duration_seconds(iso: str) -> int:
    m = re.fullmatch(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    if not m:
        return 0
    h, mi, s = (int(x or 0) for x in m.groups())
    return h * 3600 + mi * 60 + s


def _extract_error_message(r: requests.Response) -> str:
    try:
        data = r.json()
        if isinstance(data, dict):
            err = data.get("error")
            if isinstance(err, dict):
                return str(err.get("message") or err)
            if err:
                return str(err)
            return str(data.get("message") or data)
        return str(data)
    except Exception:
        return r.text.strip() or f"HTTP {r.status_code}"


def _yt_get(endpoint: str, **params) -> dict:
    params["key"] = config.YOUTUBE_API_KEY
    r = requests.get(f"{YT}/{endpoint}", params=params, timeout=20)
    if r.status_code != 200:
        msg = _extract_error_message(r)
        raise RuntimeError(f"YouTube respondió {r.status_code}: {msg}")
    try:
        return r.json()
    except Exception as e:
        raise RuntimeError(f"Error parseando respuesta de YouTube: {e} ({r.text[:100]})")


def fetch_account_summary() -> dict:
    """Trae seguidores/suscriptores totales de YouTube e Instagram."""
    summary = {"yt_subs": None, "yt_views": None, "ig_followers": None, "ig_posts": None}
    if config.YOUTUBE_API_KEY:
        try:
            handle = config.YOUTUBE_HANDLE.lstrip("@")
            ch = _yt_get("channels", part="statistics", forHandle=handle)
            if ch.get("items"):
                st = ch["items"][0].get("statistics", {})
                summary["yt_subs"] = int(st.get("subscriberCount", 0))
                summary["yt_views"] = int(st.get("viewCount", 0))
        except Exception:
            pass
    if config.INSTAGRAM_ACCESS_TOKEN:
        try:
            r = requests.get(
                f"{IG}/me",
                params={"fields": "username,followers_count,media_count", "access_token": config.INSTAGRAM_ACCESS_TOKEN},
                timeout=15,
            )
            if r.status_code == 200:
                d = r.json()
                summary["ig_followers"] = int(d.get("followers_count", 0))
                summary["ig_posts"] = int(d.get("media_count", 0))
        except Exception:
            pass
    return summary


def fetch_youtube(max_videos: int = 200) -> pd.DataFrame:
    """Últimos videos del canal (hasta 200 piezas = ~10 días de historial completo)."""
    if not config.YOUTUBE_API_KEY:
        return _empty()
    handle = config.YOUTUBE_HANDLE.lstrip("@")
    ch = _yt_get("channels", part="contentDetails", forHandle=handle)
    if not ch.get("items"):
        raise RuntimeError(f"No encontré el canal @{handle} en YouTube.")
    uploads = ch["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

    video_ids: list[str] = []
    page_token = None
    pages = max(1, (max_videos + 49) // 50)
    for _ in range(pages):
        params = {"part": "contentDetails", "playlistId": uploads, "maxResults": min(50, max_videos - len(video_ids))}
        if page_token:
            params["pageToken"] = page_token
        res = _yt_get("playlistItems", **params)
        video_ids.extend(i["contentDetails"]["videoId"] for i in res.get("items", []))
        page_token = res.get("nextPageToken")
        if not page_token or len(video_ids) >= max_videos:
            break

    if not video_ids:
        return _empty()

    chunks = [video_ids[i : i + 50] for i in range(0, len(video_ids), 50)]
    with ThreadPoolExecutor(max_workers=4) as pool:
        batch_results = list(
            pool.map(
                lambda c: _yt_get("videos", part="snippet,statistics,contentDetails,liveStreamingDetails", id=",".join(c)).get("items", []),
                chunks,
            )
        )
    videos = [v for batch in batch_results for v in batch]

    rows = []
    for v in videos:
        sn, st = v["snippet"], v.get("statistics", {})
        dur = _duration_seconds(v.get("contentDetails", {}).get("duration", ""))
        if "liveStreamingDetails" in v:
            kind = "En vivo"
        elif dur <= 180:
            kind = "Short"
        else:
            kind = "Video"
        thumbs = sn.get("thumbnails", {})
        thumb = (thumbs.get("high") or thumbs.get("medium") or thumbs.get("default") or {}).get("url", "")
        title = sn.get("title", "").strip()
        raw_desc = sn.get("description", "").strip()
        clean_desc = raw_desc.split("TURNO es el canal")[0].split("🗓️ Programación")[0].strip()
        views = int(st.get("viewCount", 0))
        rows.append(
            {
                "platform": "YouTube",
                "kind": kind,
                "title": title,
                "full_text": f"{title}\n{clean_desc}",
                "url": f"https://www.youtube.com/watch?v={v['id']}",
                "thumbnail": thumb,
                "published_at": pd.to_datetime(sn["publishedAt"], utc=True),
                "views": views,
                "reach": views,
                "likes": int(st.get("likeCount", 0)),
                "comments": int(st.get("commentCount", 0)),
                "shares": 0,
                "saved": 0,
                "duration_sec": dur,
            }
        )
    return pd.DataFrame(rows, columns=COLUMNS)


def _parse_ig_insights(item: dict) -> dict[str, int]:
    out = {"views": 0, "reach": 0, "saved": 0, "shares": 0}
    ins_data = item.get("insights", {}).get("data", [])
    for metric in ins_data:
        name = metric.get("name")
        vals = metric.get("values") or []
        if name in out and vals:
            try:
                out[name] = int(vals[0].get("value", 0) or 0)
            except Exception:
                pass
    return out


def fetch_instagram(limit: int = 150) -> pd.DataFrame:
    """Instagram API con métricas completas (views, reach, saved, shares) en 1-2 llamadas rápidas."""
    if not config.INSTAGRAM_ACCESS_TOKEN:
        return _empty()

    fields_with_insights = (
        "id,caption,media_type,media_product_type,media_url,thumbnail_url,"
        "permalink,timestamp,like_count,comments_count,insights.metric(views,reach,saved,shares)"
    )
    items: list[dict] = []
    next_url = f"{IG}/me/media"
    params: dict | None = {
        "fields": fields_with_insights,
        "limit": min(100, limit),
        "access_token": config.INSTAGRAM_ACCESS_TOKEN,
    }

    while next_url and len(items) < limit:
        r = requests.get(next_url, params=params, timeout=25)
        if r.status_code != 200:
            msg = _extract_error_message(r)
            raise RuntimeError(f"Instagram respondió {r.status_code}: {msg}")
        try:
            payload = r.json()
        except Exception as e:
            raise RuntimeError(f"Error parseando respuesta de Instagram: {e} ({r.text[:100]})")
        batch = payload.get("data", [])
        items.extend(batch)
        next_url = payload.get("paging", {}).get("next")
        params = None  # next_url ya incluye los query params
        if not batch:
            break

    items = items[:limit]
    rows = []
    for m in items:
        if m.get("media_product_type") == "REELS":
            kind = "Reel"
        elif m.get("media_type") == "CAROUSEL_ALBUM":
            kind = "Carrusel"
        elif m.get("media_product_type") == "STORY":
            kind = "Historia"
        else:
            kind = "Post"

        caption = (m.get("caption") or "").strip()
        first_line = next((ln.strip() for ln in caption.splitlines() if ln.strip()), "(sin texto)")[:140]
        ins = _parse_ig_insights(m)
        views = ins["views"] or ins["reach"]
        rows.append(
            {
                "platform": "Instagram",
                "kind": kind,
                "title": first_line,
                "full_text": caption,
                "url": m.get("permalink", ""),
                "thumbnail": m.get("thumbnail_url") or m.get("media_url", ""),
                "published_at": pd.to_datetime(m["timestamp"], utc=True),
                "views": views,
                "reach": ins["reach"] or views,
                "likes": int(m.get("like_count", 0)),
                "comments": int(m.get("comments_count", 0)),
                "shares": ins["shares"],
                "saved": ins["saved"],
                "duration_sec": 0,
            }
        )
    return pd.DataFrame(rows, columns=COLUMNS)


def demo_data() -> pd.DataFrame:
    """Datos de ejemplo realistas para probar el dashboard sin credenciales."""
    rnd = random.Random(42)
    now = datetime.now(timezone.utc)
    samples = [
        ("Es momento de hablarlo: El Estallido Social dio un poco de cringe #TurnoZ", "Instagram", "Carrusel", 280000),
        ("¿Qué DEJÓ el ESTALLIDO? Pancho Vidal EXPLICA las LECCIONES a 7 AÑOS del 18-O | #TurnoEnVivo", "YouTube", "Video", 21500),
        ("🎤 María José Quintanilla respondió a la polémica en televisión", "Instagram", "Reel", 155000),
        ("¿ALIANZA para DAÑAR a CHILE? Vidal RESPONDE a CRÍTICAS de SQUELLA a BACHELET y BORIC | #TurnoEnVivo", "YouTube", "Video", 23000),
        ("📚 La escritora chilena Isabel Allende ganó el Premio Planeta de Novela", "Instagram", "Reel", 86000),
        ("🇦🇷 Javier Milei lanzó duras críticas contra Lula da Silva en Brasil", "Instagram", "Reel", 42000),
        ("¿Por qué MIGUELES traicionó a VIVANCO? Paulina Toro de CIPER lo EXPLICA | #TurnoEnVivo", "YouTube", "Video", 28400),
        ("📉 ¿Cómo el fondo más seguro de las AFP terminó perdiendo más del 10%? #TurnoAM", "Instagram", "Reel", 31000),
        ("¡Especial 7 AÑOS del 18-O! ¿La DERECHA está en CONTRA de la VIOLENCIA? | #TurnoAM", "YouTube", "En vivo", 19500),
        ("🇨🇱 El presidente José Antonio Kast en visita oficial a Bolivia", "Instagram", "Carrusel", 18000),
    ]
    rows = []
    for i in range(80):
        base_title, platform, kind, base_views = samples[i % len(samples)]
        age_h = i * rnd.uniform(1.5, 2.6)
        views = int(base_views * rnd.uniform(0.55, 1.45))
        likes = int(views * rnd.uniform(0.02, 0.08))
        comments = int(views * rnd.uniform(0.002, 0.015))
        shares = int(views * rnd.uniform(0.004, 0.03)) if platform == "Instagram" else 0
        saved = int(views * rnd.uniform(0.002, 0.015)) if platform == "Instagram" else 0
        rows.append(
            {
                "platform": platform,
                "kind": kind,
                "title": base_title,
                "full_text": base_title,
                "url": "https://www.youtube.com/@turnoenvivo" if platform == "YouTube" else "https://www.instagram.com/turnoenvivo/",
                "thumbnail": f"https://picsum.photos/seed/tev{i}/480/270",
                "published_at": now - timedelta(hours=age_h),
                "views": views,
                "reach": int(views * 0.78),
                "likes": likes,
                "comments": comments,
                "shares": shares,
                "saved": saved,
                "duration_sec": 900 if kind == "Video" else (7200 if kind == "En vivo" else 60),
            }
        )
    return pd.DataFrame(rows, columns=COLUMNS)
