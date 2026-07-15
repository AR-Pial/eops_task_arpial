from django.db.models import Case, IntegerField, Value, When
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .category_cache import (
    dfs_collect_descendant_ids,
    get_category_tree,
    invalidate_category_tree,
)
from .models import Category, Product
from .permissions import IsAdminOrSuperAdmin
from .serializers import CategorySerializer, ProductSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    lookup_field = "id"
    queryset = Category.objects.select_related("parent").order_by("name")

    def get_permissions(self):
        if self.action in ("list", "retrieve", "tree"):
            return [AllowAny()]
        return [IsAuthenticated(), IsAdminOrSuperAdmin()]

    def perform_create(self, serializer):
        serializer.save()
        invalidate_category_tree()

    def perform_update(self, serializer):
        serializer.save()
        invalidate_category_tree()

    def perform_destroy(self, instance):
        instance.delete()
        invalidate_category_tree()

    @action(detail=False, methods=["get"], url_path="tree")
    def tree(self, request):
        return Response(get_category_tree())


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    lookup_field = "id"

    def get_queryset(self):
        qs = (
            Product.objects.select_related("category")
            .annotate(
                out_of_stock=Case(
                    When(stock=0, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField(),
                )
            )
            .order_by("-is_featured", "out_of_stock", "-created_at")
        )

        category_id = self.request.query_params.get("category")
        include_descendants = self.request.query_params.get(
            "include_descendants", "1"
        ).lower() in ("1", "true", "yes")

        if category_id:
            if include_descendants:
                ids = dfs_collect_descendant_ids(str(category_id))
                qs = qs.filter(category_id__in=ids) if ids else qs.none()
            else:
                qs = qs.filter(category_id=category_id)

        user = self.request.user
        if user.is_authenticated and getattr(user, "user_type", None) in (
            "admin",
            "superadmin",
        ):
            return qs
        return qs.filter(status=Product.Status.ACTIVE)

    def get_permissions(self):
        if self.action in ("list", "retrieve", "related"):
            return [AllowAny()]
        return [IsAuthenticated(), IsAdminOrSuperAdmin()]

    @action(detail=True, methods=["get"], url_path="related")
    def related(self, request, id=None):
        """Recommend products via DFS over the cached category hierarchy."""
        product = self.get_object()
        if not product.category_id:
            return Response([])

        tree = get_category_tree()
        category_id = str(product.category_id)
        # Prefer the parent subtree (siblings + descendants); fall back to self.
        parent_id = tree.get("nodes", {}).get(category_id, {}).get("parent_id")
        root_id = parent_id or category_id
        category_ids = dfs_collect_descendant_ids(root_id, tree)

        related = (
            Product.objects.filter(
                category_id__in=category_ids,
                status=Product.Status.ACTIVE,
            )
            .exclude(pk=product.pk)
            .order_by("-is_featured", "-created_at")[:12]
        )
        return Response(ProductSerializer(related, many=True).data)
