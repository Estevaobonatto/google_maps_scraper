#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
whatsapp.py
Utilitarios para geracao de links e campanhas via WhatsApp Web.
"""
import re
import time
import urllib.parse
import webbrowser

from database import Business

DEFAULT_TEMPLATE = (
    "Ola {nome}! Tudo bem?\n\n"
    "Encontrei o {nome} no Google Maps e gostaria de fazer uma proposta.\n"
    "Podemos conversar?"
)

PLACEHOLDERS_HELP = (
    "Placeholders disponiveis: {nome}, {endereco}, {telefone}, {website}, "
    "{avaliacao}, {avaliacoes}, {query}, {local}"
)


def normalize_phone(phone: str) -> str:
    """Remove tudo exceto digitos e tenta garantir codigo de pais (55)."""
    digits = re.sub(r"\D", "", phone or "")
    if not digits:
        return ""
    # Remove zero a esquerda do DDD (padrao BR)
    if digits.startswith("0") and len(digits) >= 11:
        digits = digits[1:]
    # Adiciona 55 se ainda nao tiver codigo de pais e parecer numero BR
    if not digits.startswith("55") and len(digits) >= 10:
        digits = "55" + digits
    return digits


def make_wa_link(phone: str, message: str) -> str:
    normalized = normalize_phone(phone)
    if not normalized:
        return ""
    encoded_msg = urllib.parse.quote(message, safe="")
    return f"https://wa.me/{normalized}?text={encoded_msg}"


def render_template(template: str, business: Business) -> str:
    mapping = {
        "{nome}": business.name or "",
        "{endereco}": business.address or "",
        "{telefone}": business.phone or "",
        "{website}": business.website or "",
        "{avaliacao}": str(business.rating) if business.rating is not None else "",
        "{avaliacoes}": str(business.total_reviews) if business.total_reviews is not None else "",
        "{query}": business.query or "",
        "{local}": business.location or "",
    }
    result = template
    for key, val in mapping.items():
        result = result.replace(key, val)
    return result


def open_wa_link(phone: str, message: str) -> None:
    link = make_wa_link(phone, message)
    if link:
        webbrowser.open(link, new=2)


def send_bulk(businesses: list[Business], template: str, delay: int = 3) -> tuple[int, int]:
    """
    Abre o navegador padrao para cada lead com telefone.
    Retorna (enviados, ignorados).
    """
    sent = 0
    skipped = 0
    for b in businesses:
        if not b.phone:
            skipped += 1
            continue
        msg = render_template(template, b)
        open_wa_link(b.phone, msg)
        sent += 1
        if sent < len(businesses):
            time.sleep(delay)
    return sent, skipped


def generate_bulk_html(businesses: list[Business], template: str, delay: int = 3) -> str:
    """
    Gera um arquivo HTML standalone que abre os links do WhatsApp
    um a um com delay via JavaScript.
    """
    items = []
    for b in businesses:
        if not b.phone:
            continue
        msg = render_template(template, b)
        link = make_wa_link(b.phone, msg)
        items.append({"name": b.name, "link": link})

    items_js = str(items).replace("'", '"')

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Campanha WhatsApp</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
  body {{ font-family: 'Inter', sans-serif; background:#0F151D; padding:2rem; color:#E2E8F0; }}
  .container {{ max-width:720px; margin:0 auto; background:#1D242C; border-radius:1.25rem; padding:2rem; box-shadow:0 4px 12px rgba(0,0,0,0.3); border:1px solid #2A3441; }}
  h1 {{ margin-top:0; font-size:1.5rem; color:#E2E8F0; letter-spacing:-0.02em; }}
  .lead {{ display:flex; align-items:center; justify-content:space-between; padding:0.85rem 1rem; background:#222B33; border:1px solid #2A3441; border-radius:0.75rem; margin-bottom:0.5rem; transition: all 0.2s ease; }}
  .lead.ok {{ border-left:4px solid #67D7A4; }}
  .lead.waiting {{ border-left:4px solid #FBBF24; }}
  button {{ background:#A8C7FA; color:#0F151D; border:none; padding:0.85rem 1.5rem; border-radius:1.25rem; font-weight:600; cursor:pointer; font-size:1rem; transition: all 0.2s ease; box-shadow:0 2px 8px rgba(168,199,250,0.25); }}
  button:hover {{ transform: translateY(-1px); box-shadow:0 4px 12px rgba(168,199,250,0.35); }}
  button:disabled {{ background:#374151; color:#94A3B8; cursor:not-allowed; box-shadow:none; transform:none; }}
  #status {{ margin-top:1rem; font-weight:600; color:#A8C7FA; }}
  .hint {{ color:#94A3B8; font-size:0.85rem; margin-top:0.75rem; }}
</style>
</head>
<body>
<div class="container">
  <h1>Campanha WhatsApp</h1>
  <p>Total de leads: <strong style="color:#A8C7FA;">{len(items)}</strong></p>
  <p>Delay entre envios: <strong style="color:#A8C7FA;">{delay}s</strong></p>
  <button id="startBtn" onclick="startCampaign()">Iniciar Envio</button>
  <div id="status"></div>
  <div class="hint">Permita pop-ups no navegador para que as abas do WhatsApp sejam abertas automaticamente.</div>
  <div id="leads" style="margin-top:1.5rem;"></div>
</div>
<script>
const leads = {items_js};
const delay = {delay} * 1000;
let current = 0;
let timer = null;

function renderLeads() {{
  const container = document.getElementById('leads');
  container.innerHTML = '';
  leads.forEach((l, idx) => {{
    const div = document.createElement('div');
    div.className = 'lead waiting';
    div.id = 'lead-' + idx;
    div.innerHTML = '<span>' + (idx+1) + '. ' + l.name + '</span><span id="status-' + idx + '">Aguardando...</span>';
    container.appendChild(div);
  }});
}}

function updateLead(idx, status) {{
  const row = document.getElementById('lead-' + idx);
  const lbl = document.getElementById('status-' + idx);
  if (row) row.className = 'lead ok';
  if (lbl) lbl.textContent = status;
}}

function startCampaign() {{
  document.getElementById('startBtn').disabled = true;
  renderLeads();
  const statusDiv = document.getElementById('status');
  statusDiv.textContent = 'Iniciando...';
  current = 0;

  function next() {{
    if (current >= leads.length) {{
      statusDiv.textContent = 'Concluido!';
      document.getElementById('startBtn').disabled = false;
      return;
    }}
    const l = leads[current];
    window.open(l.link, '_blank');
    updateLead(current, 'Enviado');
    statusDiv.textContent = 'Enviando ' + (current+1) + ' de ' + leads.length + '...';
    current++;
    timer = setTimeout(next, delay);
  }}
  next();
}}

renderLeads();
</script>
</body>
</html>"""
    return html
