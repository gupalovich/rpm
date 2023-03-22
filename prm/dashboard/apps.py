from django.apps import AppConfig


class DashboardConfig(AppConfig):
    name = "prm.dashboard"
    verbose_name = "Dashboard"
    label = "dashboard"

    def ready(self):
        try:
            import prm.dashboard.signals  # noqa F401
        except ImportError:
            pass
