from app.ai.classifier import (
    AIClassificationError,
    ClassificationProvider,
    classify_lead,
)
from app.ai.schemas import LeadClassification
from app.db.lead_repository import (
    mark_lead_for_review,
    update_lead_classification,
)
from app.schemas import LeadCreate


def classify_saved_lead(
    lead_id: str,
    lead: LeadCreate,
    provider: ClassificationProvider,
) -> LeadClassification | None:
    """
    Classify an already-persisted lead.

    Failed AI classification never deletes or loses the lead. Instead,
    the record is routed to manual review.
    """

    try:
        classification = classify_lead(lead, provider)
    except AIClassificationError:
        mark_lead_for_review(lead_id)
        return None

    update_lead_classification(
        lead_id,
        classification,
    )

    return classification
