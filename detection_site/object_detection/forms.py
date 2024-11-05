from django import forms
from .models import ImageFeed
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class ImageFeedForm(forms.ModelForm):
    class Meta:
        model = ImageFeed
        fields = ['image']

class ImageUploadForm(forms.ModelForm):
    class Meta:
        model = ImageFeed
        fields = ['image']

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
