from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from .models import Product, CartItem, Profile
from .forms import ProfileForm
from django.utils.crypto import get_random_string
from django.contrib.auth.models import User

# Главная страница: список товаров
def product_list(request):
    products = Product.objects.all()
    return render(request, 'product_list.html', {'products': products})

# Детали товара
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'product_detail.html', {'product': product})

# Регистрация пользователя
def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('product_list')
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})

# Добавление в корзину
@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    item, created = CartItem.objects.get_or_create(user=request.user, product=product)
    if not created:
        item.quantity += 1
        item.save()
    return redirect('cart')

# Просмотр корзины
@login_required
def cart_view(request):
    items = CartItem.objects.filter(user=request.user)
    return render(request, 'cart.html', {'items': items})

# Обновление количества
@login_required
def update_cart(request, item_id):
    if request.method == 'POST':
        item = get_object_or_404(CartItem, id=item_id, user=request.user)
        qty = int(request.POST.get('quantity', 1))
        if qty > 0:
            item.quantity = qty
            item.save()
        return redirect('cart')

# Удаление из корзины
@login_required
def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, user=request.user)
    item.delete()
    return redirect('cart')

# Профиль пользователя
@login_required
def profile_view(request):
    profile = request.user.profile
    items = CartItem.objects.filter(user=request.user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile)

    if not profile.share_token:
        profile.share_token = get_random_string(length=32)
        profile.save()

    share_url = request.build_absolute_uri(f"/wishlist/{profile.share_token}/")

    return render(request, 'profile.html', {'items': items, 'form': form, 'share_url': share_url})

# Просмотр чужого wishlist по токену
def public_wishlist(request, token):
    profile = get_object_or_404(Profile, share_token=token)
    items = CartItem.objects.filter(user=profile.user)
    return render(request, 'public_wishlist.html', {'profile': profile, 'items': items})

# Просмотр списка друзей
@login_required
def friends_list(request):
    profile = request.user.profile
    return render(request, 'friends.html', {'friends': profile.friends.all()})

# Добавление друга по username
@login_required
def add_friend(request, username):
    target_user = get_object_or_404(User, username=username)
    if target_user != request.user:
        request.user.profile.friends.add(target_user.profile)
    return redirect('friends_list')
