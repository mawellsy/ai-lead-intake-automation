from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError

from app.db.database import engine
from app.schemas import LeadCreate


@dataclass(frozen=True)
class SaveLeadResult:
    lead_id: str
    created: bool


def _normalize_text(value: str | None) -> str:
    if not value:
        return ""

    return " ".join(value.lower().split())


def _normalize_phone(value: str | None) -> str:
    if not value:
        return ""

    return "".join(character for character in value if character.isdigit())


def build_dedup_key(lead: LeadCreate) -> str:
    """
    Build a stable fingerprint for duplicate detection.

    Two submissions are considered duplicates when their normalized
    email, phone, requested service, and message are identical.
    """

    components = [
        str(lead.email).lower(),
        _normalize_phone(lead.phone),
        _normalize_text(lead.service_requested),
        _normalize_text(lead.message),
    ]

    raw_value = "|".join(components)

    return hashlib.sha256(raw_value.encode("utf-8")).hexdigest()


def save_lead(
    lead: LeadCreate,
    db_engine: Engine = engine,
) -> SaveLeadResult:
    dedup_key = build_dedup_key(lead)

    with db_engine.begin() as connection:
        existing = connection.execute(
            text(
                """
                SELECT id
                FROM leads
                WHERE dedup_key = :dedup_key
                """
            ),
            {"dedup_key": dedup_key},
        ).mappings().first()

        if existing:
            return SaveLeadResult(
                lead_id=existing["id"],
                created=False,
            )

        lead_id = str(uuid4())
        now = datetime.now(timezone.utc).isoformat()

        try:
            connection.execute(
                text(
                    """
                    INSERT INTO leads (
                        id,
                        full_name,
                        email,
                        phone,
                        service_requested,
                        message,
                        city,
                        created_at,
                        status,
                        source,
                        dedup_key,
                        updated_at
                    )
                    VALUES (
                        :id,
                        :full_name,
                        :email,
                        :phone,
                        :service_requested,
                        :message,
                        :city,
                        :created_at,
                        :status,
                        :source,
                        :dedup_key,
                        :updated_at
                    )
                    """
                ),
                {
                    "id": lead_id,
                    "full_name": lead.full_name,
                    "email": str(lead.email),
                    "phone": lead.phone,
                    "service_requested": lead.service_requested,
                    "message": lead.message,
                    "city": lead.city,
                    "created_at": now,
                    "status": "new",
                    "source": lead.source,
                    "dedup_key": dedup_key,
                    "updated_at": now,
                },
            )

        except IntegrityError:
            existing = connection.execute(
                text(
                    """
                    SELECT id
                    FROM leads
                    WHERE dedup_key = :dedup_key
                    """
                ),
                {"dedup_key": dedup_key},
            ).mappings().first()

            if existing:
                return SaveLeadResult(
                    lead_id=existing["id"],
                    created=False,
                )

            raise

    return SaveLeadResult(
        lead_id=lead_id,
        created=True,
    )