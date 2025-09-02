import uuid
from datetime import datetime, timedelta, timezone

import jwt
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response

from .models import BlacklistedRefreshToken, Profile
from .permissions import IsOwnerProfileOrAdmin, IsSelfOrAdmin
from .serializers import ProfileSerializer, SignupSerializer, UserSerializer

User = get_user_model()


# ── JWT helpers ───────────────────────────────────────────
def _now():
    return datetime.now(timezone.utc)


def _encode(payload):
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def make_access_token(user):
    payload = {
        "jti": str(uuid.uuid4()),
        "type": "access",
        "user_id": user.id,
        "role": user.role,
        "iat": int(_now().timestamp()),
        "exp": int((_now() + timedelta(minutes=20)).timestamp()),  # 20min
    }
    return _encode(payload)


def make_refresh_token(user):
    jti = str(uuid.uuid4())
    payload = {
        "jti": jti,
        "type": "refresh",
        "user_id": user.id,
        "iat": int(_now().timestamp()),
        "exp": int((_now() + timedelta(days=7)).timestamp()),  # 7d
    }
    return {"token": _encode(payload), "jti": jti}


def decode_token(token):
    return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])


# ── User ViewSet ─────────────────────────────────────────
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsSelfOrAdmin]

    def get_serializer_class(self):
        if self.action == "create":
            return SignupSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action in ["create", "login"]:
            return [permissions.AllowAny()]
        return super().get_permissions()

    # signup = POST /api/users/
    # login = POST /api/users/login/
    @action(detail=False, methods=["post"], permission_classes=[permissions.AllowAny])
    def login(self, request):
        identifier = request.data.get("username")
        password = request.data.get("password")

        # allow login with email or username
        if "@" in identifier:
            try:
                identifier = User.objects.get(email__iexact=identifier).username
            except User.DoesNotExist:
                pass

        user = authenticate(username=identifier, password=password)
        if not user:
            raise AuthenticationFailed("Invalid credentials")

        access = make_access_token(user)
        refresh = make_refresh_token(user)["token"]

        return Response(
            {"user": UserSerializer(user).data, "access": access, "refresh": refresh}
        )

    @action(detail=False, methods=["post"], permission_classes=[permissions.AllowAny])
    def refresh(self, request):
        token = request.data.get("refresh")
        if not token:
            return Response({"detail": "refresh required"}, status=400)
        try:
            payload = decode_token(token)
        except jwt.ExpiredSignatureError:
            return Response({"detail": "refresh expired"}, status=401)
        except jwt.InvalidTokenError:
            return Response({"detail": "invalid refresh"}, status=401)

        if payload.get("type") != "refresh":
            return Response({"detail": "wrong token type"}, status=401)

        jti = payload.get("jti")
        if BlacklistedRefreshToken.objects.filter(jti=jti).exists():
            return Response({"detail": "refresh revoked"}, status=401)
        BlacklistedRefreshToken.objects.create(jti=jti)

        user = User.objects.get(id=payload["user_id"])
        new_access = make_access_token(user)
        new_refresh = make_refresh_token(user)
        return Response({"access": new_access, "refresh": new_refresh["token"]})

    @action(detail=False, methods=["post"])
    def logout(self, request):
        token = request.data.get("refresh")
        if not token:
            return Response({"detail": "refresh required"}, status=400)
        try:
            payload = decode_token(token)
            if payload.get("type") == "refresh":
                jti = payload.get("jti")
                if not BlacklistedRefreshToken.objects.filter(jti=jti).exists():
                    BlacklistedRefreshToken.objects.create(jti=jti)
        except jwt.InvalidTokenError:
            pass
        return Response(status=status.HTTP_205_RESET_CONTENT)


# ── Profile ViewSet ──────────────────────────────────────
class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerProfileOrAdmin]
