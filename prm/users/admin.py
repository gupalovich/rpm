from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from prm.users.forms import UserAdminChangeForm, UserAdminCreationForm

User = get_user_model()


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):
    form = UserAdminChangeForm
    add_form = UserAdminCreationForm
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            _("Персональная информация"),
            {
                "fields": (
                    "parent",
                    "first_name",
                    "last_name",
                    "email",
                    "phone_number",
                    "avatar",
                )
            },
        ),
        (
            _("Кошелек"),
            {
                "fields": (
                    "token_balance",
                    "metamask_wallet",
                    "metamask_confirmed",
                )
            },
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    list_display = [
        "username",
        "first_name",
        "last_name",
        "is_superuser",
    ]
    search_fields = ["username"]
