from django.http import JsonResponse


def home(request):
    return JsonResponse(
        {
            "status": "running",
            "message": "Event Management API is live",
        }
    )

