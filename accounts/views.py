# accounts/views.py
from rest_framework import viewsets
from .models import User
from .serializers import UserSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from accounts.authentication import CustomJWTAuthentication
import jwt
from django.conf import settings
from datetime import datetime, timedelta
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.shortcuts import render, redirect
# accounts/views.py
from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
import uuid

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    authentication_classes = [CustomJWTAuthentication]  

    permission_classes = [IsAuthenticated]

@api_view(['POST'])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')
    
    try:
        user = User.objects.get(username=username)
        if not user.check_password(password):
            return Response({
                "error": "Invalid credentials"
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Generate token with jti claim
        refresh = RefreshToken.for_user(user)
        refresh.set_jti()
        
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'username': user.username,
                'email': user.email,
                'role': user.role
            }
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({
            "error": "User not found"
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
def refresh_token_view(request):
    refresh_token = request.data.get("refresh_token")
    if not refresh_token:
        return Response({"error": "Refresh token required"}, status=400)

    try:
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=["HS256"])
        user = User.objects.get(id=payload["user_id"])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, User.DoesNotExist):
        return Response({"error": "Invalid or expired refresh token"}, status=401)

    # Issue new access token (20 min)
    access_payload = {
        "user_id": user.id,
        "exp": datetime.utcnow() + timedelta(minutes=20)
    }
    access_token = jwt.encode(access_payload, settings.SECRET_KEY, algorithm="HS256")

    return Response({"access_token": access_token})

@csrf_exempt
def register_user(request):
    if request.method == "POST":
        import json
        body = json.loads(request.body.decode('utf-8'))  # read JSON payload

        username = body.get("username")
        email = body.get("email")
        password = body.get("password")
        role = body.get("role", "customer")
        profile_image_url = body.get("profile_image_url", "")

        if User.objects.filter(username=username).exists():
            return JsonResponse({"error": "Username already exists"}, status=400)

        User.objects.create_user(
            username=username,
            email=email,
            password=password,
            role=role,
            profile_image_url=profile_image_url
        )

        return JsonResponse({"message": "User registered successfully!"}, status=201)

    return JsonResponse({"error": "Invalid request"}, status=400)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    try:
        refresh_token = request.data.get("refresh_token")
        if not refresh_token:
            return Response({"error": "Refresh token required"}, status=status.HTTP_400_BAD_REQUEST)

        # Create token with verify=False to avoid immediate verification
        token = RefreshToken(refresh_token, verify=False)
        
        # Add jti claim if missing
        if 'jti' not in token:
            token.set_jti()
            
        # Now verify and blacklist
        token.verify()
        token.blacklist()
        
        return Response({
            "message": "Logged out successfully"
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            "error": f"Invalid or expired token: {str(e)}"
        }, status=status.HTTP_400_BAD_REQUEST)
