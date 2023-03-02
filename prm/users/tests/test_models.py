from django.test import TestCase

from .factories import UserFactory


class UserTests(TestCase):
    """TODO: tests"""

    def setUp(self) -> None:
        self.user = UserFactory()

    # def test_get_absolute_url(self):
    #     assert self.user.get_absolute_url() == f"/dashboard/{self.user.username}/"
