from django.apps import AppConfig

from prm.core.utils import load_profanity_words


class UsersConfig(AppConfig):
    name = "prm.users"
    verbose_name = "Пользователи"
    profanity_words = load_profanity_words()

    def ready(self):
        try:
            import prm.users.signals  # noqa F401
        except ImportError:
            pass
