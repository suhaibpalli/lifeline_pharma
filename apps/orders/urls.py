from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # Order management
    path('', views.OrderListView.as_view(), name='order_list'),
    path('<str:order_number>/', views.OrderDetailView.as_view(), name='order_detail'),
    
    # Checkout
    path('checkout/', views.checkout_view, name='checkout'),
    
    # Order actions
    path('<str:order_number>/cancel/', views.cancel_order, name='cancel_order'),
    
    # Coupon management
    path('apply-coupon/', views.apply_coupon, name='apply_coupon'),
    path('remove-coupon/', views.remove_coupon, name='remove_coupon'),
    
    # Public tracking
    path('track/<str:order_number>/', views.order_tracking, name='order_tracking'),
]
