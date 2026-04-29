#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scraper.py
Busca no Google Places (New) e extracao de e-mails e telefones.
"""

import logging
import re
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

API_BASE = "https://places.googleapis.com/v1"
EMAIL_REGEX = re.compile(
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", re.IGNORECASE
)
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
}


@dataclass
class PlaceResult:
    place_id: str
    name: str
    address: str
    phone: str
    website: str
    emails: list[str]
    rating: float | None
    total_reviews: int | None
    latitude: float | None
    longitude: float | None
    types: list[str]
    price_level: str | None
    opening_hours: str | None
    photos: list[str]


# =============================================================================
# GEOCODING
# =============================================================================

def geocode_address(address: str, api_key: str) -> tuple[float, float] | None:
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": address, "key": api_key}
    logger.info("[GEOCODE] Tentando geocodificar: %s", address)
    try:
        r = requests.get(url, params=params, timeout=15)
        logger.info("[GEOCODE] HTTP %s | URL: %s", r.status_code, r.url)
        data = r.json()
        status = data.get("status", "UNKNOWN")
        logger.info("[GEOCODE] Status da API: %s", status)

        if status == "OK" and data.get("results"):
            loc = data["results"][0]["geometry"]["location"]
            lat, lng = loc["lat"], loc["lng"]
            logger.info("[GEOCODE] Sucesso: lat=%s lng=%s", lat, lng)
            return lat, lng
        else:
            error_msg = data.get("error_message", "Sem detalhes adicionais")
            logger.error("[GEOCODE] Falha: status=%s | error_message=%s | address=%s", status, error_msg, address)
    except requests.exceptions.Timeout:
        logger.error("[GEOCODE] Timeout ao conectar com a API (15s)")
    except requests.exceptions.RequestException as e:
        logger.error("[GEOCODE] Erro de rede: %s", e)
    except Exception as e:
        logger.error("[GEOCODE] Erro inesperado: %s", e)
    return None


# =============================================================================
# PLACES SEARCH
# =============================================================================

def search_places(
    query: str,
    lat: float,
    lng: float,
    radius: int,
    api_key: str,
    max_results: int = 60,
    price_levels: list[int] | None = None,
    open_now: bool = False,
) -> list[dict]:
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": (
            "places.id,places.displayName,places.formattedAddress,"
            "places.internationalPhoneNumber,places.nationalPhoneNumber,"
            "places.websiteUri,places.rating,places.userRatingCount,"
            "places.location,places.types,places.priceLevel,"
            "places.regularOpeningHours,places.photos,places.editorialSummary,"
            "nextPageToken"
        ),
    }

    results: list[dict] = []
    next_page_token = None

    while len(results) < max_results:
        payload: dict = {
            "textQuery": query,
            "locationBias": {
                "circle": {
                    "center": {"latitude": lat, "longitude": lng},
                    "radius": float(radius),
                }
            },
            "pageSize": min(20, max_results - len(results)),
        }
        if next_page_token:
            payload["pageToken"] = next_page_token
        if price_levels:
            payload["priceLevels"] = price_levels
        if open_now:
            payload["openNow"] = True

        try:
            r = requests.post(
                f"{API_BASE}/places:searchText",
                json=payload,
                headers=headers,
                timeout=25,
            )
            data = r.json()
            logger.info("[PLACES] HTTP %s | Resultados nesta pagina: %s", r.status_code, len(data.get("places", [])))
        except requests.exceptions.Timeout:
            logger.error("[PLACES] Timeout na busca (25s)")
            break
        except requests.exceptions.RequestException as e:
            logger.error("[PLACES] Erro de rede na busca: %s", e)
            break
        except Exception as e:
            logger.error("[PLACES] Erro inesperado na busca: %s", e)
            break

        if r.status_code != 200:
            error_detail = data.get("error", {})
            error_msg = error_detail.get("message", str(data))
            error_status = error_detail.get("status", "UNKNOWN")
            logger.error("[PLACES] API Error: status=%s | message=%s | payload=%s", error_status, error_msg, payload)
            break

        places = data.get("places", [])
        if not places:
            break

        results.extend(places)
        next_page_token = data.get("nextPageToken")

        if not next_page_token:
            break
        time.sleep(2)

    return results[:max_results]


# =============================================================================
# EMAIL EXTRACTION
# =============================================================================

def extract_emails_from_url(url: str, max_pages: int = 3) -> list[str]:
    if not url:
        return []

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    found_emails: set[str] = set()
    visited: set[str] = set()
    to_visit = [url]
    pages_visited = 0

    while to_visit and pages_visited < max_pages:
        current_url = to_visit.pop(0)
        if current_url in visited:
            continue
        visited.add(current_url)

        try:
            resp = requests.get(current_url, headers=HEADERS, timeout=12, allow_redirects=True)
            content_type = resp.headers.get("Content-Type", "")
            if resp.status_code != 200 or "text/html" not in content_type:
                continue

            soup = BeautifulSoup(resp.text, "html.parser")

            for tag in soup(["script", "style", "noscript"]):
                tag.decompose()

            text = soup.get_text(separator=" ")
            html_str = str(soup)

            for source in [text, html_str]:
                for match in EMAIL_REGEX.findall(source):
                    email = match.lower().strip()
                    if (
                        len(email) > 5
                        and "." in email.split("@")[-1]
                        and not any(
                            email.endswith(ext)
                            for ext in [
                                ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp",
                                ".css", ".js", ".xml", ".json",
                            ]
                        )
                        and "example" not in email
                        and "yourname" not in email
                        and "nome" not in email
                        and "sentry" not in email
                        and "noreply" not in email
                        and "no-reply" not in email
                    ):
                        found_emails.add(email)

            for link in soup.find_all("a", href=True):
                href = link["href"]
                if href.startswith("mailto:"):
                    email = href[7:].split("?")[0].strip().lower()
                    if email and "@" in email:
                        found_emails.add(email)

            if pages_visited == 0:
                base_domain = urllib.parse.urlparse(url).netloc
                for link in soup.find_all("a", href=True):
                    href = urllib.parse.urljoin(current_url, link["href"])
                    parsed = urllib.parse.urlparse(href)
                    if parsed.netloc == base_domain and parsed.path not in ["/", ""]:
                        if href not in visited and len(to_visit) < 10:
                            lower_path = parsed.path.lower()
                            if any(
                                kw in lower_path
                                for kw in ["contato", "contact", "fale", "sobre", "about", "atendimento"]
                            ):
                                to_visit.insert(0, href)
                            else:
                                to_visit.append(href)

            pages_visited += 1
            time.sleep(0.5)

        except requests.exceptions.Timeout:
            logger.warning("[EMAIL] Timeout ao acessar: %s", current_url)
        except requests.exceptions.RequestException as e:
            logger.warning("[EMAIL] Erro de rede em %s: %s", current_url, e)
        except Exception as e:
            logger.warning("[EMAIL] Erro inesperado em %s: %s", current_url, e)

    return sorted(found_emails)


def extract_emails_parallel(
    places_data: list[dict], max_workers: int = 5
) -> dict[str, list[str]]:
    results: dict[str, list[str]] = {}
    urls_map: dict[str, str] = {}

    for place in places_data:
        pid = place.get("id", "")
        website = place.get("websiteUri", "")
        if website and pid:
            urls_map[pid] = website

    if not urls_map:
        return results

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_pid = {
            executor.submit(extract_emails_from_url, url, 2): pid
            for pid, url in urls_map.items()
        }

        for future in as_completed(future_to_pid):
            pid = future_to_pid[future]
            try:
                emails = future.result(timeout=30)
                results[pid] = emails
            except Exception:
                results[pid] = []

    return results


# =============================================================================
# PHONE EXTRACTION (normalization)
# =============================================================================

def normalize_phone(phone: str | None) -> str:
    if not phone:
        return ""
    phone = phone.strip()
    digits = re.sub(r"\D", "", phone)
    if len(digits) >= 10:
        return phone
    return ""


# =============================================================================
# BUILD RESULTS
# =============================================================================

def build_place_results(
    raw_places: list[dict],
    emails_map: dict[str, list[str]],
    query: str,
    location: str,
) -> list[PlaceResult]:
    results: list[PlaceResult] = []

    for p in raw_places:
        pid = p.get("id", "")
        loc = p.get("location", {})
        phone = p.get("internationalPhoneNumber") or p.get("nationalPhoneNumber", "")
        phone = normalize_phone(phone)
        website = p.get("websiteUri", "")
        emails = emails_map.get(pid, [])

        price = p.get("priceLevel", "")
        if isinstance(price, str) and price.startswith("PRICE_LEVEL_"):
            price = price.replace("PRICE_LEVEL_", "")

        opening = ""
        oh = p.get("regularOpeningHours", {})
        if oh:
            opening = oh.get("weekdayDescriptions", [])
            opening = "; ".join(opening) if isinstance(opening, list) else str(opening)

        photos = []
        for ph in p.get("photos", [])[:3]:
            name = ph.get("name", "")
            if name:
                photos.append(name)

        results.append(
            PlaceResult(
                place_id=pid,
                name=p.get("displayName", {}).get("text", ""),
                address=p.get("formattedAddress", ""),
                phone=phone,
                website=website,
                emails=emails,
                rating=p.get("rating"),
                total_reviews=p.get("userRatingCount"),
                latitude=loc.get("latitude"),
                longitude=loc.get("longitude"),
                types=p.get("types", []),
                price_level=price,
                opening_hours=opening,
                photos=photos,
            )
        )

    return results


def photo_url(photo_name: str, api_key: str, max_width: int = 400) -> str:
    return (
        f"{API_BASE}/{photo_name}/media"
        f"?key={api_key}&maxWidthPx={max_width}"
    )
