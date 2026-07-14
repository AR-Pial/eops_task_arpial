from rest_framework.routers import DefaultRouter

from .views import CategoryViewSet, ProductViewSet

product_router = DefaultRouter()
product_router.register("", ProductViewSet, basename="product")

category_router = DefaultRouter()
category_router.register("", CategoryViewSet, basename="category")

product_urlpatterns = product_router.urls
category_urlpatterns = category_router.urls
