from django import forms
from django.contrib.auth import get_user_model, password_validation
from django.utils.translation import gettext_lazy as _

from .validators import (
    validate_image_max_pixel_size,
    validate_image_min_pixel_size,
    validate_image_size,
)

User = get_user_model()


class AvatarUpdateForm(forms.Form):
    avatar = forms.ImageField(
        required=False,
        validators=[
            validate_image_size,
            validate_image_min_pixel_size,
            validate_image_max_pixel_size,
        ],
    )

    def clean_avatar(self):
        avatar = self.cleaned_data.get("avatar", None)
        if not avatar:
            raise forms.ValidationError(_("Avatar is required."))
        return avatar


class CustomUserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "date_of_birth",
            "city",
            "metamask_wallet",
        ]

    password = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        required=False,
    )
    password1 = forms.CharField(
        label=_("Password confirmation"),
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        strip=False,
        required=False,
    )

    def clean_password(self):
        """
        Validate that the password is as per the required password policy.
        """
        password = self.cleaned_data.get("password")
        if password:
            password_validation.validate_password(password)
        return password

    def clean_password1(self):
        """
        Validate that the two password inputs match.
        """
        password1 = self.cleaned_data.get("password1")
        password = self.cleaned_data.get("password")
        if password and password1 and password != password1:
            raise forms.ValidationError(_("Passwords do not match"))
        return password1

    def save(self, commit=True):
        """
        Save the updated user information and the new password (if entered).
        """
        user = super().save(commit=False)
        password = self.cleaned_data.get("password")
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user
