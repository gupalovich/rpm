from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = "prm.core"
    verbose_name = "Core"

    def ready(self):
        try:
            import prm.core.signals  # noqa F401
        except ImportError:
            pass
