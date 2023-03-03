from allauth.account.forms import SignupForm
from django import forms
from django.contrib.auth import forms as admin_forms
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from django.forms.widgets import TextInput
from django.utils.translation import gettext_lazy as _

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
    phone_regex = RegexValidator(
        regex=r"^8 \(\d{3}\) \d{3}-\d{2}-\d{2}$",
        message=_("Phone number must be in the format: '8 (999) 999-99-99'."),
    )
    phone_number = forms.CharField(
        max_length=30,
        label=_("Телефон"),
        # validators=[phone_regex],
        widget=TextInput(attrs={"type": "tel", "placeholder": _("8 (999) 999-99-99")}),
    )
    referral = forms.CharField(max_length=30, required=False, label=_("Вас пригласил"))

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

    def clean_first_name(self):
        first_name = self.cleaned_data.get("first_name")
        if not first_name:
            raise forms.ValidationError(_("First Name is required."))
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get("last_name")
        if not last_name:
            raise forms.ValidationError(_("Second Name is required."))
        return last_name

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get("phone_number")
        if not phone_number:
            raise forms.ValidationError(_("Phone Number is required."))
        return phone_number

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
            user.phone_number = self.cleaned_data.get("phone_number", "")

            referral = self.cleaned_data.get("referral")
            if referral:
                pass  # referral logic
            user.save()
        return user
