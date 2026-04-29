#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
database.py
Persistencia em SQLite para o Google Maps Scraper.
"""

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).parent / "scraper.db"


@dataclass
class Business:
    id: int | None
    place_id: str
    name: str
    address: str
    phone: str
    website: str
    emails: str
    rating: float | None
    total_reviews: int | None
    latitude: float | None
    longitude: float | None
    query: str
    location: str
    created_at: str | None


# =============================================================================
# SCHEMA
# =============================================================================

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS businesses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    place_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    address TEXT,
    phone TEXT,
    website TEXT,
    emails TEXT,
    rating REAL,
    total_reviews INTEGER,
    latitude REAL,
    longitude REAL,
    query TEXT,
    location TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_businesses_query ON businesses(query);
CREATE INDEX IF NOT EXISTS idx_businesses_location ON businesses(location);
CREATE INDEX IF NOT EXISTS idx_businesses_name ON businesses(name);
"""


# =============================================================================
# CONNECTION MANAGER
# =============================================================================

@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(SCHEMA_SQL)


# =============================================================================
# CRUD OPERATIONS
# =============================================================================

def save_business(b: Business) -> int:
    with get_conn() as conn:
        cursor = conn.execute(
            """
            INSERT INTO businesses
            (place_id, name, address, phone, website, emails, rating,
             total_reviews, latitude, longitude, query, location)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(place_id) DO UPDATE SET
                name=excluded.name,
                address=excluded.address,
                phone=excluded.phone,
                website=excluded.website,
                emails=excluded.emails,
                rating=excluded.rating,
                total_reviews=excluded.total_reviews,
                latitude=excluded.latitude,
                longitude=excluded.longitude,
                query=excluded.query,
                location=excluded.location,
                created_at=CURRENT_TIMESTAMP
            RETURNING id
            """,
            (
                b.place_id, b.name, b.address, b.phone, b.website, b.emails,
                b.rating, b.total_reviews, b.latitude, b.longitude,
                b.query, b.location,
            ),
        )
        row = cursor.fetchone()
        return row["id"] if row else 0


def save_businesses(businesses: list[Business]) -> int:
    saved = 0
    with get_conn() as conn:
        for b in businesses:
            try:
                conn.execute(
                    """
                    INSERT INTO businesses
                    (place_id, name, address, phone, website, emails, rating,
                     total_reviews, latitude, longitude, query, location)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(place_id) DO UPDATE SET
                        name=excluded.name,
                        address=excluded.address,
                        phone=excluded.phone,
                        website=excluded.website,
                        emails=excluded.emails,
                        rating=excluded.rating,
                        total_reviews=excluded.total_reviews,
                        latitude=excluded.latitude,
                        longitude=excluded.longitude,
                        query=excluded.query,
                        location=excluded.location,
                        created_at=CURRENT_TIMESTAMP
                    """,
                    (
                        b.place_id, b.name, b.address, b.phone, b.website, b.emails,
                        b.rating, b.total_reviews, b.latitude, b.longitude,
                        b.query, b.location,
                    ),
                )
                saved += 1
            except Exception:
                continue
    return saved


def get_all_businesses(
    query_filter: str = "",
    location_filter: str = "",
    has_email: bool = False,
    has_phone: bool = False,
    limit: int = 500,
) -> list[Business]:
    conditions: list[str] = []
    params: list[Any] = []

    if query_filter:
        conditions.append("query LIKE ?")
        params.append(f"%{query_filter}%")
    if location_filter:
        conditions.append("location LIKE ?")
        params.append(f"%{location_filter}%")
    if has_email:
        conditions.append("emails IS NOT NULL AND emails != '' AND emails != 'Não encontrado'")
    if has_phone:
        conditions.append("phone IS NOT NULL AND phone != ''")

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    sql = f"""
        SELECT * FROM businesses
        {where_clause}
        ORDER BY created_at DESC
        LIMIT ?
    """
    params.append(limit)

    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()

    return [_row_to_business(row) for row in rows]


def get_business_by_place_id(place_id: str) -> Business | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM businesses WHERE place_id = ?", (place_id,)
        ).fetchone()
    return _row_to_business(row) if row else None


def delete_business(business_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM businesses WHERE id = ?", (business_id,))


def delete_all_businesses() -> int:
    with get_conn() as conn:
        cursor = conn.execute("DELETE FROM businesses")
        return cursor.rowcount


def count_businesses() -> int:
    with get_conn() as conn:
        row = conn.execute("SELECT COUNT(*) as cnt FROM businesses").fetchone()
        return row["cnt"] if row else 0


def get_stats() -> dict[str, Any]:
    with get_conn() as conn:
        total = conn.execute("SELECT COUNT(*) as cnt FROM businesses").fetchone()["cnt"]
        with_email = conn.execute(
            "SELECT COUNT(*) as cnt FROM businesses WHERE emails IS NOT NULL AND emails != '' AND emails != 'Não encontrado'"
        ).fetchone()["cnt"]
        with_phone = conn.execute(
            "SELECT COUNT(*) as cnt FROM businesses WHERE phone IS NOT NULL AND phone != ''"
        ).fetchone()["cnt"]
        with_website = conn.execute(
            "SELECT COUNT(*) as cnt FROM businesses WHERE website IS NOT NULL AND website != ''"
        ).fetchone()["cnt"]
        queries = conn.execute(
            "SELECT query, COUNT(*) as cnt FROM businesses GROUP BY query ORDER BY cnt DESC LIMIT 5"
        ).fetchall()
        locations = conn.execute(
            "SELECT location, COUNT(*) as cnt FROM businesses GROUP BY location ORDER BY cnt DESC LIMIT 5"
        ).fetchall()

    return {
        "total": total,
        "with_email": with_email,
        "with_phone": with_phone,
        "with_website": with_website,
        "top_queries": queries,
        "top_locations": locations,
    }


def _row_to_business(row: sqlite3.Row) -> Business:
    return Business(
        id=row["id"],
        place_id=row["place_id"],
        name=row["name"],
        address=row["address"] or "",
        phone=row["phone"] or "",
        website=row["website"] or "",
        emails=row["emails"] or "",
        rating=row["rating"],
        total_reviews=row["total_reviews"],
        latitude=row["latitude"],
        longitude=row["longitude"],
        query=row["query"] or "",
        location=row["location"] or "",
        created_at=row["created_at"],
    )
