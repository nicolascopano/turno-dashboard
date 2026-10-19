"""Lee la configuración desde el archivo .env (o variables de entorno / secrets de Streamlit)."""
import os
from pathlib import Path


def _load_dotenv() -> None:
    env_file = Path(__file__).parent / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv()


def get(name: str, default: str = "") -> str:
    value = os.environ.get(name)
    if value:
        return value
    try:  # Streamlit Cloud guarda las claves en "secrets"
        import streamlit as st

        return str(st.secrets.get(name, default))
    except Exception:
        return default


YOUTUBE_API_KEY = get("YOUTUBE_API_KEY")
YOUTUBE_HANDLE = get("YOUTUBE_HANDLE", "turnoenvivo")
INSTAGRAM_ACCESS_TOKEN = get("INSTAGRAM_ACCESS_TOKEN")
INSTAGRAM_USER_ID = get("INSTAGRAM_USER_ID")
TIMEZONE = get("TIMEZONE", "America/Santiago")
DAILY_GOAL = int(get("DAILY_GOAL", "5") or 5)
DASHBOARD_PIN = get("DASHBOARD_PIN", "")
