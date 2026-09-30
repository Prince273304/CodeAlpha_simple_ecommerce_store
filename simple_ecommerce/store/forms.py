from django import forms
from django.contrib.auth.models import User
from .models import Order


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Create a password'}),
        min_length=6,
        help_text="Password must be at least 6 characters."
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm your password'}),
        label="Confirm Password"
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Choose a username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'your.email@example.com'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with that email already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', "Passwords do not match.")
        return cleaned_data


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            'full_name', 'email', 'phone',
            'address', 'city', 'state', 'postal_code', 'country',
            'payment_method', 'notes'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'John Doe'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'john@example.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1 (555) 123-4567'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '123 Market Street, Apt 4B'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'New York'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'NY'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '10001'}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'United States'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional delivery notes or apartment instructions...'}),
        }
