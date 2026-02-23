
import json
import logging
from django.http import JsonResponse
from django.views import View

logger = logging.getLogger(__name__)


class FetchPreviewView(View):
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            url = data.get("url", "").strip()
        except (json.JSONDecodeError, AttributeError):
            return JsonResponse({"error": "Invalid JSON body"}, status=400)

        if not url:
            return JsonResponse({"error": "Missing 'url' field"}, status=400)

        logger.info("Preview request received", extra={"url": url})
        
        return JsonResponse({
            "title": None,
            "description": None,
            "favicon": None,
            "message": "Phase 2 not implemented yet"
        })
