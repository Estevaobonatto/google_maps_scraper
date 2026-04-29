#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app.py
Interface Streamlit premium para o Google Maps Scraper.
"""

import io
import logging
import re
import sys
from datetime import datetime

import pandas as pd
import streamlit as st

from database import (
    Business,
    count_businesses,
    delete_all_businesses,
    delete_business,
    get_all_businesses,
    get_stats,
    init_db,
    save_businesses,
)
from scraper import (
    build_place_results,
    extract_emails_parallel,
    geocode_address,
    search_places,
)
from whatsapp import (
    DEFAULT_TEMPLATE,
    PLACEHOLDERS_HELP,
    generate_bulk_html,
    make_wa_link,
    open_wa_link,
    render_template,
    send_bulk,
)
from config_manager import load_config, save_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%H:%M:%S",
)


# =============================================================================
# STREAMLIT GUARD
# =============================================================================

def ensure_streamlit():
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        if get_script_run_ctx() is not None:
            return
    except Exception:
        pass
    print("Reiniciando via Streamlit...")
    import subprocess
    subprocess.run([sys.executable, "-m", "streamlit", "run", __file__])
    sys.exit(0)


# =============================================================================
# CUSTOM CSS
# =============================================================================

def inject_css():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        /* Material 3 Dark Surface Colors */
        :root {
            --md-sys-color-background: #0F151D;
            --md-sys-color-surface: #1D242C;
            --md-sys-color-surface-variant: #222B33;
            --md-sys-color-primary: #A8C7FA;
            --md-sys-color-on-primary: #0F151D;
            --md-sys-color-secondary: #82B1FF;
            --md-sys-color-tertiary: #67D7A4;
            --md-sys-color-error: #F2B8B5;
            --md-sys-color-on-surface: #E2E8F0;
            --md-sys-color-on-surface-variant: #94A3B8;
            --md-sys-color-outline: #374151;
            --md-sys-color-outline-variant: #2A3441;
        }

        /* Main Layout */
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1200px;
        }

        /* Headers */
        .main-header {
            font-size: 2.6rem;
            font-weight: 700;
            color: var(--md-sys-color-on-surface);
            letter-spacing: -0.03em;
            margin-bottom: 0.25rem;
            line-height: 1.1;
        }

        .sub-header {
            font-size: 1.05rem;
            color: var(--md-sys-color-on-surface-variant);
            font-weight: 400;
            margin-bottom: 2rem;
        }

        /* Section Titles */
        .section-title {
            font-size: 1.35rem;
            font-weight: 600;
            color: var(--md-sys-color-on-surface);
            margin-top: 1rem;
            margin-bottom: 0.75rem;
            letter-spacing: -0.01em;
        }

        .section-subtitle {
            font-size: 1.1rem;
            font-weight: 600;
            color: var(--md-sys-color-on-surface);
            margin-bottom: 0.5rem;
        }

        /* Metric Cards - Material 3 Elevation */
        .metric-card {
            background: var(--md-sys-color-surface);
            border: 1px solid var(--md-sys-color-outline-variant);
            border-radius: 1.25rem;
            padding: 1.5rem;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            box-shadow: 0 1px 2px rgba(0,0,0,0.2), 0 1px 3px rgba(0,0,0,0.1);
        }

        .metric-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }

        .metric-value {
            font-size: 1.85rem;
            font-weight: 700;
            color: var(--md-sys-color-primary);
            line-height: 1.2;
        }

        .metric-label {
            font-size: 0.75rem;
            color: var(--md-sys-color-on-surface-variant);
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-top: 0.35rem;
            font-weight: 600;
        }

        /* Buttons - Material 3 Shape */
        .stButton>button {
            border-radius: 1.25rem !important;
            font-weight: 600 !important;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
            text-transform: none !important;
            letter-spacing: 0.01em !important;
            border: none !important;
        }

        .stButton>button:active {
            transform: scale(0.97);
        }

        /* Primary Button Glow */
        .stButton>button[kind="primary"] {
            box-shadow: 0 2px 8px rgba(168, 199, 250, 0.25) !important;
        }

        /* DataFrames / Tables */
        div[data-testid="stDataFrame"] {
            border-radius: 1.25rem !important;
            overflow: hidden;
            border: 1px solid var(--md-sys-color-outline-variant);
            background: var(--md-sys-color-surface);
        }

        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background: var(--md-sys-color-surface);
            border-right: 1px solid var(--md-sys-color-outline-variant);
        }

        section[data-testid="stSidebar"] .block-container {
            padding-top: 1.5rem;
        }

        /* Inputs */
        div[data-testid="stTextInput"] input,
        div[data-testid="stTextArea"] textarea {
            background: var(--md-sys-color-surface-variant) !important;
            border: 1px solid var(--md-sys-color-outline) !important;
            border-radius: 0.75rem !important;
            color: var(--md-sys-color-on-surface) !important;
            transition: border-color 0.2s ease, box-shadow 0.2s ease;
        }

        div[data-testid="stTextInput"] input:focus,
        div[data-testid="stTextArea"] textarea:focus {
            border-color: var(--md-sys-color-primary) !important;
            box-shadow: 0 0 0 2px rgba(168, 199, 250, 0.15) !important;
        }

        /* Slider */
        div[data-testid="stSlider"] .stSlider {
            padding-top: 0.5rem;
        }

        /* Tabs - Material 3 */
        .stTabs [data-baseweb="tab-list"] {
            gap: 0.5rem;
            border-bottom: 1px solid var(--md-sys-color-outline-variant);
        }

        .stTabs [data-baseweb="tab"] {
            border-radius: 0.75rem 0.75rem 0 0;
            padding: 0.75rem 1.25rem;
            font-weight: 500;
            color: var(--md-sys-color-on-surface-variant);
            border: none;
        }

        .stTabs [aria-selected="true"] {
            color: var(--md-sys-color-primary) !important;
            background: linear-gradient(180deg, rgba(168,199,250,0.08) 0%, transparent 100%);
            border-bottom: 2px solid var(--md-sys-color-primary) !important;
        }

        /* Expanders */
        div[data-testid="stExpander"] {
            border: 1px solid var(--md-sys-color-outline-variant);
            border-radius: 1rem;
            overflow: hidden;
            background: var(--md-sys-color-surface);
        }

        /* Info / Success / Warning / Error Messages */
        div[data-testid="stAlert"] {
            border-radius: 1rem !important;
            border: 1px solid var(--md-sys-color-outline-variant) !important;
        }

        /* Multiselect & Selectbox Chips */
        div[data-testid="stMultiSelect"] span[data-baseweb="tag"] {
            background: rgba(168, 199, 250, 0.15) !important;
            color: var(--md-sys-color-primary) !important;
            border-radius: 0.5rem !important;
            font-weight: 500;
        }

        /* Scrollbar - Modern */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }

        ::-webkit-scrollbar-track {
            background: transparent;
        }

        ::-webkit-scrollbar-thumb {
            background: var(--md-sys-color-outline);
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: var(--md-sys-color-on-surface-variant);
        }

        /* Divider */
        hr {
            border-color: var(--md-sys-color-outline-variant) !important;
            margin: 1.5rem 0;
        }

        /* Captions */
        .stCaption {
            color: var(--md-sys-color-on-surface-variant) !important;
            font-size: 0.8rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# =============================================================================
# SESSION STATE
# =============================================================================

def init_session():
    cfg = load_config()
    defaults = {
        "results_df": None,
        "search_done": False,
        "tab": "buscar",
        "toast_message": None,
        "wa_select_all": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
    # Sobrescreve com config persistente apenas na primeira carga
    for k in ["api_key", "address", "radius", "query", "max_results",
              "open_now", "price_levels", "scrape_emails", "max_workers", "wa_template"]:
        if k not in st.session_state:
            st.session_state[k] = cfg.get(k, load_config().get(k))


# =============================================================================
# SIDEBAR
# =============================================================================

def _ensure_widget_state(key: str, state_key: str):
    if key not in st.session_state:
        st.session_state[key] = st.session_state.get(state_key, "")


def render_sidebar():
    with st.sidebar:
        st.markdown("<h2 style='font-size:1.25rem;font-weight:700;color:#E2E8F0;letter-spacing:-0.01em;'>Configuracoes</h2>", unsafe_allow_html=True)
        st.markdown("---")

        _ensure_widget_state("input_api_key", "api_key")
        api_key = st.text_input(
            "Google API Key",
            type="password",
            help="Obtida em console.cloud.google.com/apis/credentials",
            key="input_api_key",
        )
        st.session_state.api_key = api_key

        st.markdown("---")
        st.markdown("<p style='font-weight:600;color:#94A3B8;font-size:0.85rem;letter-spacing:0.05em;text-transform:uppercase;'>Localizacao</p>", unsafe_allow_html=True)

        _ensure_widget_state("input_address", "address")
        address = st.text_input(
            "Cidade / Bairro / Endereco",
            help="Ex: Centro, Rio de Janeiro, RJ",
            key="input_address",
        )

        _ensure_widget_state("input_radius", "radius")
        radius = st.slider(
            "Raio de busca (m)",
            min_value=100,
            max_value=50000,
            step=500,
            key="input_radius",
        )

        st.markdown("---")
        st.markdown("<p style='font-weight:600;color:#94A3B8;font-size:0.85rem;letter-spacing:0.05em;text-transform:uppercase;'>Tipo de Negocio</p>", unsafe_allow_html=True)

        _ensure_widget_state("input_query", "query")
        query = st.text_input(
            "Palavras-chave",
            help="Ex: dentista, academia, advogado",
            key="input_query",
        )

        _ensure_widget_state("input_max_results", "max_results")
        max_results = st.slider(
            "Maximo de resultados",
            min_value=5,
            max_value=100,
            step=5,
            key="input_max_results",
        )

        st.markdown("---")
        st.markdown("<p style='font-weight:600;color:#94A3B8;font-size:0.85rem;letter-spacing:0.05em;text-transform:uppercase;'>Filtros Opcionais</p>", unsafe_allow_html=True)

        col_f1, col_f2 = st.columns(2)
        with col_f1:
            _ensure_widget_state("input_open_now", "open_now")
            open_now = st.checkbox("Aberto agora", key="input_open_now")
        with col_f2:
            _ensure_widget_state("input_scrape_emails", "scrape_emails")
            scrape_emails = st.checkbox("Extrair e-mails", key="input_scrape_emails")

        _ensure_widget_state("input_price_levels", "price_levels")
        price_levels = st.multiselect(
            "Faixa de preco",
            options=["FREE", "INEXPENSIVE", "MODERATE", "EXPENSIVE", "VERY_EXPENSIVE"],
            help="Deixe vazio para qualquer faixa",
            key="input_price_levels",
        )

        price_map = {
            "FREE": 0,
            "INEXPENSIVE": 1,
            "MODERATE": 2,
            "EXPENSIVE": 3,
            "VERY_EXPENSIVE": 4,
        }
        price_level_nums = [price_map[p] for p in price_levels] if price_levels else None

        st.markdown("---")
        st.markdown("<p style='font-weight:600;color:#94A3B8;font-size:0.85rem;letter-spacing:0.05em;text-transform:uppercase;'>Extracao de E-mails</p>", unsafe_allow_html=True)

        _ensure_widget_state("input_max_workers", "max_workers")
        max_workers = st.slider(
            "Threads paralelos",
            min_value=1,
            max_value=10,
            step=1,
            key="input_max_workers",
        )

        st.markdown("---")
        search_btn = st.button(
            "Buscar Negocios",
            type="primary",
            width='stretch',
            key="btn_search",
        )

        # Persiste configuracoes
        save_config({
            "api_key": api_key,
            "address": address,
            "radius": radius,
            "query": query,
            "max_results": max_results,
            "open_now": open_now,
            "price_levels": price_levels,
            "scrape_emails": scrape_emails,
            "max_workers": max_workers,
            "wa_template": st.session_state.get("wa_template", DEFAULT_TEMPLATE),
        })

        return {
            "api_key": api_key,
            "address": address,
            "radius": radius,
            "query": query,
            "max_results": max_results,
            "scrape_emails": scrape_emails,
            "max_workers": max_workers,
            "open_now": open_now,
            "price_levels": price_level_nums,
            "search_btn": search_btn,
        }


# =============================================================================
# SEARCH LOGIC
# =============================================================================

def perform_search(cfg: dict):
    if not cfg["api_key"]:
        st.error("Informe sua Google API Key.")
        logging.error("[BUSCA] API Key nao informada pelo usuario")
        return None
    if not cfg["query"]:
        st.error("Informe o tipo de negocio.")
        logging.error("[BUSCA] Query nao informada pelo usuario")
        return None

    logging.info("[BUSCA] Iniciando busca: query='%s' | address='%s' | radius=%s", cfg["query"], cfg["address"], cfg["radius"])
    progress = st.progress(0, text="Geocodificando endereco...")

    coords = geocode_address(cfg["address"], cfg["api_key"])
    if not coords:
        progress.empty()
        logging.error("[BUSCA] Geocodificacao falhou para: %s", cfg["address"])
        st.error(
            "Nao foi possivel geocodificar o endereco.\n\n"
            "**Possiveis causas:**\n"
            "- A API Key esta incorreta ou nao tem a Geocoding API ativada\n"
            "- O endereco e muito vago ou possui erros de digitacao\n"
            "- Problema de conexao com a internet\n\n"
            "**Dica:** Tente um endereco mais completo, ex: `Avenida Paulista, Sao Paulo, SP`"
        )
        return None

    lat, lng = coords
    logging.info("[BUSCA] Coordenadas: lat=%s lng=%s", lat, lng)
    progress.progress(15, text=f"Buscando '{cfg['query']}'...")

    places = search_places(
        query=cfg["query"],
        lat=lat,
        lng=lng,
        radius=cfg["radius"],
        api_key=cfg["api_key"],
        max_results=cfg["max_results"],
        price_levels=cfg["price_levels"],
        open_now=cfg["open_now"],
    )

    if not places:
        progress.empty()
        logging.warning("[BUSCA] Nenhum negocio encontrado para query='%s' em lat=%s lng=%s", cfg["query"], lat, lng)
        st.warning(
            "Nenhum negocio encontrado.\n\n"
            "**Dicas:**\n"
            "- Aumente o raio de busca\n"
            "- Simplifique a query (ex: use apenas `restaurante` ao inves de `restaurante italiano gourmet`)\n"
            "- Verifique se a API Key tem a Places API (New) ativada"
        )
        return None

    logging.info("[BUSCA] %s lugares encontrados pela API", len(places))
    progress.progress(45, text=f"{len(places)} resultados encontrados. Processando...")

    emails_map = {}
    if cfg["scrape_emails"]:
        progress.progress(50, text=f"Extraindo e-mails de {len(places)} sites...")
        logging.info("[BUSCA] Iniciando extracao de e-mails de %s sites (workers=%s)", len(places), cfg["max_workers"])
        emails_map = extract_emails_parallel(places, max_workers=cfg["max_workers"])
        total_emails = sum(len(v) for v in emails_map.values())
        logging.info("[BUSCA] Extracao concluida: %s e-mails encontrados no total", total_emails)

    progress.progress(85, text="Organizando dados...")

    results = build_place_results(places, emails_map, cfg["query"], cfg["address"])
    logging.info("[BUSCA] Resultados finais organizados: %s negocios", len(results))

    # Persist
    businesses = [
        Business(
            id=None,
            place_id=r.place_id,
            name=r.name,
            address=r.address,
            phone=r.phone,
            website=r.website,
            emails=", ".join(r.emails) if r.emails else "Nao encontrado",
            rating=r.rating,
            total_reviews=r.total_reviews,
            latitude=r.latitude,
            longitude=r.longitude,
            query=cfg["query"],
            location=cfg["address"],
            created_at=None,
        )
        for r in results
    ]
    saved_count = save_businesses(businesses)

    progress.progress(100, text="Concluido!")
    import time as _time
    _time.sleep(0.6)
    progress.empty()

    st.session_state.toast_message = f"{saved_count} negocios salvos no banco de dados!"
    return results


# =============================================================================
# RESULTS RENDERING
# =============================================================================

def results_to_df(results: list) -> pd.DataFrame:
    rows = []
    for r in results:
        rows.append({
            "Nome": r.name,
            "Endereco": r.address,
            "Telefone": r.phone or "Nao informado",
            "Website": r.website or "",
            "E-mails": ", ".join(r.emails) if r.emails else "Nao encontrado",
            "Avaliacao": r.rating,
            "Avaliacoes": r.total_reviews,
            "Tipo": ", ".join(r.types[:3]),
            "Preco": r.price_level or "",
            "Horario": r.opening_hours or "",
        })
    return pd.DataFrame(rows)


def render_metrics(results: list):
    total = len(results)
    with_phone = sum(1 for r in results if r.phone)
    with_site = sum(1 for r in results if r.website)
    with_email = sum(1 for r in results if r.emails)

    cols = st.columns(4)
    metrics = [
        ("Total", total, "#A8C7FA"),
        ("Com Telefone", f"{with_phone} ({with_phone/total*100:.0f}%)", "#67D7A4"),
        ("Com Website", f"{with_site} ({with_site/total*100:.0f}%)", "#82B1FF"),
        ("Com E-mail", f"{with_email} ({with_email/total*100:.0f}%)", "#C4A8FA"),
    ]

    for col, (label, value, color) in zip(cols, metrics):
        with col:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-value" style="color:{color};">{value}</div>
                    <div class="metric-label">{label}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_results(results: list):
    if not results:
        st.info("Nenhum resultado para exibir.")
        return

    st.markdown(f"<div class='section-title'>Resultados ({len(results)})</div>", unsafe_allow_html=True)
    render_metrics(results)

    df = results_to_df(results)

    with st.expander("Filtrar Resultados", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            name_filter = st.text_input("Filtrar por nome", "", key="res_filter_name")
        with c2:
            email_only = st.checkbox("Apenas com e-mail", False, key="res_filter_email")

        if name_filter:
            df = df[df["Nome"].str.contains(name_filter, case=False, na=False)]
        if email_only:
            df = df[df["E-mails"] != "Nao encontrado"]

        st.caption(f"Exibindo {len(df)} de {len(results)}")

    display_cols = [c for c in df.columns if c in df]
    st.dataframe(
        df[display_cols],
        width='stretch',
        hide_index=True,
        column_config={
            "Website": st.column_config.LinkColumn("Website"),
            "Avaliacao": st.column_config.NumberColumn("Avaliacao", format="%.1f"),
        },
    )

    st.markdown("---")
    st.markdown("<div class='section-subtitle'>Exportar</div>", unsafe_allow_html=True)

    csv_bytes = df.to_csv(index=False).encode("utf-8-sig")
    e1, e2 = st.columns(2)
    with e1:
        st.download_button(
            "Download CSV",
            data=csv_bytes,
            file_name=f"negocios_{cfg_safe_query()}.csv",
            mime="text/csv",
            width='stretch',
        )
    with e2:
        try:
            buf = io.BytesIO()
            df.to_excel(buf, index=False, engine="openpyxl")
            st.download_button(
                "Download Excel",
                data=buf.getvalue(),
                file_name=f"negocios_{cfg_safe_query()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                width='stretch',
            )
        except ImportError:
            st.info("Instale openpyxl para exportar Excel.")

    # -------------------------------------------------------------------------
    # WhatsApp - Resultados Atuais
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("<div class='section-subtitle'>Campanha WhatsApp (Resultados Atuais)</div>", unsafe_allow_html=True)

    wa_results = [r for r in results if r.phone]
    if wa_results:
        wa_template_res = st.text_area(
            "Template da mensagem",
            value=st.session_state.get("wa_template", DEFAULT_TEMPLATE),
            height=120,
            key="wa_template_results",
            help=PLACEHOLDERS_HELP,
        )
        st.caption(PLACEHOLDERS_HELP)

        names = [r.name for r in wa_results]
        selected_names = st.multiselect(
            "Selecionar leads para envio",
            options=names,
            default=names[: min(5, len(names))],
            key="wa_results_multiselect",
        )

        preview_candidates = [r for r in wa_results if r.name in selected_names]
        if preview_candidates:
            with st.expander("Preview da mensagem (primeiro selecionado)"):
                st.text(render_template(wa_template_res, preview_candidates[0]))

        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("Abrir WhatsApp (local)", width='stretch', key="wa_results_open"):
                to_send = [r for r in wa_results if r.name in selected_names]
                if to_send:
                    with st.spinner("Abrindo conversas no navegador..."):
                        sent, skipped = send_bulk(to_send, wa_template_res, delay=2)
                    st.success(f"{sent} conversas abertas. {skipped} ignorados (sem telefone).")
                else:
                    st.warning("Nenhum lead selecionado com telefone.")
        with c2:
            if st.button("Gerar Launcher HTML", width='stretch', key="wa_results_html"):
                to_send = [r for r in wa_results if r.name in selected_names]
                if to_send:
                    html = generate_bulk_html(to_send, wa_template_res, delay=3)
                    st.download_button(
                        "Baixar HTML",
                        data=html,
                        file_name="campanha_whatsapp_resultados.html",
                        mime="text/html",
                        width='stretch',
                        key="wa_results_download",
                    )
                else:
                    st.warning("Nenhum lead selecionado com telefone.")
        with c3:
            if st.button("Salvar Template", width='stretch', key="wa_results_save_tpl"):
                st.session_state.wa_template = wa_template_res
                st.success("Template salvo para reutilizacao!")
    else:
        st.info("Nenhum resultado da busca possui telefone para campanha WhatsApp.")


def cfg_safe_query() -> str:
    q = st.session_state.get("input_query", "busca")
    return re.sub(r"[^\w\-]", "_", q).strip("_")[:40]


# =============================================================================
# SAVED DATA TAB
# =============================================================================

def render_saved_data():
    stats = get_stats()

    st.markdown("<div class='section-title'>Estatisticas do Banco</div>", unsafe_allow_html=True)
    cols = st.columns(4)
    metrics = [
        ("Total Salvo", stats["total"], "#A8C7FA"),
        ("Com E-mail", stats["with_email"], "#C4A8FA"),
        ("Com Telefone", stats["with_phone"], "#67D7A4"),
        ("Com Website", stats["with_website"], "#82B1FF"),
    ]
    for col, (label, value, color) in zip(cols, metrics):
        with col:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-value" style="color:{color};">{value}</div>
                    <div class="metric-label">{label}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("---")
    st.markdown("<div class='section-subtitle'>Filtros do Banco</div>", unsafe_allow_html=True)

    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        db_query_filter = st.text_input("Busca (query)", "", key="db_filter_query")
    with fc2:
        db_loc_filter = st.text_input("Localizacao", "", key="db_filter_loc")
    with fc3:
        db_has_email = st.checkbox("Apenas com e-mail", False, key="db_filter_email")

    db_has_phone = st.checkbox("Apenas com telefone", False, key="db_filter_phone")

    records = get_all_businesses(
        query_filter=db_query_filter,
        location_filter=db_loc_filter,
        has_email=db_has_email,
        has_phone=db_has_phone,
        limit=500,
    )

    if not records:
        st.info("Nenhum registro encontrado no banco de dados.")
        return

    st.caption(f"{len(records)} registros encontrados")

    rows = []
    for r in records:
        rows.append({
            "ID": r.id,
            "Nome": r.name,
            "Endereco": r.address,
            "Telefone": r.phone or "Nao informado",
            "Website": r.website or "",
            "E-mails": r.emails or "Nao encontrado",
            "Avaliacao": r.rating,
            "Avaliacoes": r.total_reviews,
            "Query": r.query,
            "Local": r.location,
            "Data": r.created_at,
        })
    df = pd.DataFrame(rows)

    st.dataframe(
        df,
        width='stretch',
        hide_index=True,
        column_config={
            "Website": st.column_config.LinkColumn("Website"),
            "Avaliacao": st.column_config.NumberColumn("Avaliacao", format="%.1f"),
        },
    )

    csv_bytes = df.to_csv(index=False).encode("utf-8-sig")
    d1, d2, d3 = st.columns(3)
    with d1:
        st.download_button(
            "Exportar CSV",
            data=csv_bytes,
            file_name="banco_de_dados.csv",
            mime="text/csv",
            width='stretch',
        )
    with d2:
        try:
            buf = io.BytesIO()
            df.to_excel(buf, index=False, engine="openpyxl")
            st.download_button(
                "Exportar Excel",
                data=buf.getvalue(),
                file_name="banco_de_dados.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                width='stretch',
            )
        except ImportError:
            pass
    with d3:
        if st.button("Limpar Banco de Dados", type="secondary", width='stretch'):
            count = delete_all_businesses()
            st.success(f"{count} registros removidos.")
            st.rerun()


# =============================================================================
# WHATSAPP TAB
# =============================================================================

def render_whatsapp_tab():
    st.markdown("<div class='section-title'>Campanha WhatsApp</div>", unsafe_allow_html=True)

    # Template
    wa_template = st.text_area(
        "Template da mensagem",
        value=st.session_state.get("wa_template", DEFAULT_TEMPLATE),
        height=150,
        key="wa_template_global",
        help=PLACEHOLDERS_HELP,
    )
    st.session_state.wa_template = wa_template
    st.caption(PLACEHOLDERS_HELP)

    # Filtros do banco
    fc1, fc2 = st.columns(2)
    with fc1:
        db_query_filter = st.text_input("Busca (query)", "", key="wa_db_filter_query")
    with fc2:
        db_loc_filter = st.text_input("Localizacao", "", key="wa_db_filter_loc")

    records = get_all_businesses(
        query_filter=db_query_filter,
        location_filter=db_loc_filter,
        has_phone=True,
        limit=500,
    )

    if not records:
        st.info("Nenhum lead com telefone encontrado no banco de dados.")
        return

    st.caption(f"{len(records)} leads com telefone encontrados")

    # Selecionar todos / desmarcar
    sa_col1, sa_col2, _ = st.columns([1, 1, 4])
    with sa_col1:
        if st.button("Selecionar Todos", key="wa_select_all_btn"):
            st.session_state.wa_select_all = True
            st.rerun()
    with sa_col2:
        if st.button("Desmarcar Todos", key="wa_deselect_all_btn"):
            st.session_state.wa_select_all = False
            st.rerun()

    select_all = st.session_state.get("wa_select_all", False)

    # Data editor
    rows = []
    for r in records:
        rows.append({
            "Selecionar": select_all,
            "ID": r.id,
            "Nome": r.name,
            "Telefone": r.phone,
            "Local": r.location,
            "Query": r.query,
            "Avaliacao": r.rating,
        })
    df = pd.DataFrame(rows)

    edited_df = st.data_editor(
        df,
        column_config={
            "Selecionar": st.column_config.CheckboxColumn("Selecionar", default=False),
            "Telefone": st.column_config.TextColumn("Telefone"),
            "Avaliacao": st.column_config.NumberColumn("Avaliacao", format="%.1f"),
        },
        hide_index=True,
        width='stretch',
        key="wa_editor",
    )

    selected_ids = edited_df[edited_df["Selecionar"] == True]["ID"].tolist()
    selected_records = [r for r in records if r.id in selected_ids]

    st.caption(f"{len(selected_records)} lead(s) selecionado(s)")

    # Preview
    if selected_records:
        with st.expander("Preview da mensagem (primeiro selecionado)"):
            st.text(render_template(wa_template, selected_records[0]))

    # Acoes
    a1, a2, a3 = st.columns(3)
    with a1:
        if st.button("Abrir WhatsApp (local)", width='stretch', key="wa_open_local"):
            if selected_records:
                with st.spinner("Abrindo conversas no navegador..."):
                    sent, skipped = send_bulk(selected_records, wa_template, delay=2)
                st.success(f"{sent} conversas abertas. {skipped} ignorados.")
            else:
                st.warning("Nenhum lead selecionado.")
    with a2:
        if st.button("Gerar Launcher HTML", width='stretch', key="wa_gen_html"):
            if selected_records:
                html = generate_bulk_html(selected_records, wa_template, delay=3)
                st.download_button(
                    "Baixar HTML",
                    data=html,
                    file_name="campanha_whatsapp.html",
                    mime="text/html",
                    width='stretch',
                    key="wa_download_html",
                )
            else:
                st.warning("Nenhum lead selecionado.")
    with a3:
        if st.button("Gerar Links CSV", width='stretch', key="wa_gen_csv"):
            if selected_records:
                link_rows = []
                for r in selected_records:
                    msg = render_template(wa_template, r)
                    link = make_wa_link(r.phone, msg)
                    link_rows.append({"Nome": r.name, "Telefone": r.phone, "Link": link})
                links_df = pd.DataFrame(link_rows)
                csv_data = links_df.to_csv(index=False).encode("utf-8-sig")
                st.download_button(
                    "Baixar CSV com Links",
                    data=csv_data,
                    file_name="links_whatsapp.csv",
                    mime="text/csv",
                    width='stretch',
                    key="wa_download_csv",
                )
            else:
                st.warning("Nenhum lead selecionado.")


# =============================================================================
# MAIN
# =============================================================================

def main():
    ensure_streamlit()
    init_db()

    st.set_page_config(
        page_title="Google Maps Scraper",
        page_icon="🌐",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_css()
    init_session()

    st.markdown("<div class='main-header'>Google Maps Scraper</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Busque negocios, extraia contatos e gerencie leads com eficiencia.</div>", unsafe_allow_html=True)

    config = render_sidebar()

    tab_buscar, tab_whatsapp, tab_salvos = st.tabs(["Buscar", "WhatsApp", "Banco de Dados"])

    with tab_buscar:
        if not st.session_state.search_done:
            st.info(
                """
                **Como usar:**
                1. Insira sua **Google API Key** na barra lateral
                2. Defina a **localizacao** e **raio** de busca
                3. Informe o **tipo de negocio** (restaurante, dentista, etc.)
                4. Ajuste os **filtros opcionais** se desejar
                5. Clique em **Buscar Negocios**

                Os resultados serao salvos automaticamente no banco de dados SQLite.
                """
            )

        if config["search_btn"]:
            with st.spinner("Executando busca..."):
                results = perform_search(config)
                if results is not None:
                    st.session_state.results_df = results
                    st.session_state.search_done = True
                    st.rerun()

        if st.session_state.search_done and st.session_state.results_df is not None:
            render_results(st.session_state.results_df)

            if st.session_state.toast_message:
                st.success(st.session_state.toast_message)
                st.session_state.toast_message = None

    with tab_whatsapp:
        render_whatsapp_tab()

    with tab_salvos:
        render_saved_data()


if __name__ == "__main__":
    main()
