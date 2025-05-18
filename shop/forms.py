from django import forms
from .models import Profile, Product

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['image']

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'image']
