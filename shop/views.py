from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from .models import Product, CartItem, Profile, Subscription
from .forms import ProfileForm, ProductForm
from django.utils.crypto import get_random_string
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib import messages

def product_list(request):
    query = request.GET.get('q', '')
    sort = request.GET.get('sort', '-id')
    
    products = Product.objects.all()
    
    if query:
        products = products.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query)
        )
    
    products = products.order_by(sort)
    
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'product_list.html', {
        'page_obj': page_obj,
        'products': page_obj.object_list,
        'is_paginated': page_obj.has_other_pages(),
        'query': query,
        'sort': sort,
    })

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'product_detail.html', {'product': product})

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('product_list')
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    item, created = CartItem.objects.get_or_create(user=request.user, product=product)
    if not created:
        item.quantity += 1
        item.save()
    messages.success(request, f'"{product.name}" added to your wishlist!')
    return redirect('cart')

@login_required
def cart_view(request):
    items = CartItem.objects.filter(user=request.user)
    total = sum(item.product.price * item.quantity for item in items)
    return render(request, 'cart.html', {'items': items, 'total': total})

@login_required
def update_cart(request, item_id):
    if request.method == 'POST':
        item = get_object_or_404(CartItem, id=item_id, user=request.user)
        qty = int(request.POST.get('quantity', 1))
        if qty > 0:
            item.quantity = qty
            item.save()
            messages.success(request, 'Quantity updated!')
        return redirect('cart')

@login_required
def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, user=request.user)
    product_name = item.product.name
    item.delete()
    messages.success(request, f'"{product_name}" removed from your wishlist!')
    return redirect('cart')

@login_required
def profile_view(request):
    profile = request.user.profile
    items = CartItem.objects.filter(user=request.user)
    total = sum(item.product.price * item.quantity for item in items)
    
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile)

    if not profile.share_token:
        profile.share_token = get_random_string(length=32)
        profile.save()

    share_url = request.build_absolute_uri(f"/wishlist/{profile.share_token}/")
    
    # Get recent subscribers
    recent_subscribers = request.user.subscribers.order_by('-created_at')[:5]
    
    # Get recent subscriptions
    recent_subscriptions = Subscription.objects.filter(subscriber=request.user).order_by('-created_at')[:5]

    return render(request, 'profile.html', {
        'items': items,
        'form': form,
        'share_url': share_url,
        'is_owner': True,
        'total': total,
        'recent_subscribers': recent_subscribers,
        'recent_subscriptions': recent_subscriptions,
    })

def public_wishlist(request, token):
    profile = get_object_or_404(Profile, share_token=token)
    items = CartItem.objects.filter(user=profile.user)
    is_subscribed = False
    if request.user.is_authenticated:
        is_subscribed = Subscription.objects.filter(
            subscriber=request.user, 
            target=profile.user
        ).exists()
    
    total = sum(item.product.price * item.quantity for item in items)
    
    return render(request, 'public_wishlist.html', {
        'profile': profile, 
        'items': items,
        'is_subscribed': is_subscribed,
        'total': total
    })

@login_required
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'Product "{product.name}" added successfully!')
            return redirect('product_list')
    else:
        form = ProductForm()
    return render(request, 'add_product.html', {'form': form})

@login_required
def subscribe(request, username):
    target = get_object_or_404(User, username=username)
    if target != request.user:
        Subscription.objects.get_or_create(subscriber=request.user, target=target)
        messages.success(request, f'You subscribed to {username}!')
    return redirect('public_profile', username=target.username)

@login_required
def unsubscribe(request, username):
    target = get_object_or_404(User, username=username)
    Subscription.objects.filter(subscriber=request.user, target=target).delete()
    messages.success(request, f'You unsubscribed from {username}.')
    return redirect('public_profile', username=target.username)

@login_required
def subscribers_list(request):
    subscribers = request.user.subscribers.all()
    return render(request, 'subscribers_list.html', {'subscribers': subscribers})

@login_required
def subscriptions_list(request):
    subscriptions = Subscription.objects.filter(subscriber=request.user)
    return render(request, 'subscriptions_list.html', {'subscriptions': subscriptions})

@login_required
def public_profile(request, username):
    target_user = get_object_or_404(User, username=username)
    items = CartItem.objects.filter(user=target_user)
    total = sum(item.product.price * item.quantity for item in items)
    
    is_subscribed = False
    if request.user.is_authenticated:
        is_subscribed = Subscription.objects.filter(
            subscriber=request.user, 
            target=target_user
        ).exists()
    
    share_url = None
    if target_user == request.user:
        share_url = request.build_absolute_uri(
            f"/wishlist/{target_user.profile.share_token}/"
        )
        
    # Check if users are mutual followers
    mutual_follow = False
    if request.user.is_authenticated and target_user != request.user:
        mutual_follow = Subscription.objects.filter(
            subscriber=target_user,
            target=request.user
        ).exists() and is_subscribed

    return render(request, 'profile.html', {
        'user': target_user,
        'items': items,
        'share_url': share_url,
        'form': None,
        'is_subscribed': is_subscribed,
        'is_owner': target_user == request.user,
        'total': total,
        'mutual_follow': mutual_follow
    })

@login_required
def search_users(request):
    query = request.GET.get('q', '')
    users = []
    
    if query:
        users = User.objects.filter(
            Q(username__icontains=query) | 
            Q(first_name__icontains=query) | 
            Q(last_name__icontains=query)
        ).exclude(id=request.user.id)
    
    return render(request, 'search_users.html', {
        'users': users,
        'query': query
    })