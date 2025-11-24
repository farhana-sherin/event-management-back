import logging
from django.utils import timezone
from organizer.models import Event
from payments.models import Booking
from customer.models import Customer

logger = logging.getLogger(__name__)

def get_event_recommendations(user):
    today = timezone.now().date() 

    try:
        customer = Customer.objects.get(user=user)
    except Customer.DoesNotExist:
        return Event.objects.filter(
            end_date__gte=today, status="APPROVED", is_active=True
        ).order_by('-id')[:5]

    bookings = Booking.objects.filter(customer=customer).select_related("event")
    booked_events = [
        b.event for b in bookings
        if b.event.end_date and b.event.end_date >= today and b.event.status == "APPROVED" and b.event.is_active
    ]

    # only approved + active events
    events = Event.objects.filter(end_date__gte=today, status="APPROVED", is_active=True)

    if not booked_events:
        return events.order_by('-id')[:5]

    try:
        from sklearn.metrics.pairwise import cosine_similarity
        from sklearn.feature_extraction.text import CountVectorizer
        import pandas as pd
    except Exception as import_error:
        logger.warning("Falling back to default recommendations: %s", import_error)
        return events.order_by('-id')[:5]

    df = pd.DataFrame(list(events.values("id", "title", "category", "location")))
    if df.empty:
        return events.order_by('-id')[:5]

    df["features"] = df["title"] + " " + df["category"] + " " + df["location"]

    try:
        cv = CountVectorizer(stop_words="english")
        vectors = cv.fit_transform(df["features"])
        similarity_matrix = cosine_similarity(vectors)

        last_event = booked_events[-1]
        # if event not found in df (filtered out), just return latest
        if last_event.id not in df["id"].values:
            return events.order_by('-id')[:5]

        last_event_index = df[df["id"] == last_event.id].index[0]

        scores = list(enumerate(similarity_matrix[last_event_index]))
        scores = sorted(scores, key=lambda x: x[1], reverse=True)

        recommended_indices = [i for i, _ in scores if df.iloc[i]["id"] != last_event.id][:5]
        recommended_ids = df.iloc[recommended_indices]["id"].tolist()

        return Event.objects.filter(id__in=recommended_ids, status="APPROVED", is_active=True)
    except Exception as processing_error:
        logger.warning("Recommendation generation failed: %s", processing_error)
        return events.order_by('-id')[:5]
