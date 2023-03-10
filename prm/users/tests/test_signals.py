from django.test import TestCase

from .factories import UserFactory


class UserSignalsTests(TestCase):
    def setUp(self) -> None:
        self.user = UserFactory()

    def test_create_user_settings(self):
        self.assertTrue(self.user.settings)
        self.assertTrue(self.user.settings.city)
        self.assertTrue(self.user.settings.birthday)
