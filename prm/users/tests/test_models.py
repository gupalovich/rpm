from django.test import TestCase

from .factories import UserFactory, get_user_model

User = get_user_model()


class UserTests(TestCase):
    def setUp(self) -> None:
        self.user_data = {
            "username": "test_user",
            "first_name": "Jane",
            "last_name": "Doe",
        }

    def test_create(self):
        user = UserFactory(**self.user_data)
        self.assertEqual(user.username, self.user_data["username"])

    def test_read(self):
        user = UserFactory(**self.user_data)
        read_user = User.objects.get(id=user.id)
        self.assertEqual(read_user.username, self.user_data["username"])

    def test_update(self):
        new_first_name = "John"
        user = UserFactory(**self.user_data)
        user.first_name = new_first_name
        user.save()
        user.refresh_from_db()
        self.assertEqual(user.first_name, new_first_name)

    def test_delete(self):
        user = UserFactory(**self.user_data)
        user.delete()
        with self.assertRaises(User.DoesNotExist):
            User.objects.get(id=user.id)

    def test_fields(self):
        user = UserFactory(**self.user_data)
        self.assertTrue(user.username)
        self.assertTrue(user.email)
        self.assertTrue(user.first_name)
        self.assertTrue(user.last_name)
        self.assertTrue(user.phone_number)
        self.assertTrue(user.birthday)
        self.assertTrue(user.metamask_wallet)
        self.assertEqual(user.avatar, "avatars/default.png")

    def test_get_absolute_url(self):
        user = UserFactory()
        self.assertEqual(user.get_absolute_url(), f"/dashboard/{user.username}/")
