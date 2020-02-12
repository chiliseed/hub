from django.http import JsonResponse
from django.views.defaults import page_not_found, server_error


def custom_404_handler(request, *args, **kwargs):
    """
    View that is called for generic 404 errors. For API views, it returns json response.
    For regular views it returns generic django page not found template.
    """
    if request.path.startswith("/api"):
        return JsonResponse({"details": "Page not found"}, status=404)
    return page_not_found(request, *args, **kwargs)


def custom_500_handler(request, *args, **kwargs):
    """
    Generic 500 error. For API views, it returns json response.
    For regular views it returns generic django server error template.
    """
    if request.path.startswith("/api"):
        return JsonResponse({"detail": "Server error"}, status=500)
    return server_error(request, *args, **kwargs)
