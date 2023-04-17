from allauth.account.forms import SignupForm
from django import forms
from django.contrib import messages
from django.contrib.auth import forms as admin_forms
from django.contrib.auth import get_user_model
from django.forms.widgets import TextInput
from django.utils.translation import gettext_lazy as _

from .validators import validate_phone_number, validate_profanity

User = get_user_model()


class UserAdminChangeForm(admin_forms.UserChangeForm):
    class Meta(admin_forms.UserChangeForm.Meta):
        model = User


class UserAdminCreationForm(admin_forms.UserCreationForm):
    """
    Form for User Creation in the Admin Area.
    To change user signup, see UserSignupForm and UserSocialSignupForm.
    """

    class Meta(admin_forms.UserCreationForm.Meta):
        model = User

        error_messages = {
            "username": {"unique": _("This username has already been taken.")}
        }


class UserSignupForm(SignupForm):
    """Форма регистрации пользователя"""

    username = forms.CharField(
        max_length=150,
        label=_("Login"),
        widget=TextInput(attrs={"placeholder": _("Login")}),
        validators=[validate_profanity],
    )
    first_name = forms.CharField(
        max_length=30,
        label=_("Имя"),
        widget=TextInput(attrs={"placeholder": _("First Name")}),
    )
    last_name = forms.CharField(
        max_length=30,
        label=_("Фамилия"),
        widget=TextInput(attrs={"placeholder": _("Second Name")}),
    )
    phone_number = forms.CharField(
        max_length=30,
        label=_("Телефон"),
        validators=[validate_phone_number],
        widget=TextInput(attrs={"type": "tel", "placeholder": _("8 (999) 999-99-99")}),
    )
    referral = forms.CharField(
        max_length=150,
        required=False,
        label=_("Вас пригласил"),
        widget=forms.TextInput(attrs={"readonly": "readonly"}),
    )

    field_order = [
        "first_name",
        "phone_number",
        "last_name",
        "password1",
        "username",
        "password2",
        "email",
        "referral",
    ]

    def __init__(self, *args, **kwargs):
        request = kwargs.pop("request", None)

        super().__init__(*args, **kwargs)

        if request:
            self.initial["referral"] = request.GET.get("referral")

        self.fields["email"].label = "Email"
        self.fields["email"].required = True
        self.fields["email"].widget.attrs.update({"placeholder": "mail@gmail.com"})

        self.fields["username"].label = "Login"
        self.fields["username"].widget.attrs.update({"placeholder": "Login"})

        self.fields["password1"].label = _("Пароль")
        self.fields["password1"].widget.attrs.update({"placeholder": "*********"})

        self.fields["password2"].label = _("Повторите пароль")
        self.fields["password2"].widget.attrs.update({"placeholder": "*********"})

    def save(self, request):
        user = super().save(request)
        if user:
            user.phone_number = self.cleaned_data.get("phone_number")

            referral = self.cleaned_data.get("referral")
            if referral:
                try:
                    user.parent = User.objects.get(username=referral)
                except User.DoesNotExist:
                    messages.error(request, _("Реферал не существует"))

            user.save()
        return user
