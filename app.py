"""Dashboard Turno en Vivo — Sala de Control Editorial y Monitoreo de Salida."""
import json
from html import escape

import altair as alt
import pandas as pd
import streamlit as st

import analytics
import config
import insights
import sources

st.set_page_config(
    page_title="Turno · Sala de Control Editorial",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ==============================================================================
# ESTILOS VISUALES: MINIMALISMO EDITORIAL DARK
# ==============================================================================
CUSTOM_CSS = """
<style>
/* Base de la aplicación */
.stApp {
    background-color: #080c14;
    color: #e2e8f0;
}
.block-container {
    padding-top: 1.2rem;
    padding-bottom: 3rem;
    max-width: 1440px;
}

/* Ocultar barra superior vacía de Streamlit para ganar espacio */
header[data-testid="stHeader"] {
    background: transparent;
}

/* Cabecera Editorial Principal */
.newsroom-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 14px 20px;
    background: #0f1420;
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 14px;
    margin-bottom: 16px;
    flex-wrap: wrap;
    gap: 12px;
}
.newsroom-brand {
    display: flex;
    align-items: center;
    gap: 10px;
}
.brand-title {
    font-size: 1.15rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    color: #ffffff;
    text-transform: uppercase;
}
.brand-live-dot {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 0.72rem;
    font-weight: 700;
    color: #34d399;
    background: rgba(52, 211, 153, 0.12);
    border: 1px solid rgba(52, 211, 153, 0.25);
    padding: 2px 8px;
    border-radius: 99px;
    letter-spacing: 0.05em;
}
.brand-stats-group {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
}
.stat-pill {
    font-size: 0.8rem;
    font-weight: 500;
    padding: 4px 10px;
    border-radius: 8px;
    background: #141b2b;
    border: 1px solid rgba(255, 255, 255, 0.06);
    color: #cbd5e1;
}
.stat-pill b {
    color: #ffffff;
}
.stat-pill.yt {
    border-color: rgba(239, 68, 68, 0.3);
    color: #fca5a5;
}
.stat-pill.ig {
    border-color: rgba(236, 72, 153, 0.3);
    color: #f472b6;
}

/* Fila de Métricas Operativas (KPI Strip) */
.kpi-card {
    background: #0e1320;
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 12px;
    padding: 14px 16px;
    height: 100%;
}
.kpi-card .k-label {
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #718096;
    margin-bottom: 4px;
}
.kpi-card .k-value {
    font-size: 1.65rem;
    font-weight: 800;
    color: #f8fafc;
    line-height: 1.15;
}
.kpi-card .k-sub {
    font-size: 0.78rem;
    color: #94a3b8;
    margin-top: 5px;
}
.text-ok { color: #34d399 !important; }
.text-warn { color: #fbbf24 !important; }
.text-bad { color: #f87171 !important; }

/* Tarjetas de Contenido Limpias */
.feed-card {
    background: #0e1422;
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 12px;
    overflow: hidden;
    height: 100%;
    transition: transform 0.15s ease, border-color 0.15s ease, box-shadow 0.15s ease;
    display: flex;
    flex-direction: column;
}
.feed-card:hover {
    transform: translateY(-2px);
    border-color: rgba(59, 130, 246, 0.6);
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.35);
}
.feed-card-thumb-wrap {
    position: relative;
    width: 100%;
    aspect-ratio: 16/9;
    background: #060911;
    overflow: hidden;
}
.feed-card-thumb-wrap img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
}
.feed-card-body {
    padding: 12px 14px;
    display: flex;
    flex-direction: column;
    flex-grow: 1;
    justify-content: space-between;
}
.feed-card-tags {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-bottom: 6px;
    flex-wrap: wrap;
}
.micro-tag {
    font-size: 0.65rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    padding: 2px 7px;
    border-radius: 6px;
}
.micro-tag.yt { background: rgba(239, 68, 68, 0.15); color: #fca5a5; border: 1px solid rgba(239, 68, 68, 0.3); }
.micro-tag.ig { background: rgba(236, 72, 153, 0.15); color: #f472b6; border: 1px solid rgba(236, 72, 153, 0.3); }
.micro-tag.prog { background: #1a2235; color: #93c5fd; }
.micro-tag.hit { background: rgba(16, 185, 129, 0.18); color: #6ee7b7; border: 1px solid rgba(16, 185, 129, 0.4); }

.feed-card-title {
    font-size: 0.88rem;
    font-weight: 600;
    line-height: 1.35;
    color: #f1f5f9;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    margin: 4px 0 10px;
    min-height: 2.4em;
}
.feed-card-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 0.78rem;
    color: #8b97b1;
    border-top: 1px solid rgba(255, 255, 255, 0.04);
    padding-top: 8px;
    margin-top: auto;
}
.feed-card-footer .views {
    font-weight: 700;
    color: #ffffff;
}

/* Tarjetas Ejecutivas de la Pauta (Tab Estrategia) */
.pillar-card {
    background: #0f1524;
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 12px;
    padding: 16px 18px;
    height: 100%;
}
.pillar-card.ok-accent { border-top: 3px solid #34d399; }
.pillar-card.warn-accent { border-top: 3px solid #fbbf24; }
.pillar-card.info-accent { border-top: 3px solid #60a5fa; }

.pillar-tag {
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #8b97b1;
    margin-bottom: 6px;
}
.pillar-title {
    font-size: 1.02rem;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 8px;
}
.pillar-body {
    font-size: 0.85rem;
    color: #cbd5e1;
    line-height: 1.45;
}

/* Fichas de Apuestas de Pauta */
.bet-box {
    background: #0d121f;
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 12px;
    padding: 14px 16px;
    height: 100%;
}
.bet-tag {
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: #60a5fa;
}
.bet-topic {
    font-size: 0.98rem;
    font-weight: 700;
    color: #ffffff;
    margin: 4px 0 8px;
}
.bet-metric-row {
    background: #070a12;
    border: 1px solid rgba(255, 255, 255, 0.04);
    border-radius: 8px;
    padding: 8px 10px;
    font-size: 0.82rem;
    color: #e2e8f0;
    margin-bottom: 8px;
}
.bet-ref {
    font-size: 0.77rem;
    color: #8b97b1;
    line-height: 1.35;
}

/* Banner del Bot de Rastreo */
.bot-banner {
    background: linear-gradient(135deg, #0e1526, #090e1a);
    border: 1px solid rgba(96, 165, 250, 0.25);
    border-radius: 12px;
    padding: 16px 20px;
    margin: 12px 0 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
}
.bot-banner-info h4 {
    margin: 0 0 4px;
    font-size: 1rem;
    font-weight: 700;
    color: #ffffff;
}
.bot-banner-info p {
    margin: 0;
    font-size: 0.83rem;
    color: #94a3b8;
}

/* Cajas de Diagnóstico en el Acordeón */
.deep-diag-box {
    background: #0e1422;
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-left: 3px solid #60a5fa;
    border-radius: 8px;
    padding: 12px 14px;
    margin-bottom: 10px;
}
.deep-diag-box.ok { border-left-color: #34d399; }
.deep-diag-box.warn { border-left-color: #fbbf24; }
.deep-diag-box .t { font-weight: 700; font-size: 0.9rem; color: #f8fafc; margin-bottom: 4px; }
.deep-diag-box .d { font-size: 0.83rem; color: #cbd5e1; line-height: 1.45; }

/* ==========================================================================
   DINÁMICA DE SUPERVIGILANCIA (ESTILO SALUD EDITORIAL / APPLE HEALTH)
   ========================================================================== */
.super-vital-card {
    background: linear-gradient(135deg, #0e1524 0%, #0a0e19 100%);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px;
    padding: 16px 20px;
    margin-bottom: 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
}
.super-vital-status {
    display: flex;
    flex-direction: column;
    gap: 4px;
}
.super-vital-badge {
    font-size: 0.74rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 3px 10px;
    border-radius: 99px;
    width: fit-content;
}
.super-vital-badge.status-ok {
    background: rgba(52, 211, 153, 0.15);
    color: #34d399;
    border: 1px solid rgba(52, 211, 153, 0.35);
}
.super-vital-badge.status-warn {
    background: rgba(251, 191, 36, 0.15);
    color: #fbbf24;
    border: 1px solid rgba(251, 191, 36, 0.35);
}
.super-vital-badge.status-bad {
    background: rgba(248, 113, 113, 0.15);
    color: #f87171;
    border: 1px solid rgba(248, 113, 113, 0.35);
}
.super-vital-text {
    font-size: 0.88rem;
    color: #cbd5e1;
    margin-top: 4px;
    max-width: 650px;
    line-height: 1.4;
}
.super-vital-rings {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
}
.vital-metric-chip {
    background: #141c2e;
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 10px;
    padding: 8px 14px;
    text-align: center;
    min-width: 105px;
}
.vital-metric-chip .v-lbl {
    font-size: 0.67rem;
    font-weight: 700;
    text-transform: uppercase;
    color: #8b97b1;
    letter-spacing: 0.05em;
}
.vital-metric-chip .v-val {
    font-size: 1.25rem;
    font-weight: 800;
    color: #ffffff;
    margin-top: 2px;
}

/* 4 Grandes Tarjetas de Supervigilancia */
.super-kpi-card {
    background: #0d1322;
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 14px;
    padding: 18px 20px;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    position: relative;
    overflow: hidden;
}
.super-kpi-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
}
.super-kpi-card.tot::before { background: linear-gradient(90deg, #34d399, #10b981); }
.super-kpi-card.yt::before { background: linear-gradient(90deg, #ef4444, #b91c1c); }
.super-kpi-card.ig::before { background: linear-gradient(90deg, #ec4899, #be185d); }
.super-kpi-card.rev::before { background: linear-gradient(90deg, #fbbf24, #f59e0b); }
.super-kpi-card.aud::before { background: linear-gradient(90deg, #38bdf8, #2563eb); }

.super-kpi-question {
    font-size: 0.76rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #8b97b1;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.super-kpi-val {
    font-size: 2.15rem;
    font-weight: 800;
    color: #ffffff;
    line-height: 1.1;
    margin-bottom: 6px;
}
.super-kpi-sub {
    font-size: 0.82rem;
    color: #94a3b8;
    line-height: 1.35;
}

/* Las 2 Joyas del Día (Hits de Hoy) */
.super-hit-card {
    background: #0f1526;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px;
    padding: 16px;
    height: 100%;
    display: flex;
    flex-direction: column;
    transition: transform 0.15s ease, border-color 0.15s ease;
}
.super-hit-card:hover {
    transform: translateY(-2px);
    border-color: rgba(96, 165, 250, 0.5);
}
.super-hit-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
}
.super-hit-crown {
    font-size: 0.72rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    padding: 3px 10px;
    border-radius: 99px;
    display: inline-flex;
    align-items: center;
    gap: 5px;
}
.super-hit-crown.yt {
    background: rgba(239, 68, 68, 0.15);
    color: #fca5a5;
    border: 1px solid rgba(239, 68, 68, 0.35);
}
.super-hit-crown.ig {
    background: rgba(236, 72, 153, 0.15);
    color: #f472b6;
    border: 1px solid rgba(236, 72, 153, 0.35);
}
.super-hit-thumb-wrap {
    width: 100%;
    aspect-ratio: 16/9;
    border-radius: 10px;
    overflow: hidden;
    background: #060911;
    margin-bottom: 12px;
}
.super-hit-thumb-wrap img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}
.super-hit-title {
    font-size: 0.98rem;
    font-weight: 700;
    line-height: 1.4;
    color: #f8fafc;
    margin-bottom: 12px;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    min-height: 2.8em;
}
.super-hit-stats {
    background: #080c16;
    border: 1px solid rgba(255, 255, 255, 0.04);
    border-radius: 8px;
    padding: 10px 14px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: auto;
    font-size: 0.82rem;
    color: #cbd5e1;
}

/* Superbrief Ticker */
.superbrief-card {
    background: linear-gradient(135deg, #0e1526, #090e1a);
    border: 1px solid rgba(96, 165, 250, 0.3);
    border-radius: 14px;
    padding: 18px 22px;
    margin: 16px 0 16px;
}
.superbrief-title {
    font-size: 0.88rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #60a5fa;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.superbrief-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 14px;
    margin-bottom: 14px;
}
.superbrief-item {
    background: #111827;
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 10px;
    padding: 12px 14px;
}
.superbrief-item-tag {
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 4px;
}
.superbrief-item-headline {
    font-size: 0.92rem;
    font-weight: 700;
    color: #ffffff;
    line-height: 1.35;
}
.superbrief-item-detail {
    font-size: 0.78rem;
    color: #94a3b8;
    margin-top: 4px;
    line-height: 1.35;
}

/* Tarjetas de Pulso de Guardia (Semáforo de Silencio & Rostro del Día) */
.super-guard-card {
    background: #0d1322;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px;
    padding: 18px 20px;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    position: relative;
    overflow: hidden;
}
.super-guard-card.silence::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, #f59e0b, #ef4444);
}
.super-guard-card.silence.ok::before {
    background: linear-gradient(90deg, #10b981, #059669);
}
.super-guard-card.face::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, #a855f7, #6366f1);
}
.super-guard-card.debate::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, #f97316, #ef4444);
}
.super-guard-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}
.super-guard-title {
    font-size: 0.74rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    color: #8b97b1;
    display: flex;
    align-items: center;
    gap: 6px;
}
.super-guard-badge {
    font-size: 0.72rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 3px 10px;
    border-radius: 99px;
}
.super-guard-badge.ok {
    background: rgba(16, 185, 129, 0.15);
    color: #34d399;
    border: 1px solid rgba(16, 185, 129, 0.35);
}
.super-guard-badge.warn {
    background: rgba(245, 158, 11, 0.15);
    color: #fbbf24;
    border: 1px solid rgba(245, 158, 11, 0.35);
}
.super-guard-badge.bad {
    background: rgba(239, 68, 68, 0.15);
    color: #f87171;
    border: 1px solid rgba(239, 68, 68, 0.35);
}
.super-guard-badge.purple {
    background: rgba(168, 85, 247, 0.15);
    color: #c084fc;
    border: 1px solid rgba(168, 85, 247, 0.35);
}
.super-guard-badge.fire {
    background: rgba(249, 115, 22, 0.15);
    color: #fb923c;
    border: 1px solid rgba(249, 115, 22, 0.35);
}
.super-guard-val {
    font-size: 1.85rem;
    font-weight: 800;
    color: #ffffff;
    line-height: 1.15;
    margin-bottom: 4px;
}
.super-guard-desc {
    font-size: 0.83rem;
    color: #cbd5e1;
    line-height: 1.4;
    margin-bottom: 12px;
}
.super-guard-subgrid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    background: rgba(0, 0, 0, 0.25);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 8px;
    padding: 10px 12px;
    font-size: 0.8rem;
    color: #94a3b8;
}
.super-guard-subgrid b {
    color: #ffffff;
}

.super-guard-badge.rocket {
    background: rgba(56, 189, 248, 0.15);
    color: #38bdf8;
    border: 1px solid rgba(56, 189, 248, 0.35);
}
.super-guard-badge.eje {
    background: rgba(168, 85, 247, 0.15);
    color: #c084fc;
    border: 1px solid rgba(168, 85, 247, 0.35);
}
.super-guard-badge.radar {
    background: rgba(148, 163, 184, 0.15);
    color: #94a3b8;
    border: 1px solid rgba(148, 163, 184, 0.35);
}

/* ==========================================================================
   EL ORÁCULO DE CONCEPTOS & FIGURAS (NUBE DE PAUTA VIVA)
   ========================================================================== */
.oracle-container {
    background: linear-gradient(135deg, #090e1a 0%, #060913 100%);
    border: 1px solid rgba(168, 85, 247, 0.28);
    border-radius: 16px;
    padding: 22px 24px;
    margin-top: 24px;
    margin-bottom: 18px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
    position: relative;
    overflow: hidden;
}
.oracle-container::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, #a855f7, #ec4899, #38bdf8);
}
.oracle-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
    flex-wrap: wrap;
    gap: 10px;
}
.oracle-title {
    font-size: 1.18rem;
    font-weight: 900;
    letter-spacing: -0.01em;
    color: #ffffff;
    display: flex;
    align-items: center;
    gap: 8px;
}
.oracle-subtitle {
    font-size: 0.84rem;
    color: #94a3b8;
    margin-bottom: 18px;
    line-height: 1.45;
}
.oracle-cloud-board {
    background: rgba(13, 19, 34, 0.65);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 24px 20px;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: center;
    gap: 12px 16px;
    min-height: 150px;
}
.oracle-tag-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 12px;
    border-radius: 20px;
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.12);
    color: #e2e8f0;
    text-decoration: none;
    transition: all 0.2s ease;
    cursor: default;
    line-height: 1.2;
}
.oracle-tag-pill:hover {
    transform: translateY(-2px) scale(1.04);
    background: rgba(255, 255, 255, 0.08);
}
.oracle-tag-pill.fire {
    border-color: rgba(239, 68, 68, 0.4);
    color: #fca5a5;
    background: rgba(239, 68, 68, 0.06);
}
.oracle-tag-pill.fire:hover {
    border-color: rgba(239, 68, 68, 0.8);
    box-shadow: 0 0 16px rgba(239, 68, 68, 0.25);
}
.oracle-tag-pill.rocket {
    border-color: rgba(56, 189, 248, 0.4);
    color: #7dd3fc;
    background: rgba(56, 189, 248, 0.06);
}
.oracle-tag-pill.rocket:hover {
    border-color: rgba(56, 189, 248, 0.8);
    box-shadow: 0 0 16px rgba(56, 189, 248, 0.25);
}
.oracle-tag-pill.eje {
    border-color: rgba(168, 85, 247, 0.4);
    color: #d8b4fe;
    background: rgba(168, 85, 247, 0.06);
}
.oracle-tag-pill.eje:hover {
    border-color: rgba(168, 85, 247, 0.8);
    box-shadow: 0 0 16px rgba(168, 85, 247, 0.25);
}
.oracle-tag-pill.radar {
    border-color: rgba(148, 163, 184, 0.25);
    color: #cbd5e1;
    background: rgba(148, 163, 184, 0.04);
}
.oracle-tag-pill-badge {
    font-size: 0.65rem;
    font-weight: 800;
    padding: 2px 6px;
    border-radius: 8px;
    background: rgba(0, 0, 0, 0.45);
    letter-spacing: 0.02em;
    vertical-align: middle;
}

/* Ficha del Oráculo (Inspector) */
.oracle-card-detail {
    background: #0b1120;
    border: 1px solid rgba(168, 85, 247, 0.3);
    border-radius: 14px;
    padding: 20px 24px;
    margin-top: 14px;
    margin-bottom: 24px;
    box-shadow: 0 6px 24px rgba(0, 0, 0, 0.45);
}
.oracle-card-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 14px;
    flex-wrap: wrap;
    gap: 8px;
}
.oracle-name-big {
    font-size: 1.5rem;
    font-weight: 900;
    color: #ffffff;
    display: flex;
    align-items: center;
    gap: 10px;
    letter-spacing: -0.01em;
}
.oracle-kpi-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
    gap: 10px;
    margin-bottom: 14px;
}
.oracle-kpi-chip {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    padding: 8px 12px;
    text-align: center;
}
.oracle-kpi-lbl {
    font-size: 0.68rem;
    font-weight: 700;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}
.oracle-kpi-val {
    font-size: 1.15rem;
    font-weight: 900;
    color: #ffffff;
    margin-top: 2px;
}
.oracle-section-block {
    background: rgba(255, 255, 255, 0.025);
    border-left: 3px solid #38bdf8;
    border-radius: 0 8px 8px 0;
    padding: 10px 14px;
    margin-bottom: 10px;
    font-size: 0.88rem;
    line-height: 1.45;
    color: #cbd5e1;
}
.oracle-section-block.hook {
    border-left-color: #ec4899;
}
.oracle-section-block.fmt {
    border-left-color: #34d399;
}
.oracle-section-title {
    font-size: 0.72rem;
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 4px;
    color: #ffffff;
}
</style>
"""


def render_html(html_str: str, target=st) -> None:
    """Renderiza HTML de forma nativa con target.html() o con markdown sanitizado,
    eliminando cualquier sangría para evitar que Markdown lo interprete como código <pre><code>."""
    cleaned = "\n".join(line.strip() for line in html_str.strip().splitlines())
    if hasattr(target, "html"):
        target.html(cleaned)
    else:
        target.markdown(cleaned, unsafe_allow_html=True)


render_html(CUSTOM_CSS)

# Bloqueo opcional por PIN (para compartir enlace en la nube de forma segura)
if config.DASHBOARD_PIN:
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        _, pin_col, _ = st.columns([1, 1.2, 1])
        with pin_col:
            st.write("")
            st.write("")
            render_html(
                """<div class="newsroom-header" style="justify-content:center;text-align:center;">
                  <div>
                    <span class="brand-title">📡 TURNO EN VIVO</span><br>
                    <small style="color:#94a3b8">Control de Acceso Editorial</small>
                  </div>
                </div>"""
            )
            with st.form("pin_form"):
                entered_pin = st.text_input("PIN de acceso editorial", type="password", placeholder="Ingresa el PIN...")
                submitted = st.form_submit_button("Entrar a la Sala de Control", width="stretch")
                if submitted:
                    if entered_pin.strip() == config.DASHBOARD_PIN.strip():
                        st.session_state.authenticated = True
                        st.rerun()
                    else:
                        st.error("PIN incorrecto.")
        st.stop()

PLATFORM_COLORS = alt.Scale(domain=["YouTube", "Instagram"], range=["#ef4444", "#ec4899"])


def fmt(n) -> str:
    if pd.isna(n):
        return "0"
    n = float(n)
    if abs(n) >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if abs(n) >= 1_000:
        return f"{n / 1_000:.1f}K"
    return f"{int(round(n))}"


def fmt_hours(h: float) -> str:
    if h < 1:
        return f"hace {int(max(h * 60, 1))}m"
    if h < 24:
        return f"hace {h:.1f}h"
    return f"hace {h / 24:.1f}d"


@st.cache_data(ttl=600, show_spinner="Actualizando datos de canales…")
def load_data(demo: bool) -> tuple[pd.DataFrame, dict, list[str]]:
    if demo:
        return sources.demo_data(), {"yt_subs": 126000, "ig_followers": 130610}, []
    frames, errors = [], []
    for name, fn in (("YouTube", sources.fetch_youtube), ("Instagram", sources.fetch_instagram)):
        try:
            frames.append(fn())
        except Exception as e:
            errors.append(f"{name}: {e}")
    non_empty = [f for f in frames if not f.empty]
    df = pd.concat(non_empty, ignore_index=True) if non_empty else sources._empty()
    summary = sources.fetch_account_summary()
    return df, summary, errors


# ==============================================================================
# SIDEBAR MINIMALISTA DE CONFIGURACIÓN
# ==============================================================================
has_credentials = bool(config.YOUTUBE_API_KEY or config.INSTAGRAM_ACCESS_TOKEN)
with st.sidebar:
    st.markdown("### ⚙️ Configuración")
    demo = st.toggle("Modo demo (simulación)", value=not has_credentials)
    platforms = st.multiselect("Canales activos", ["YouTube", "Instagram"], default=["YouTube", "Instagram"])
    days_window = st.slider(
        "Historial de análisis (base: 72h)",
        min_value=3,
        max_value=14,
        value=3,
        help="La base analítica parte siempre en 3 días (72 horas) para capturar el ciclo de noticias activo.",
    )
    st.divider()
    if st.button("🔄 Refrescar datos ahora", width="stretch"):
        st.cache_data.clear()
        st.rerun()
    st.caption("Caché inteligente de 10 minutos para optimizar cuotas.")

raw_df, acc_summary, errors = load_data(demo)
for err in errors:
    st.warning(err)

now = pd.Timestamp.now(tz=config.TIMEZONE)

if raw_df.empty or not platforms:
    st.info("Sin publicaciones para mostrar. Ajusta los filtros en la barra lateral.")
    st.stop()

# Enriquecimiento del DataFrame con el motor analítico
df = analytics.enrich_dataframe(raw_df[raw_df["platform"].isin(platforms)], now, config.TIMEZONE)
today_start = now.floor("D")
df_today = df[df["published_local"] >= today_start]
df_24h = df[df["age_hours"] <= 24.0]
df_72h = df[df["age_hours"] <= 72.0]
df_7d = df[df["age_hours"] <= 168.0]

# Meta diaria calculada automáticamente como promedio semanal real (últimos 7 días)
weekly_pieces_count = len(df_7d)
weekly_avg_daily = max(1.0, round(weekly_pieces_count / 7.0, 1))
daily_goal = max(1, int(round(weekly_avg_daily)))

df_win = df[df["age_hours"] <= days_window * 24.0].copy()
if df_win.empty:
    df_win = df.copy()

# Motor de Inteligencia Editorial transversal (disponible para Supervigilancia y Consejo Editorial)
topic_df = analytics.compute_topic_diagnostics(df_win)
entity_df = analytics.compute_entity_ranking(df_win, min_pieces=2)
proj_data = analytics.generate_projections_and_actions(df_win, topic_df, entity_df)
exec_bullets = insights.build_executive_bullets(df_win, topic_df, entity_df, proj_data["recommended_bets"], days_window)
brief_text, brief_data = insights.build_tracker_brief(
    df_win, topic_df, entity_df, proj_data["recommended_bets"], days_window, now, config.TIMEZONE
)

# ==============================================================================
# CABECERA INSTITUCIONAL EDITORIAL (BRAND + PULSE)
# ==============================================================================
yt_subs = f"🔴 YouTube: <b>{fmt(acc_summary.get('yt_subs', 126000))}</b>"
ig_folls = f"🟣 Instagram: <b>{fmt(acc_summary.get('ig_followers', 130600))}</b>"

render_html(
    f"""<div class="newsroom-header">
      <div class="newsroom-brand">
        <span class="brand-title">📡 TURNO EN VIVO</span>
        <span class="brand-live-dot">● SALA DE CONTROL</span>
        {'<span class="stat-pill" style="color:#fbbf24;border-color:rgba(251,191,36,0.3)">🧪 MODO DEMO</span>' if demo else ''}
      </div>
      <div class="brand-stats-group">
        <span class="stat-pill yt">{yt_subs}</span>
        <span class="stat-pill ig">{ig_folls}</span>
        <span class="stat-pill">🕒 {now:%d/%m · %H:%M} ({config.TIMEZONE.split('/')[-1]})</span>
      </div>
    </div>"""
)

# ==============================================================================
# BANDA DE CONTROL OPERATIVO (KPI STRIP)
# ==============================================================================
n_today = len(df_today)
n_24h = len(df_24h)
yt_today = len(df_today[df_today["platform"] == "YouTube"])
ig_today = len(df_today[df_today["platform"] == "Instagram"])
goal_pct = min(int((n_today / daily_goal) * 100), 100)
goal_color_cls = "text-ok" if n_today >= daily_goal else ("text-warn" if n_today >= daily_goal * 0.5 else "text-bad")

yt_all = df[df["platform"] == "YouTube"].sort_values("published_at")
ig_all = df[df["platform"] == "Instagram"].sort_values("published_at")
yt_last_h = float(yt_all.iloc[-1]["age_hours"]) if not yt_all.empty else 999.0
ig_last_h = float(ig_all.iloc[-1]["age_hours"]) if not ig_all.empty else 999.0

def render_kpi_strip() -> None:
    """Banda compacta de 5 KPIs operacionales (para la vista de Feed)."""
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        render_html(
            f"""<div class="kpi-card">
              <div class="k-label">Meta de Hoy</div>
              <div class="k-value"><span class="{goal_color_cls}">{n_today}</span> <span style="font-size:1rem;color:#64748b">/ {daily_goal}</span></div>
              <div class="k-sub">YT: {yt_today} · IG: {ig_today} ({goal_pct}% de la pauta)</div>
            </div>""",
            target=k1,
        )
    with k2:
        v72 = df_72h["views"].sum()
        n_72 = len(df_72h)
        render_html(
            f"""<div class="kpi-card">
              <div class="k-label">Vistas Ciclo (72h)</div>
              <div class="k-value">{fmt(v72)}</div>
              <div class="k-sub">{n_72} piezas ({fmt(df_today['views'].sum())} hoy)</div>
            </div>""",
            target=k2,
        )
    with k3:
        yt_cls = "text-ok" if yt_last_h < 4 else ("text-warn" if yt_last_h < 10 else "text-bad")
        yt_sub_txt = f"{yt_all.iloc[-1]['kind']} · {yt_all.iloc[-1]['program']}" if not yt_all.empty else "Sin subidas"
        render_html(
            f"""<div class="kpi-card">
              <div class="k-label">Actividad YouTube</div>
              <div class="k-value"><span class="{yt_cls}">{fmt_hours(yt_last_h)}</span></div>
              <div class="k-sub">{escape(yt_sub_txt)}</div>
            </div>""",
            target=k3,
        )
    with k4:
        ig_cls = "text-ok" if ig_last_h < 4 else ("text-warn" if ig_last_h < 10 else "text-bad")
        ig_sub_txt = f"{ig_all.iloc[-1]['kind']} · {fmt(ig_all.iloc[-1]['views'])} v" if not ig_all.empty else "Sin subidas"
        render_html(
            f"""<div class="kpi-card">
              <div class="k-label">Actividad Instagram</div>
              <div class="k-value"><span class="{ig_cls}">{fmt_hours(ig_last_h)}</span></div>
              <div class="k-sub">{escape(ig_sub_txt)}</div>
            </div>""",
            target=k4,
        )
    with k5:
        avg_mult = float(df_win["perf_index"].mean()) if not df_win.empty else 1.0
        render_html(
            f"""<div class="kpi-card">
              <div class="k-label">Multiplicador {days_window}d</div>
              <div class="k-value">{avg_mult:.2f}x</div>
              <div class="k-sub">{len(df_win)} piezas · {fmt(df_win['views'].sum())} vistas</div>
            </div>""",
            target=k5,
        )

# ==============================================================================
# RENDERIZADOR DE FEED ELEGANTE (SIN RUIDO VISUAL)
# ==============================================================================
def render_feed_grid(frame: pd.DataFrame, per_row: int = 4) -> None:
    rows = list(frame.itertuples())
    for i in range(0, len(rows), per_row):
        cols = st.columns(per_row)
        for col, r in zip(cols, rows[i : i + per_row]):
            p_cls = "yt" if r.platform == "YouTube" else "ig"
            hit_badge = f'<span class="micro-tag hit">🔥 {r.perf_index:.1f}x</span>' if r.perf_index >= 1.3 else ""
            prog_badge = f'<span class="micro-tag prog">{escape(str(r.program))}</span>' if str(r.program) not in ("General / Otros", "Prensa / Feed IG") else ""
            
            # Formateo sutil de métricas
            time_ago = fmt_hours(r.age_hours)
            views_str = fmt(r.views)
            eng_str = f"❤️ {fmt(r.likes)}" if r.likes > 0 else ""
            if r.comments > 0:
                eng_str += f" · 💬 {fmt(r.comments)}"
            
            render_html(
                f"""<a class="clean-link" href="{escape(str(r.url))}" target="_blank">
                  <div class="feed-card">
                    <div class="feed-card-thumb-wrap">
                      <img src="{escape(str(r.thumbnail))}" loading="lazy" onerror="this.style.display='none'">
                    </div>
                    <div class="feed-card-body">
                      <div class="feed-card-tags">
                        <span class="micro-tag {p_cls}">{r.platform} · {r.kind}</span>
                        {prog_badge}
                        {hit_badge}
                      </div>
                      <div class="feed-card-title">{escape(str(r.title))}</div>
                      <div class="feed-card-footer">
                        <span>🕒 {time_ago}</span>
                        <span>{eng_str}</span>
                        <span class="views">{views_str} vistas</span>
                      </div>
                    </div>
                  </div>
                </a>""",
                target=col,
            )


# ==============================================================================
# LAS 4 GRANDES ÁREAS CONCEPTUALES
# ==============================================================================
tab_super, tab_pulse, tab_editorial, tab_archive = st.tabs(
    [
        "🩺 1. Supervigilancia & Pauta (La Guardia)",
        "⚡ 2. El Pulso (Feed en Vivo)",
        "🧠 3. Consejo Editorial & Estrategia",
        "📊 4. Hemeroteca & Explorador",
    ]
)

# ------------------------------------------------------------------------------
# TAB 1: SUPERVIGILANCIA (ESTILO SALUD EDITORIAL / APPLE HEALTH)
# ------------------------------------------------------------------------------
with tab_super:
    # 1. Signos Vitales y Estado de Salud
    pct_goal = int((n_today / daily_goal) * 100)
    avg_mult_today = float(df_today["perf_index"].mean()) if not df_today.empty else (float(df_24h["perf_index"].mean()) if not df_24h.empty else 1.0)
    today_views = int(df_today["views"].sum())
    today_debate = float(df_today["debate_rate"].mean()) if not df_today.empty else 0.0

    if n_today >= daily_goal and avg_mult_today >= 1.0:
        vital_cls = "status-ok"
        vital_label = "🟢 SALUD EDITORIAL: ÓPTIMA"
        vital_text = f"Meta diaria alcanzada (<b>{pct_goal}%</b>) con multiplicador promedio de <b>{avg_mult_today:.2f}x</b> sobre la mediana. El canal sostiene alta retención y ritmo activo."
    elif n_today >= max(1, int(daily_goal * 0.5)):
        vital_cls = "status-warn"
        vital_label = "🟡 SALUD EDITORIAL: EN PROGRESO"
        vital_text = f"Producción al <b>{pct_goal}%</b> de la meta diaria ({n_today}/{daily_goal} piezas). Rendimiento actual en <b>{avg_mult_today:.2f}x</b>. Conviene empujar el cierre vespertino con piezas de impacto."
    else:
        vital_cls = "status-bad"
        vital_label = "🔴 SALUD EDITORIAL: RITMO LENTO"
        vital_text = f"Bajo volumen acumulado hoy (<b>{n_today}/{daily_goal}</b> piezas, {pct_goal}% de la meta). Se recomienda acelerar la salida de cortes y publicaciones en franja prime."

    render_html(
        f"""<div class="super-vital-card">
          <div class="super-vital-status">
            <span class="super-vital-badge {vital_cls}">{vital_label}</span>
            <div class="super-vital-text">{vital_text}</div>
          </div>
          <div class="super-vital-rings">
            <div class="vital-metric-chip">
              <div class="v-lbl">Meta Diaria</div>
              <div class="v-val">{pct_goal}%</div>
            </div>
            <div class="vital-metric-chip">
              <div class="v-lbl">Tracción</div>
              <div class="v-val">{avg_mult_today:.2f}x</div>
            </div>
            <div class="vital-metric-chip">
              <div class="v-lbl">Vistas Hoy</div>
              <div class="v-val">{fmt(today_views)}</div>
            </div>
            <div class="vital-metric-chip">
              <div class="v-lbl">Debate / 1K</div>
              <div class="v-val">{today_debate:.1f}</div>
            </div>
          </div>
        </div>""",
        target=tab_super,
    )

    # 2. Las 4 Grandes Preguntas de Supervigilancia
    c_q1, c_q2, c_q3, c_q4 = st.columns(4)

    # Pregunta 1: ¿Cuánto se produjo en la Guardia (Hoy)?
    with c_q1:
        tot_color_cls = "text-ok" if n_today >= daily_goal else ("text-warn" if n_today >= daily_goal * 0.5 else "text-bad")
        render_html(
            f"""<div class="super-kpi-card tot">
              <div class="super-kpi-question">¿Cuánto se produjo en la Guardia (Hoy)? <span>📦</span></div>
              <div class="super-kpi-val"><span class="{tot_color_cls}">{n_today}</span> <span style="font-size:1.15rem;color:#64748b;font-weight:600">/ {daily_goal} piezas</span></div>
              <div class="super-kpi-sub">
                <b>{pct_goal}%</b> de la meta diaria cumplida<br>
                Meta calculada sobre promedio semanal (7 días: <b>{weekly_avg_daily:.1f}</b> piezas/día)
              </div>
            </div>""",
            target=c_q1,
        )

    # Pregunta 2: ¿Cuánto en YouTube hoy?
    yt_today_df = df_today[df_today["platform"] == "YouTube"]
    yt_long = yt_today_df[yt_today_df["kind"].isin(["Video", "En vivo"])]
    yt_shorts = yt_today_df[yt_today_df["kind"] == "Short"]
    yt_v_today = yt_today_df["views"].sum()
    with c_q2:
        render_html(
            f"""<div class="super-kpi-card yt">
              <div class="super-kpi-question">¿Cuánto en YouTube hoy? <span style="color:#ef4444">🔴</span></div>
              <div class="super-kpi-val">{len(yt_today_df)} <span style="font-size:1.15rem;color:#94a3b8;font-weight:600">piezas</span></div>
              <div class="super-kpi-sub">
                <b>{len(yt_long)}</b> largos/vivos · <b>{len(yt_shorts)}</b> shorts<br>
                <b>{fmt(yt_v_today)}</b> vistas · Última: <b>{fmt_hours(yt_last_h)}</b>
              </div>
            </div>""",
            target=c_q2,
        )

    # Pregunta 3: ¿Cuánto en Instagram hoy?
    ig_today_df = df_today[df_today["platform"] == "Instagram"]
    ig_reels = ig_today_df[ig_today_df["kind"] == "Reel"]
    ig_posts = ig_today_df[~ig_today_df["kind"].isin(["Reel"])]
    ig_v_today = ig_today_df["views"].sum()
    with c_q3:
        render_html(
            f"""<div class="super-kpi-card ig">
              <div class="super-kpi-question">¿Cuánto en Instagram hoy? <span style="color:#ec4899">🟣</span></div>
              <div class="super-kpi-val">{len(ig_today_df)} <span style="font-size:1.15rem;color:#94a3b8;font-weight:600">piezas</span></div>
              <div class="super-kpi-sub">
                <b>{len(ig_reels)}</b> reels · <b>{len(ig_posts)}</b> posts/carrusel<br>
                <b>{fmt(ig_v_today)}</b> vistas/reach · Última: <b>{fmt_hours(ig_last_h)}</b>
              </div>
            </div>""",
            target=c_q3,
        )

    # Pregunta 4: ¿Cuánta audiencia acumulada?
    v_total_today = int(df_today["views"].sum())
    v_72h = int(df_72h["views"].sum())

    with c_q4:
        render_html(
            f"""<div class="super-kpi-card aud">
              <div class="super-kpi-question">¿Cuánta audiencia acumulada? <span>📈</span></div>
              <div class="super-kpi-val">{fmt(v_total_today)} <span style="font-size:1.15rem;color:#cbd5e1;font-weight:600">vistas hoy</span></div>
              <div class="super-kpi-sub">
                🔴 YT: <b>{fmt(yt_v_today)}</b> · 🟣 IG: <b>{fmt(ig_v_today)}</b> hoy<br>
                🔄 Ciclo Activo (72h Base): <b>{fmt(v_72h)}</b> vistas totales
              </div>
            </div>""",
            target=c_q4,
        )

    st.write("")

    # 3. Pulso de Guardia: Ritmo, Protagonista & Debate
    st.markdown("### ⚡ Pulso de Guardia (Ritmo, Protagonista & Debate)")
    g_col1, g_col2, g_col3 = st.columns(3)

    # Cálculo 1: Semáforo de Silencio
    yt_last = yt_all.iloc[-1] if not yt_all.empty else None
    ig_last = ig_all.iloc[-1] if not ig_all.empty else None
    yt_last_h = float(yt_last["age_hours"]) if yt_last is not None else 999.0
    ig_last_h = float(ig_last["age_hours"]) if ig_last is not None else 999.0

    if yt_last_h < 3.0:
        s_cls = "ok"
        s_badge = "🟢 AL DÍA · RITMO ACTIVO"
        s_tip = "El canal mantiene un flujo fresco sin baches en el algoritmo de YouTube."
    elif yt_last_h <= 5.0:
        s_cls = "warn"
        s_badge = "🟡 SILENCIO MODERADO"
        s_tip = "Ventana propicia para soltar un Short o clip y reactivar la campana de notificaciones."
    else:
        s_cls = "bad"
        s_badge = "🔴 ALERTA DE BACHE"
        s_tip = "Más de 5 horas sin subir contenido en YouTube. Se recomienda forzar un corte de impacto."

    yt_last_desc = f"{yt_last['kind']} · {yt_last['program']}" if yt_last is not None else "Sin subidas"
    ig_last_desc = f"{ig_last['kind']} ({fmt(ig_last['views'])} v)" if ig_last is not None else "Sin subidas"

    with g_col1:
        render_html(
            f"""<div class="super-guard-card silence {s_cls}">
              <div>
                <div class="super-guard-header">
                  <span class="super-guard-title">⏱️ Semáforo de Silencio · YouTube</span>
                  <span class="super-guard-badge {s_cls}">{s_badge}</span>
                </div>
                <div class="super-guard-val">{fmt_hours(yt_last_h)} <span style="font-size:1.05rem;color:#94a3b8;font-weight:600">sin publicar</span></div>
                <div class="super-guard-desc">{s_tip}</div>
              </div>
              <div class="super-guard-subgrid">
                <div>🔴 <b>YouTube:</b> {fmt_hours(yt_last_h)} atrás<br><span style="color:#64748b">{escape(yt_last_desc)}</span></div>
                <div>🟣 <b>Instagram:</b> {fmt_hours(ig_last_h)} atrás<br><span style="color:#64748b">{escape(ig_last_desc)}</span></div>
              </div>
            </div>""",
            target=g_col1,
        )

    # Cálculo 2: Protagonista / Rostro del Ciclo Activo (72h)
    ent_today = analytics.compute_entity_ranking(df_today, min_pieces=1)
    if not ent_today.empty:
        top_ent = ent_today.iloc[0]
        ent_window = "HOY"
    else:
        ent_72 = analytics.compute_entity_ranking(df_72h, min_pieces=1)
        top_ent = ent_72.iloc[0] if not ent_72.empty else None
        ent_window = "CICLO 72H"

    with g_col2:
        if top_ent is not None:
            ent_name = str(top_ent["entities"])
            ent_mult = float(top_ent["perf_score"])
            ent_badge = f"🔥 {ent_mult:.2f}x s/mediana" if ent_mult >= 1.0 else f"{ent_mult:.2f}x"
            best_t = escape(str(top_ent.get("best_title", ""))[:65])
            render_html(
                f"""<div class="super-guard-card face">
                  <div>
                    <div class="super-guard-header">
                      <span class="super-guard-title">👤 Imán de Audiencia ({ent_window})</span>
                      <span class="super-guard-badge purple">{ent_badge}</span>
                    </div>
                    <div class="super-guard-val">{escape(ent_name)}</div>
                    <div class="super-guard-desc">Pieza clave: <i>«{best_t}…»</i></div>
                  </div>
                  <div class="super-guard-subgrid">
                    <div>📦 <b>{top_ent['pieces']} piezas</b> ({fmt(top_ent['total_views'])} vistas)<br><span style="color:#64748b">Mayor tracción del ciclo</span></div>
                    <div>💬 <b>{top_ent['avg_debate']:.1f}</b> com / 1K vistas<br><span style="color:#64748b">Alto índice de debate</span></div>
                  </div>
                </div>""",
                target=g_col2,
            )
        else:
            render_html(
                """<div class="super-guard-card face">
                  <div>
                    <div class="super-guard-header">
                      <span class="super-guard-title">👤 Imán de Audiencia</span>
                      <span class="super-guard-badge purple">AGENDA CORAL</span>
                    </div>
                    <div class="super-guard-val">Agenda Diversificada</div>
                    <div class="super-guard-desc">Producción distribuida sin un único protagonista dominante en el ciclo.</div>
                  </div>
                  <div class="super-guard-subgrid">
                    <div>📦 <b>Parrilla equilibrada</b></div>
                    <div>💬 <b>Sin concentración crítica</b></div>
                  </div>
                </div>""",
                target=g_col2,
            )

    # Cálculo 3: Termómetro de Polémica (Pieza más comentada / debatida del Ciclo 72h)
    valid_debate = df_72h[df_72h["views"] >= 50].copy()
    with g_col3:
        if not valid_debate.empty:
            polemic_piece = valid_debate.sort_values("debate_rate", ascending=False).iloc[0]
            pol_title = escape(str(polemic_piece["title"])[:65])
            pol_rate = float(polemic_piece["debate_rate"])
            pol_comments = int(polemic_piece["comments"])
            pol_views = int(polemic_piece["views"])
            pol_plat = str(polemic_piece["platform"])
            pol_url = str(polemic_piece["url"])
            render_html(
                f"""<a class="clean-link" href="{escape(pol_url)}" target="_blank">
                  <div class="super-guard-card debate">
                    <div>
                      <div class="super-guard-header">
                        <span class="super-guard-title">💬 Termómetro de Polémica (72h)</span>
                        <span class="super-guard-badge fire">🔥 {pol_rate:.1f} COM / 1K</span>
                      </div>
                      <div class="super-guard-val">{fmt(pol_comments)} <span style="font-size:1.05rem;color:#fb923c;font-weight:600">comentarios ↗</span></div>
                      <div class="super-guard-desc">«{pol_title}…»</div>
                    </div>
                    <div class="super-guard-subgrid">
                      <div>💬 <b>{pol_rate:.1f}</b> com / 1K vistas<br><span style="color:#64748b">Mayor fricción de audiencia</span></div>
                      <div>📈 <b>{fmt(pol_views)} vistas</b><br><span style="color:#64748b">En {pol_plat}</span></div>
                    </div>
                  </div>
                </a>""",
                target=g_col3,
            )
        else:
            render_html(
                """<div class="super-guard-card debate">
                  <div>
                    <div class="super-guard-header">
                      <span class="super-guard-title">💬 Termómetro de Polémica (72h)</span>
                      <span class="super-guard-badge fire">CALMA EDITORIAL</span>
                    </div>
                    <div class="super-guard-val">Debate Estable</div>
                    <div class="super-guard-desc">Conversación fluida sin picos anómalos de conflicto en los comentarios.</div>
                  </div>
                  <div class="super-guard-subgrid">
                    <div>💬 <b>Interacción normal</b></div>
                    <div>📈 <b>Comunidad alineada</b></div>
                  </div>
                </div>""",
                target=g_col3,
            )

    st.write("")

    # 4. Las 2 Joyas del Día (Éxitos de Hoy o del Ciclo)
    st.markdown("### 🏆 Los Éxitos de la Jornada (Piezas Líderes)")

    if not yt_today_df.empty:
        yt_hit = yt_today_df.sort_values("views", ascending=False).iloc[0]
        yt_crown_label = "👑 ÉXITO YOUTUBE DE HOY"
    else:
        yt_72h_df = df_72h[df_72h["platform"] == "YouTube"]
        yt_hit = yt_72h_df.sort_values("views", ascending=False).iloc[0] if not yt_72h_df.empty else None
        yt_crown_label = "⭐ LÍDER YOUTUBE (CICLO 72H)"

    if not ig_today_df.empty:
        ig_hit = ig_today_df.sort_values("views", ascending=False).iloc[0]
        ig_crown_label = "👑 ÉXITO INSTAGRAM DE HOY"
    else:
        ig_72h_df = df_72h[df_72h["platform"] == "Instagram"]
        ig_hit = ig_72h_df.sort_values("views", ascending=False).iloc[0] if not ig_72h_df.empty else None
        ig_crown_label = "⭐ LÍDER INSTAGRAM (CICLO 72H)"

    hit_col1, hit_col2 = st.columns(2)

    with hit_col1:
        if yt_hit is not None:
            prog_badge = f'<span class="micro-tag prog">{escape(str(yt_hit["program"]))}</span>'
            mult_badge = f"🔥 <b>{yt_hit['perf_index']:.1f}x</b> s/mediana" if yt_hit["perf_index"] >= 1.0 else f"{yt_hit['perf_index']:.1f}x"
            render_html(
                f"""<a class="clean-link" href="{escape(str(yt_hit['url']))}" target="_blank">
                  <div class="super-hit-card">
                    <div class="super-hit-header">
                      <span class="super-hit-crown yt">{yt_crown_label}</span>
                      {prog_badge}
                    </div>
                    <div class="super-hit-thumb-wrap">
                      <img src="{escape(str(yt_hit['thumbnail']))}" loading="lazy" onerror="this.style.display='none'">
                    </div>
                    <div class="super-hit-title">{escape(str(yt_hit['title']))}</div>
                    <div class="super-hit-stats">
                      <span>{mult_badge} · 🕒 {fmt_hours(yt_hit['age_hours'])}</span>
                      <span>❤️ {fmt(yt_hit['likes'])} · 💬 {fmt(yt_hit['comments'])}</span>
                      <span style="font-weight:800;color:#ffffff;font-size:0.95rem">{fmt(yt_hit['views'])} vistas ↗</span>
                    </div>
                  </div>
                </a>""",
                target=hit_col1,
            )
        else:
            st.info("Sin publicaciones en YouTube en la ventana activa.")

    with hit_col2:
        if ig_hit is not None:
            kind_badge = f'<span class="micro-tag ig">{escape(str(ig_hit["kind"]))}</span>'
            mult_badge = f"🔥 <b>{ig_hit['perf_index']:.1f}x</b> s/mediana" if ig_hit["perf_index"] >= 1.0 else f"{ig_hit['perf_index']:.1f}x"
            render_html(
                f"""<a class="clean-link" href="{escape(str(ig_hit['url']))}" target="_blank">
                  <div class="super-hit-card">
                    <div class="super-hit-header">
                      <span class="super-hit-crown ig">{ig_crown_label}</span>
                      {kind_badge}
                    </div>
                    <div class="super-hit-thumb-wrap">
                      <img src="{escape(str(ig_hit['thumbnail']))}" loading="lazy" onerror="this.style.display='none'">
                    </div>
                    <div class="super-hit-title">{escape(str(ig_hit['title']))}</div>
                    <div class="super-hit-stats">
                      <span>{mult_badge} · 🕒 {fmt_hours(ig_hit['age_hours'])}</span>
                      <span>❤️ {fmt(ig_hit['likes'])} · 💬 {fmt(ig_hit['comments'])}</span>
                      <span style="font-weight:800;color:#ffffff;font-size:0.95rem">{fmt(ig_hit['views'])} vistas ↗</span>
                    </div>
                  </div>
                </a>""",
                target=hit_col2,
            )
        else:
            st.info("Sin publicaciones en Instagram en la ventana activa.")

    st.write("")

    # 5. El SUPERBRIEF: Adelanto Corto de Recomendaciones en Titulares
    if proj_data["recommended_bets"]:
        b1 = proj_data["recommended_bets"][0]
        head_bet = f"Subir «{b1['topic']}» ({b1['kind']} en {b1['platform']})"
        sub_bet = f"Ángulo: <b>{b1['hook']}</b> · Proyección: <b>{fmt(b1['proj_low'])} – {fmt(b1['proj_high'])} vistas</b> ({b1['mult']:.2f}x)."
    else:
        head_bet = "Diversificar parrilla en temas de alta tracción"
        sub_bet = "Revisar pestaña de Consejo Editorial para recomendaciones."

    if proj_data["cross_platform_gaps"]:
        g1 = proj_data["cross_platform_gaps"][0]
        head_gap = f"Llevar hit de {g1['from_platform']} a {g1['to_platform']} ({g1['to_format']})"
        sub_gap = f"Original: «{escape(g1['title'][:65])}» (<b>{fmt(g1['views'])} vistas</b> · {g1['perf_index']:.1f}x)."
    else:
        head_gap = "Canales alineados sin brechas críticas"
        sub_gap = "No se detectaron piezas virales sin su versión equivalente en el otro canal."

    fatigue_rows = topic_df[topic_df["quadrant"].str.contains("Fatiga")]
    if not fatigue_rows.empty:
        f1 = fatigue_rows.iloc[0]
        head_fat = f"Alerta de Saturación en «{f1['topic']}»"
        sub_fat = f"Concentra el <b>{f1['share_volume']:.0f}%</b> de producción pero rinde a <b>{f1['perf_score']:.2f}x</b>. Reservar solo para conflicto o figuras calientes."
    else:
        head_fat = "Distribución temática equilibrada"
        sub_fat = "Ningún tema muestra niveles críticos de fatiga o sobre-producción."

    render_html(
        f"""<div class="superbrief-card">
          <div class="superbrief-title">⚡ SUPERBRIEF DE PAUTA · DIRECCIÓN EDITORIAL</div>
          <div class="superbrief-grid">
            <div class="superbrief-item">
              <div class="superbrief-item-tag" style="color:#34d399">🎯 1. LA APUESTA PRINCIPAL</div>
              <div class="superbrief-item-headline">{escape(head_bet)}</div>
              <div class="superbrief-item-detail">{sub_bet}</div>
            </div>
            <div class="superbrief-item">
              <div class="superbrief-item-tag" style="color:#60a5fa">🔄 2. OPORTUNIDAD DE RECICLAJE</div>
              <div class="superbrief-item-headline">{escape(head_gap)}</div>
              <div class="superbrief-item-detail">{sub_gap}</div>
            </div>
            <div class="superbrief-item">
              <div class="superbrief-item-tag" style="color:#fbbf24">⚠️ 3. SEMÁFORO / ROTACIÓN</div>
              <div class="superbrief-item-headline">{escape(head_fat)}</div>
              <div class="superbrief-item-detail">{sub_fat}</div>
            </div>
          </div>
        </div>""",
        target=tab_super,
    )

    sb_c1, sb_c2, sb_c3 = st.columns([1.5, 1.5, 4])
    stamp = f"{now:%Y%m%d_%H%M}"
    with sb_c1:
        st.download_button(
            "⬇️ Descargar Brief (.txt)",
            data=brief_text,
            file_name=f"turno_superbrief_{stamp}.txt",
            mime="text/plain",
            width="stretch",
            key="btn_dl_txt_super",
        )
    with sb_c2:
        st.download_button(
            "⬇️ Descargar Datos (.json)",
            data=json.dumps(brief_data, ensure_ascii=False, indent=2),
            file_name=f"turno_superbrief_{stamp}.json",
            mime="application/json",
            width="stretch",
            key="btn_dl_json_super",
        )
    with sb_c3:
        with st.popover("👁️ Previsualizar Prompt para el Bot Rastreador"):
            st.caption("Texto de pauta listo para copiar y pegar en tu bot de rastreo:")
            st.code(brief_text, language=None, wrap_lines=True)

    # 6. EL ORÁCULO DE CONCEPTOS & FIGURAS (NUBE DE PAUTA VIVA)
    concept_cloud = analytics.compute_concept_oracle_cloud(df_win)
    if concept_cloud:
        tag_htmls = []
        for c in concept_cloud:
            font_sz = c["font_size_rem"]
            font_w = c["font_weight"]
            cls_type = c["heat_type"]
            name_esc = escape(c["name"])
            badge_esc = escape(c["heat_badge"])
            tag_htmls.append(
                f'<span class="oracle-tag-pill {cls_type}" style="font-size:{font_sz}rem;font-weight:{font_w};">'
                f'{name_esc} <span class="oracle-tag-pill-badge">{badge_esc}</span>'
                f'</span>'
            )
        cloud_tags_str = "\n".join(tag_htmls)

        render_html(
            f"""<div class="oracle-container">
              <div class="oracle-head">
                <div class="oracle-title">
                  <span>🔮 ORÁCULO DE CONCEPTOS & FIGURAS · NUBE DE PAUTA VIVA</span>
                </div>
                <span class="micro-tag" style="background:rgba(168,85,247,0.18);border:1px solid rgba(168,85,247,0.45);color:#d8b4fe">
                  {len(concept_cloud)} CONCEPTOS ACTIVOS EN EL CICLO
                </span>
              </div>
              <div class="oracle-subtitle">
                El tamaño de cada concepto refleja su volumen acumulado de piezas, vistas e impacto en la audiencia. 
                Los colores señalan la temperatura de la conversación: 
                🔴 <b style="color:#fca5a5">Alta Polémica</b> (fricción en comentarios) · 
                🚀 <b style="color:#7dd3fc">Imán Algorítmico</b> (tracción s/mediana) · 
                🟣 <b style="color:#d8b4fe">Eje Central</b> (frecuencia sostenida).
              </div>
              <div class="oracle-cloud-board">
                {cloud_tags_str}
              </div>
            </div>""",
            target=tab_super,
        )

        # Inspector interactivo del Oráculo
        or_c1, or_c2 = st.columns([2.8, 1.2])
        with or_c1:
            sel_oracle_name = st.selectbox(
                "🔮 Selecciona un concepto o figura para consultar la bajada editorial del Oráculo:",
                [c["name"] for c in concept_cloud],
                index=0,
                key="sel_oracle_concept",
                help="Selecciona cualquier concepto o figura de la nube para ver por qué creció y cómo usarlo en la pauta de hoy.",
            )
        selected_item = next((c for c in concept_cloud if c["name"] == sel_oracle_name), concept_cloud[0])
        with or_c2:
            render_html(
                f"""<div style="font-size:0.82rem;color:#94a3b8;line-height:1.4;margin-top:10px;">
                  📌 <b style="color:#ffffff">{escape(selected_item['category'])}</b><br>
                  Prioridad: <b style="color:#38bdf8">#{concept_cloud.index(selected_item) + 1}</b> en peso relativo.
                </div>"""
            )

        render_html(
            f"""<div class="oracle-card-detail">
              <div class="oracle-card-head">
                <div class="oracle-name-big">
                  🔮 {escape(selected_item['name'])}
                  <span class="super-guard-badge {selected_item['heat_type']}">
                    {escape(selected_item['heat_label'])} · {escape(selected_item['heat_badge'])}
                  </span>
                </div>
                <span class="micro-tag" style="color:#94a3b8;border-color:rgba(255,255,255,0.15)">
                  {escape(selected_item['category'])}
                </span>
              </div>
              <div class="oracle-kpi-row">
                <div class="oracle-kpi-chip">
                  <div class="oracle-kpi-lbl">Presencia en Ciclo</div>
                  <div class="oracle-kpi-val">{selected_item['pieces']} piezas</div>
                </div>
                <div class="oracle-kpi-chip">
                  <div class="oracle-kpi-lbl">Vistas Acumuladas</div>
                  <div class="oracle-kpi-val">{fmt(selected_item['total_views'])}</div>
                </div>
                <div class="oracle-kpi-chip">
                  <div class="oracle-kpi-lbl">Tracción Algorítmica</div>
                  <div class="oracle-kpi-val" style="color:#38bdf8">{selected_item['avg_perf']:.2f}x</div>
                </div>
                <div class="oracle-kpi-chip">
                  <div class="oracle-kpi-lbl">Temperatura Debate</div>
                  <div class="oracle-kpi-val" style="color:#fb923c">{selected_item['avg_debate']:.1f} com/1K</div>
                </div>
              </div>
              <div class="oracle-section-block">
                <div class="oracle-section-title">🧠 Diagnóstico del Oráculo (¿Por qué se mueve en la audiencia?)</div>
                {escape(selected_item['oracle_diagnostic'])}
              </div>
              <div class="oracle-section-block hook">
                <div class="oracle-section-title" style="color:#f472b6">🎯 Acción de Pauta & Gancho Sugerido para Hoy</div>
                <b>{escape(selected_item['oracle_hook'])}</b>
              </div>
              <div class="oracle-section-block fmt">
                <div class="oracle-section-title" style="color:#34d399">🎬 Formato Recomendado</div>
                {escape(selected_item['oracle_format'])}
              </div>
              <div style="margin-top:14px;padding-top:10px;border-top:1px solid rgba(255,255,255,0.08);display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
                <span style="font-size:0.82rem;color:#94a3b8">
                  👑 <b>Nota líder con este concepto:</b> «{escape(selected_item['top_title'][:70])}» ({fmt(selected_item['top_views'])} vistas en {escape(selected_item['top_platform'])})
                </span>
                <a href="{escape(selected_item['top_url'])}" target="_blank" class="clean-link" style="font-size:0.82rem;color:#38bdf8;font-weight:700">
                  Ver publicación ↗
                </a>
              </div>
            </div>""",
            target=tab_super,
        )

# ------------------------------------------------------------------------------
# TAB 2: EL PULSO DEL CICLO Y GUARDIA (FEED EN VIVO)
# ------------------------------------------------------------------------------
with tab_pulse:
    render_kpi_strip()
    st.write("")
    f_c1, f_c2, f_c3 = st.columns([1.6, 1.4, 1.4])
    with f_c1:
        pulse_scope = st.radio(
            "Ventana temporal",
            ["🔄 Ciclo Activo (72h Base)", "🔴 La Guardia (Solo Hoy)", "📅 Semana Completa (7 días)"],
            horizontal=True,
            label_visibility="collapsed",
        )
    with f_c2:
        sort_mode = st.selectbox(
            "Ordenar por",
            ["Más recientes primero", "Mayor velocidad (vistas/h)", "Más vistas", "Mayor impacto (x)"],
            label_visibility="collapsed",
        )
    with f_c3:
        all_unique = sorted(df["program"].unique().tolist())
        prog_options = [p for p in all_unique if p != "Prensa / Feed IG"]
        all_progs = [
            "Todos los programas",
            "🔴 Solo YouTube",
            "🟣 Solo Instagram",
        ] + prog_options
        filter_prog = st.selectbox("Filtrar canal o programa", all_progs, label_visibility="collapsed")

    # Filtrado reactivo
    if pulse_scope == "🔴 La Guardia (Solo Hoy)":
        pulse_df = df_today.copy()
    elif pulse_scope == "📅 Semana Completa (7 días)":
        pulse_df = df_7d.copy()
    else:
        pulse_df = df_72h.copy()

    if filter_prog in ("🔴 Solo YouTube", "Solo YouTube"):
        pulse_df = pulse_df[pulse_df["platform"] == "YouTube"]
    elif filter_prog in ("🟣 Solo Instagram", "Solo Instagram", "Prensa / Feed IG"):
        pulse_df = pulse_df[pulse_df["platform"] == "Instagram"]
    elif filter_prog != "Todos los programas":
        pulse_df = pulse_df[pulse_df["program"] == filter_prog]

    sort_mapping = {
        "Más recientes primero": ("published_at", False),
        "Mayor velocidad (vistas/h)": ("views_per_hour", False),
        "Más vistas": ("views", False),
        "Mayor impacto (x)": ("perf_index", False),
    }[sort_mode]

    if pulse_df.empty:
        st.warning(f"No hay piezas en la ventana «{pulse_scope}» para el filtro «{filter_prog}».")
    else:
        filter_note = f" ({filter_prog})" if filter_prog != "Todos los programas" else ""
        st.caption(
            f"Mostrando **{len(pulse_df)}** piezas{filter_note} · **{fmt(pulse_df['views'].sum())}** vistas generadas · "
            f"El badge **🔥 1.5x** destaca las piezas que superan la mediana de su formato."
        )
        render_feed_grid(pulse_df.sort_values(sort_mapping[0], ascending=sort_mapping[1]))


# ------------------------------------------------------------------------------
# TAB 3: CONSEJO EDITORIAL & PAUTA (ESTRATEGIA)
# ------------------------------------------------------------------------------
with tab_editorial:
    # 1. HERRAMIENTA RÁPIDA: Brief para Bot Rastreador (Banner Integrado)
    render_html(
        """<div class="bot-banner">
          <div class="bot-banner-info">
            <h4>🤖 Generador de Pauta para Bot Rastreador</h4>
            <p>Resumen conclusivo con temas prioritarios, protagonistas, ángulos y exclusiones de hoy listo para alimentar a tu IA rastreadora.</p>
          </div>
        </div>"""
    )
    
    b_act1, b_act2, b_act3 = st.columns([1.5, 1.5, 4])
    stamp = f"{now:%Y%m%d_%H%M}"
    with b_act1:
        st.download_button(
            "⬇️ Descargar Brief (.txt)",
            data=brief_text,
            file_name=f"turno_pauta_bot_{stamp}.txt",
            mime="text/plain",
            width="stretch",
            key="btn_dl_txt_editorial",
        )
    with b_act2:
        st.download_button(
            "⬇️ Descargar Datos (.json)",
            data=json.dumps(brief_data, ensure_ascii=False, indent=2),
            file_name=f"turno_pauta_bot_{stamp}.json",
            mime="application/json",
            width="stretch",
            key="btn_dl_json_editorial",
        )
    with b_act3:
        with st.popover("👁️ Previsualizar Prompt del Bot"):
            st.caption("Copia el texto completo para pegarlo en tu bot o asistente de noticias:")
            st.code(brief_text, language=None, wrap_lines=True)


    st.write("")

    # 2. LOS 3 PILARES EJECUTIVOS (THE 3 BIG TAKEAWAYS)
    st.markdown("### 🎯 Conclusiones Clave de Dirección")
    
    # Extraer las 3 conclusiones más contundentes de los datos
    top_topic = topic_df.iloc[0] if not topic_df.empty else None
    fatigue_topic = topic_df[topic_df["quadrant"].str.contains("Fatiga")].head(1)
    if fatigue_topic.empty:
        fatigue_topic = topic_df.sort_values("perf_score").head(1)
    fat_row = fatigue_topic.iloc[0] if not fatigue_topic.empty else None
    top_entity = entity_df.iloc[0] if not entity_df.empty else None

    c_pil1, c_pil2, c_pil3 = st.columns(3)
    with c_pil1:
        if top_topic is not None:
            render_html(
                f"""<div class="pillar-card ok-accent">
                  <div class="pillar-tag">🌟 Mayor Retorno por Pieza</div>
                  <div class="pillar-title">{escape(top_topic['topic'])} ({top_topic['perf_score']:.2f}x)</div>
                  <div class="pillar-body">
                    Representa el <b>{top_topic['share_volume']:.0f}%</b> de la producción pero aporta el <b>{top_topic['share_views']:.0f}%</b> de las vistas.
                    Promedia <b>{fmt(top_topic['avg_views'])}</b> vistas por pieza y duplica la eficiencia del canal.
                  </div>
                </div>""",
                target=c_pil1,
            )
    with c_pil2:
        if fat_row is not None:
            render_html(
                f"""<div class="pillar-card warn-accent">
                  <div class="pillar-tag">⚠️ Alerta de Saturación</div>
                  <div class="pillar-title">{escape(fat_row['topic'])} ({fat_row['perf_score']:.2f}x)</div>
                  <div class="pillar-body">
                    Concentra el <b>{fat_row['share_volume']:.0f}%</b> del esfuerzo ({int(fat_row['pieces'])} piezas) pero rinde por debajo del promedio.
                    Conviene reducir la repetición y publicar solo ángulos de conflicto o figuras calientes.
                  </div>
                </div>""",
                target=c_pil2,
            )
    with c_pil3:
        if top_entity is not None:
            render_html(
                f"""<div class="pillar-card info-accent">
                  <div class="pillar-tag">🔥 Protagonista de Mayor Tracción</div>
                  <div class="pillar-title">{escape(top_entity['entities'])} ({top_entity['perf_score']:.2f}x)</div>
                  <div class="pillar-body">
                    Multiplica las vistas a <b>{top_entity['perf_score']:.2f}x</b> sobre la mediana ({int(top_entity['pieces'])} piezas analizadas).
                    Genera <b>{top_entity['avg_debate']:.1f}</b> comentarios por cada 1.000 vistas.
                  </div>
                </div>""",
                target=c_pil3,
            )

    st.write("")

    # 3. APUESTAS DE PAUTA RECOMENDADAS (FICHAS EJECUTIVAS)
    st.markdown("### 🔮 3 Apuestas Recomendadas para la Pauta de Mañana")
    st.caption("Proyección calculada sobre el rendimiento histórico de cada combinación de tema, formato y ángulo.")
    if proj_data["recommended_bets"]:
        b_cols = st.columns(len(proj_data["recommended_bets"]))
        for col, bet in zip(b_cols, proj_data["recommended_bets"]):
            render_html(
                f"""<div class="bet-box">
                  <div class="bet-tag">{escape(bet['quadrant'])} · {bet['mult']:.2f}x</div>
                  <div class="bet-topic">{escape(bet['topic'])}</div>
                  <div class="bet-metric-row">
                    🎯 <b>Proyección:</b> {fmt(bet['proj_low'])} – {fmt(bet['proj_high'])} vistas<br>
                    📺 <b>Formato ideal:</b> {escape(bet['platform'])} · {escape(bet['kind'])}<br>
                    🪝 <b>Ángulo:</b> {escape(bet['hook'])}
                  </div>
                  <div class="bet-ref">
                    <b>Referencia ({fmt(bet['example_views'])} v):</b><br>
                    «{escape(bet['example_title'][:85])}»
                  </div>
                </div>""",
                target=col,
            )

    st.write("")

    # 4. CRUCES PENDIENTES ENTRE CANALES (RECICLAJE)
    if proj_data["cross_platform_gaps"]:
        st.markdown("### 🔄 Cruces Pendientes (Oportunidades de Reciclaje)")
        st.caption("Piezas que explotaron en un canal y aún no tienen su versión equivalente en el otro:")
        gap_cols = st.columns(len(proj_data["cross_platform_gaps"][:3]))
        for col, gap in zip(gap_cols, proj_data["cross_platform_gaps"][:3]):
            render_html(
                f"""<div class="pillar-card info-accent">
                  <div class="pillar-tag">De {escape(gap['from_platform'])} ({gap['perf_index']:.1f}x) ➡️ Llevar a {escape(gap['to_platform'])}</div>
                  <div class="pillar-title" style="font-size:0.92rem">«{escape(gap['title'][:75])}»</div>
                  <div class="pillar-body">
                    Original con <b>{fmt(gap['views'])} vistas</b>. Producir versión en <b>{escape(gap['to_format'])}</b>.
                  </div>
                </div>""",
                target=col,
            )

    st.write("")

    # 5. AUDITORÍA METODOLÓGICA PROFUNDA (ACORDEÓN PLEGABLE)
    with st.expander("🔍 Auditoría Editorial Completa (13 Áreas Metodológicas Detalladas)"):
        st.caption("Análisis exhaustivo generado por el motor de inteligencia editorial para el período:")
        if exec_bullets:
            d_cols = st.columns(2)
            for idx, b in enumerate(exec_bullets):
                border_type = "ok" if b["status"] == "ok" else ("warn" if b["status"] == "warn" else "")
                render_html(
                    f"""<div class="deep-diag-box {border_type}">
                      <div class="t">{escape(b['title'])}</div>
                      <div class="d">{b['detail']}</div>
                    </div>""",
                    target=d_cols[idx % 2],
                )


# ------------------------------------------------------------------------------
# TAB 3: HEMEROTECA & EXPLORADOR
# ------------------------------------------------------------------------------
with tab_archive:
    st.markdown("### 📈 Rendimiento Histórico y Hemeroteca")
    
    # 1. Gráficos Comparativos (YouTube vs Instagram separados para no romper escalas)
    start_day = (now.floor("D") - pd.Timedelta(days=days_window - 1))
    all_days = pd.date_range(start_day, now.floor("D"), freq="D")
    day_labels = [d.strftime("%d/%m") for d in all_days]

    daily_grid = (
        df_win[df_win["day_date"] >= start_day]
        .groupby(["date_str", "platform"], as_index=False)
        .agg(
            pieces=("views", "count"),
            views=("views", "sum"),
            avg_views=("views", "mean"),
            med_perf=("perf_index", "median"),
        )
    )
    full_index = pd.MultiIndex.from_product([day_labels, platforms], names=["date_str", "platform"]).to_frame().reset_index(drop=True)
    daily_full = pd.merge(full_index, daily_grid, on=["date_str", "platform"], how="left").fillna(
        {"pieces": 0, "views": 0, "avg_views": 0, "med_perf": 0}
    )

    gc1, gc2 = st.columns(2)
    with gc1:
        st.markdown("##### 📦 Producción Diaria vs. Meta")
        bar_chart = (
            alt.Chart(daily_full)
            .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
            .encode(
                x=alt.X("date_str:N", sort=day_labels, title=None, axis=alt.Axis(labelAngle=0)),
                y=alt.Y("pieces:Q", title="Piezas publicadas", stack="zero"),
                color=alt.Color("platform:N", scale=PLATFORM_COLORS, legend=alt.Legend(orient="top", title=None)),
                tooltip=["date_str", "platform", "pieces", alt.Tooltip("views", format=",")],
            )
        )
        goal_line = alt.Chart(pd.DataFrame({"y": [daily_goal]})).mark_rule(strokeDash=[4, 4], color="#34d399").encode(y="y:Q")
        st.altair_chart((bar_chart + goal_line).properties(height=240), width="stretch")

    with gc2:
        st.markdown("##### 📈 Rendimiento Mediano Relativo (1.0x = Mediana)")
        perf_chart = (
            alt.Chart(daily_full[daily_full["pieces"] > 0])
            .mark_line(point=alt.OverlayMarkDef(size=60), strokeWidth=2.5)
            .encode(
                x=alt.X("date_str:N", sort=day_labels, title=None, axis=alt.Axis(labelAngle=0)),
                y=alt.Y("med_perf:Q", title="Multiplicador (x)"),
                color=alt.Color("platform:N", scale=PLATFORM_COLORS, legend=alt.Legend(orient="top", title=None)),
                tooltip=["date_str", "platform", alt.Tooltip("med_perf", format=".2f"), "pieces"],
            )
        )
        base_rule = alt.Chart(pd.DataFrame({"y": [1.0]})).mark_rule(strokeDash=[4, 4], color="#64748b").encode(y="y:Q")
        st.altair_chart((perf_chart + base_rule).properties(height=240), width="stretch")

    # 2. Vistas separadas por canal
    vc1, vc2 = st.columns(2)
    with vc1:
        yt_d = daily_full[daily_full["platform"] == "YouTube"]
        st.markdown("##### 🔴 Vistas Diarias en YouTube")
        ch_yt = (
            alt.Chart(yt_d)
            .mark_bar(color="#ef4444", cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
            .encode(
                x=alt.X("date_str:N", sort=day_labels, title=None, axis=alt.Axis(labelAngle=0)),
                y=alt.Y("views:Q", title="Vistas"),
                tooltip=["date_str", "pieces", alt.Tooltip("views", format=",")],
            )
            .properties(height=200)
        )
        st.altair_chart(ch_yt, width="stretch")

    with vc2:
        ig_d = daily_full[daily_full["platform"] == "Instagram"]
        st.markdown("##### 🟣 Vistas Diarias en Instagram")
        ch_ig = (
            alt.Chart(ig_d)
            .mark_bar(color="#ec4899", cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
            .encode(
                x=alt.X("date_str:N", sort=day_labels, title=None, axis=alt.Axis(labelAngle=0)),
                y=alt.Y("views:Q", title="Vistas"),
                tooltip=["date_str", "pieces", alt.Tooltip("views", format=",")],
            )
            .properties(height=200)
        )
        st.altair_chart(ch_ig, width="stretch")

    st.write("")

    # 3. Matriz Estratégica & Protagonistas
    mc1, mc2 = st.columns([1.1, 1])
    with mc1:
        st.markdown("##### 🎯 Matriz de Eficiencia (Esfuerzo vs. Retorno)")
        if not topic_df.empty:
            base_b = alt.Chart(topic_df).encode(
                x=alt.X("share_volume:Q", title="% Esfuerzo (Publicaciones)", scale=alt.Scale(zero=True)),
                y=alt.Y("perf_score:Q", title="Multiplicador (1.0x = Promedio)", scale=alt.Scale(zero=False)),
                tooltip=["topic", "quadrant", "pieces", alt.Tooltip("perf_score", format=".2f"), alt.Tooltip("avg_views", format=",")],
            )
            bubbles = base_b.mark_circle(opacity=0.85, stroke="#ffffff", strokeWidth=1).encode(
                size=alt.Size("total_views:Q", scale=alt.Scale(range=[200, 1400]), legend=None),
                color=alt.Color(
                    "quadrant:N",
                    scale=alt.Scale(
                        domain=["🌟 Motor de Audiencia", "🚀 Oportunidad Sub-explotada", "⚖️ Pilar Estable", "⚠️ Alerta de Fatiga"],
                        range=["#34d399", "#60a5fa", "#94a3b8", "#f87171"],
                    ),
                    legend=alt.Legend(orient="bottom", title=None),
                ),
            )
            labels = base_b.mark_text(align="left", dx=10, dy=-4, fontSize=11, color="#cbd5e1").encode(text="topic:N")
            hline = alt.Chart(pd.DataFrame({"y": [1.0]})).mark_rule(strokeDash=[4, 4], color="#fbbf24").encode(y="y:Q")
            st.altair_chart((bubbles + labels + hline).properties(height=290), width="stretch")

    with mc2:
        st.markdown("##### 🔥 Protagonistas Calientes & Debate")
        if not entity_df.empty:
            ent_chart = (
                alt.Chart(entity_df.head(8))
                .mark_bar(cornerRadiusEnd=5)
                .encode(
                    x=alt.X("perf_score:Q", title="Multiplicador (x)"),
                    y=alt.Y("entities:N", sort="-x", title=None, axis=alt.Axis(labelLimit=200)),
                    color=alt.Color("avg_debate:Q", title="Comentarios/1K v", scale=alt.Scale(scheme="goldred"), legend=alt.Legend(orient="bottom")),
                    tooltip=["entities", "pieces", alt.Tooltip("perf_score", format=".2f"), alt.Tooltip("avg_views", format=",")],
                )
                .properties(height=290)
            )
            st.altair_chart(ent_chart, width="stretch")

    st.write("")

    # 4. Explorador Interactivo de Catálogo (Estilo Notion/Airtable)
    st.markdown("##### 🔎 Explorador de Catálogo Completo")
    s_col1, s_col2, s_col3, s_col4 = st.columns([1.8, 1.1, 1.1, 1.1])
    with s_col1:
        search_kw = st.text_input("Buscador por invitado o titular", placeholder="Ej: Mayol, Vidal, Kast, Estallido…", label_visibility="collapsed")
    with s_col2:
        sel_chan = st.selectbox("Canal", ["Todos los canales", "🔴 YouTube", "🟣 Instagram"], label_visibility="collapsed")
    with s_col3:
        top_opts = ["Todos los temas"] + sorted(df_win["topic"].unique().tolist())
        sel_topic = st.selectbox("Tema", top_opts, label_visibility="collapsed")
    with s_col4:
        fmt_opts = ["Todos los formatos"] + sorted(df_win["kind"].unique().tolist())
        sel_fmt = st.selectbox("Formato", fmt_opts, label_visibility="collapsed")

    filtered_table = df_win.copy()
    if search_kw.strip():
        q = analytics._norm(search_kw)
        filtered_table = filtered_table[filtered_table["full_text"].fillna("").apply(lambda t: q in analytics._norm(t))]
    if sel_chan == "🔴 YouTube":
        filtered_table = filtered_table[filtered_table["platform"] == "YouTube"]
    elif sel_chan == "🟣 Instagram":
        filtered_table = filtered_table[filtered_table["platform"] == "Instagram"]
    if sel_topic != "Todos los temas":
        filtered_table = filtered_table[filtered_table["topic"] == sel_topic]
    if sel_fmt != "Todos los formatos":
        filtered_table = filtered_table[filtered_table["kind"] == sel_fmt]

    st.dataframe(
        filtered_table.sort_values("published_at", ascending=False)[
            [
                "published_local",
                "platform",
                "kind",
                "program",
                "topic",
                "title",
                "views",
                "perf_index",
                "likes",
                "comments",
                "shares",
                "saved",
                "url",
            ]
        ],
        hide_index=True,
        width="stretch",
        column_config={
            "published_local": st.column_config.DatetimeColumn("Fecha", format="DD/MM HH:mm"),
            "platform": st.column_config.TextColumn("Canal"),
            "kind": st.column_config.TextColumn("Tipo"),
            "program": st.column_config.TextColumn("Franja"),
            "topic": st.column_config.TextColumn("Tema"),
            "title": st.column_config.TextColumn("Titular", width="large"),
            "views": st.column_config.NumberColumn("Vistas", format="%d"),
            "perf_index": st.column_config.NumberColumn("Mult.", format="%.2fx"),
            "likes": st.column_config.NumberColumn("Likes", format="%d"),
            "comments": st.column_config.NumberColumn("Coment.", format="%d"),
            "shares": st.column_config.NumberColumn("Compart.", format="%d"),
            "saved": st.column_config.NumberColumn("Guardados", format="%d"),
            "url": st.column_config.LinkColumn("Enlace", display_text="Abrir ↗"),
        },
    )
