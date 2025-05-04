from django.urls import path
from .views import (
    StoreListCreateView, StoreRetrieveUpdateDestroyView,
    CategoryListCreateView, CategoryRetrieveUpdateDestroyView,
    ProductListCreateView, ProductRetrieveUpdateDestroyView,
    ManagerView, StaffView, UserView,
)

urlpatterns = [
    # Store URLs
    path('stores/', StoreListCreateView.as_view(), name='store-list-create'),
    path('stores/<int:pk>/', StoreRetrieveUpdateDestroyView.as_view(), name='store-detail'),

    # Category URLs
    path('categories/', CategoryListCreateView.as_view(), name='category-list-create'),
    path('categories/<int:pk>/', CategoryRetrieveUpdateDestroyView.as_view(), name='category-detail'),

    # Product URLs
    path('products/', ProductListCreateView.as_view(), name='product-list-create'),
    path('products/<int:pk>/', ProductRetrieveUpdateDestroyView.as_view(), name='product-detail'),

    # Manager URLs
    path('stores/<int:store_id>/manager/', ManagerView.as_view(), name='store-manager'),


    # Staff URLs
    path('stores/<int:store_id>/staff/', StaffView.as_view(), name='store-staff'),

    # User URLs
    path('users/', UserView.as_view(), name='user-list-create'),
    path('users/<int:pk>/', UserView.as_view(), name='user-detail'),
]
