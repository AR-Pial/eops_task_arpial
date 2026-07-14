from django.contrib import admin
from django.urls import include, path

from apps.products.urls import category_urlpatterns, product_urlpatterns

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/categories/", include(category_urlpatterns)),
    path("api/products/", include(product_urlpatterns)),
    path("api/orders/", include("apps.orders.urls")),
    path("api/payments/", include("apps.payments.urls")),
]
