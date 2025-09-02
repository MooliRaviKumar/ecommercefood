import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

User = get_user_model()


class CustomJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth = request.headers.get("Authorization") or ""
        if not auth.startswith("Bearer "):
            return None

        token = auth.split(" ", 1)[1]
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed("Access token expired")
        except jwt.InvalidTokenError:
            raise AuthenticationFailed("Invalid token")

        if payload.get("type") != "access":
            raise AuthenticationFailed("Not an access token")

        try:
            user = User.objects.get(id=payload["user_id"], is_active=True)
        except User.DoesNotExist:
            raise AuthenticationFailed("User not found")

        return (user, token)
