from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError

from app.ai.schemas import LeadClassification
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


def get_lead(
    lead_id: str,
    db_engine: Engine = engine,
) -> dict | None:
    """Return one stored lead for API/workflow orchestration."""

    with db_engine.connect() as connection:
        row = connection.execute(
            text(
                """
                SELECT
                    id,
                    full_name,
                    email,
                    phone,
                    service_requested,
                    message,
                    city,
                    created_at,
                    classification,
                    urgency,
                    status,
                    source,
                    ai_summary,
                    follow_up_at,
                    updated_at
                FROM leads
                WHERE id = :lead_id
                """
            ),
            {"lead_id": lead_id},
        ).mappings().first()

    if row is None:
        return None

    return dict(row)


def update_lead_classification(
    lead_id: str,
    classification: LeadClassification,
    db_engine: Engine = engine,
) -> None:
    """Persist validated AI classification results for an existing lead."""

    now_value = datetime.now(timezone.utc)
    now = now_value.isoformat()
    follow_up_at = None

    if classification.classification.value == "quote_request":
        follow_up_at = (now_value + timedelta(hours=24)).isoformat()

    with db_engine.begin() as connection:
        result = connection.execute(
            text(
                """
                UPDATE leads
                SET
                    classification = :classification,
                    urgency = :urgency,
                    ai_summary = :ai_summary,
                    status = :status,
                    follow_up_at = :follow_up_at,
                    updated_at = :updated_at
                WHERE id = :lead_id
                """
            ),
            {
                "lead_id": lead_id,
                "classification": classification.classification.value,
                "urgency": classification.urgency.value,
                "ai_summary": classification.ai_summary,
                "status": "open",
                "follow_up_at": follow_up_at,
                "updated_at": now,
            },
        )

        if result.rowcount != 1:
            raise LookupError(f"Lead not found: {lead_id}")


def mark_lead_for_review(
    lead_id: str,
    db_engine: Engine = engine,
) -> None:
    """Route a lead to manual review when automated processing fails."""

    now = datetime.now(timezone.utc).isoformat()

    with db_engine.begin() as connection:
        result = connection.execute(
            text(
                """
                UPDATE leads
                SET
                    status = :status,
                    updated_at = :updated_at
                WHERE id = :lead_id
                """
            ),
            {
                "lead_id": lead_id,
                "status": "review",
                "updated_at": now,
            },
        )

        if result.rowcount != 1:
            raise LookupError(f"Lead not found: {lead_id}")


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