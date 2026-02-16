from rest_framework.throttling import SimpleRateThrottle

class LoginRateThrottle(SimpleRateThrottle):
    scope = "login"

    def get_cache_key(self, request, view):
       
        username = request.data.get("username") or request.data.get("email")
        if username:
            return f"login_throttle:{username}"
        return None  
