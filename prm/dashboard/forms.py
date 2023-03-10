from django import forms
from django.contrib.auth import get_user_model, password_validation
from django.utils.translation import gettext_lazy as _

from .validators import (
    validate_image_max_pixel_size,
    validate_image_min_pixel_size,
    validate_image_size,
)

User = get_user_model()


class BuyTokenForm(forms.Form):
    token_amount = forms.IntegerField(
        label="",
        widget=forms.NumberInput(attrs={"placeholder": _("Введите кол-во токенов")}),
    )
    token_price_usdt = forms.DecimalField(
        label="",
        widget=forms.NumberInput(attrs={"placeholder": _("Стоимость USDT")}),
        max_digits=12,
        decimal_places=4,
    )

    def clean_token_amount(self):
        token_amount = self.cleaned_data.get("token_amount", None)
        if token_amount <= 0:
            raise forms.ValidationError(_("Неверное количество."))
        return token_amount

    def clean_token_price_usdt(self):
        token_price_usdt = self.cleaned_data.get("token_price_usdt", None)
        if token_price_usdt <= 0:
            raise forms.ValidationError(_("Неверное количество."))
        return token_price_usdt


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


class ProfileUserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "birthday",
            "city",
            "metamask_wallet",
            # don't add password/password1 here
        ]

    city = forms.CharField(label=_("Город"), required=False)
    birthday = forms.DateField(
        label=_("Дата рождения"),
        required=False,
        widget=forms.TextInput(attrs={"type": "date"}),
    )
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["city"].initial = self.instance.settings.city
        self.fields["birthday"].initial = self.instance.settings.birthday

    def save(self, commit=True):
        """
        Save the updated user information and the new password (if entered).
        """
        user = super().save(commit=False)
        password = self.cleaned_data.get("password")
        user.settings.city = self.cleaned_data["city"]
        user.settings.birthday = self.cleaned_data["birthday"]

        if password:
            user.set_password(password)

        if commit:
            user.settings.save()
            user.save()

        return user
