from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from django.utils.translation import gettext_lazy as _

from .forms import UserAdminChangeForm, UserAdminCreationForm
from .models import User, UserSettings


class UserSettingsInline(admin.StackedInline):
    model = UserSettings
    can_delete = False
    verbose_name = "Дополнительная информация"
    fk_name = "user"


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):
    form = UserAdminChangeForm
    add_form = UserAdminCreationForm
    inlines = (UserSettingsInline,)
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
