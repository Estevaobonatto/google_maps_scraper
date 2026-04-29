#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
config_manager.py
Persistencia simples de configuracoes do usuario em JSON.
"""
import json
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "user_config.json"

DEFAULTS = {
    "api_key": "",
    "address": "Sao Paulo, SP",
    "radius": 5000,
    "query": "restaurante",
    "max_results": 20,
    "open_now": False,
    "price_levels": [],
    "scrape_emails": True,
    "max_workers": 3,
    "wa_template": (
        "Ola {nome}! Tudo bem?\n\n"
        "Encontrei o {nome} no Google Maps e gostaria de fazer uma proposta.\n"
        "Podemos conversar?"
    ),
}


def load_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            with CONFIG_PATH.open("r", encoding="utf-8") as f:
                data = json.load(f)
            # garante que todas as chaves existam
            return {**DEFAULTS, **data}
        except Exception:
            pass
    return DEFAULTS.copy()


def save_config(cfg: dict) -> None:
    try:
        with CONFIG_PATH.open("w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
