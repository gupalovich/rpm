from django.apps import AppConfig


class UsersConfig(AppConfig):
    name = "prm.users"
    verbose_name = "Пользователи"

    def ready(self):
        try:
            import prm.users.signals  # noqa F401
        except ImportError:
            pass
