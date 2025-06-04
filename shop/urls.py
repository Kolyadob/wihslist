from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('signup/', views.signup, name='signup'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_view, name='cart'),
    path('cart/update/<int:item_id>/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('profile/', views.profile_view, name='profile'),
    path('wishlist/<str:token>/', views.public_wishlist, name='public_wishlist'),
    path('add-product/', views.add_product, name='add_product'),
    path('subscribe/<str:username>/', views.subscribe, name='subscribe'),
    path('unsubscribe/<str:username>/', views.unsubscribe, name='unsubscribe'),
    path('subscribers/', views.subscribers_list, name='subscribers_list'),
    path('subscriptions/', views.subscriptions_list, name='subscriptions_list'),
    path('user/<str:username>/', views.public_profile, name='public_profile'),
]