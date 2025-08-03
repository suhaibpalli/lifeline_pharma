from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    # Product catalog and search
    path('', views.ProductCatalogView.as_view(), name='catalog'),
    path('search/', views.ProductSearchView.as_view(), name='search'),
    
    # Category and manufacturer pages
    path('category/<slug:slug>/', views.CategoryProductsView.as_view(), name='category_products'),
    path('manufacturer/<slug:slug>/', views.ManufacturerProductsView.as_view(), name='manufacturer_products'),
    
    # Product detail and reviews
    path('product/<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('product/<slug:slug>/review/', views.ProductReviewCreateView.as_view(), name='add_review'),
    
    # AJAX endpoints
    path('api/quick-view/<int:product_id>/', views.product_quick_view, name='product_quick_view'),
    path('api/search-suggestions/', views.search_suggestions, name='search_suggestions'),
]
