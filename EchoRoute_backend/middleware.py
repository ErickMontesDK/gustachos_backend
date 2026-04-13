from django.http import JsonResponse
from django.conf import settings

class DemoModeMiddleware:
    """
    Middleware to block database modifications when running in Demo Mode.
    Intercepts POST, PUT, PATCH, and DELETE requests and returns a 403 Forbidden.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.unsafe_methods = ['POST', 'PUT', 'PATCH', 'DELETE']
        self.exempt_paths = [
            '/api/auth/login/',
            '/api/auth/refresh/'
        ]

    def __call__(self, request):
        if getattr(settings, 'DEMO_MODE', False):
            if request.method in self.unsafe_methods:
                # Allow authentication to work
                if any(request.path.startswith(path) for path in self.exempt_paths):
                    pass
                else:
                    return JsonResponse(
                        {"error": "Demo mode active: Database modifications are disabled."},
                        status=403
                    )
        
        response = self.get_response(request)
        return response
