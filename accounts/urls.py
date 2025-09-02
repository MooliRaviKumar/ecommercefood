from rest_framework.routers import DefaultRouter

from .views import ProfileViewSet, UserViewSet

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")
router.register(r"profiles", ProfileViewSet, basename="profile")

urlpatterns = router.urls
