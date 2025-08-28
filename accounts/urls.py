# accounts/urls.py
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, login_view, refresh_token_view, register_user, logout_view
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.urls import path, include


router = DefaultRouter()
router.register(r'users', UserViewSet)

urlpatterns = router.urls + [
    path('login/', login_view, name='login'),
    path("refresh/", refresh_token_view, name="refresh"),
    path("register/", register_user, name="register"),
    path('logout/', logout_view, name='logout')
]
