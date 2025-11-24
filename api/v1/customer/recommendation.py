import logging
from django.utils import timezone
from organizer.models import Event
from payments.models import Booking
from customer.models import Customer
import numpy as np
import re
from collections import Counter

logger = logging.getLogger(__name__)


# ==========================
# HELPERS
# ==========================

def clean_text(text):
    """Clean the text: lowercase + remove special chars."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return text.strip()


def text_to_vector(text):
    """Convert text into a Counter bag-of-words vector."""
    words = clean_text(text).split()
    return Counter(words)


def cosine_similarity(vec1, vec2):
    """Compute cosine similarity between two Counter vectors."""
    if not vec1 or not vec2:
        return 0.0

    all_words = set(vec1.keys()).union(set(vec2.keys()))
    v1 = np.array([vec1.get(w, 0) for w in all_words])
    v2 = np.array([vec2.get(w, 0) for w in all_words])

    dot = np.dot(v1, v2)
    norm_a = np.linalg.norm(v1)
    norm_b = np.linalg.norm(v2)

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot / (norm_a * norm_b)


# ==========================
# MAIN RECOMMENDATION FUNCTION
# ==========================

def get_event_recommendations(user):
    today = timezone.now().date()

    try:
        customer = Customer.objects.get(user=user)
    except Customer.DoesNotExist:
        return Event.objects.filter(
            end_date__gte=today,
            status="APPROVED",
            is_active=True
        ).order_by('-id')[:5]

    # All user's past bookings
    bookings = Booking.objects.filter(customer=customer).select_related("event")

    booked_events = [
        b.event for b in bookings
        if b.event.end_date and b.event.end_date >= today and b.event.status == "APPROVED" and b.event.is_active
    ]

    # Available recommended event pool
    events = Event.objects.filter(
        end_date__gte=today,
        status="APPROVED",
        is_active=True
    )

    if not booked_events:
        return events.order_by('-id')[:5]

    # Last event user booked
    last_event = booked_events[-1]

    # User event features
    last_features = f"{last_event.title} {last_event.category} {last_event.location}"
    last_vector = text_to_vector(last_features)

    # Compute similarity for each event
    scored_events = []

    for event in events:
        if event.id == last_event.id:
            continue  # skip same event

        features = f"{event.title} {event.category} {event.location}"
        vector = text_to_vector(features)

        score = cosine_similarity(last_vector, vector)
        scored_events.append((event, score))

    # Sort by similarity desc
    scored_events.sort(key=lambda x: x[1], reverse=True)

    # Top 5
    recommended = [event for event, score in scored_events[:5]]

    # If no recommendations found, fallback
    if not recommended:
        return events.order_by('-id')[:5]

    return recommended
