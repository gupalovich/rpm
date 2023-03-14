from django.core.exceptions import ValidationError
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
        user = UserFactory(parent=UserFactory(), **self.user_data)
        # parent
        self.assertTrue(user.parent.username)
        # fields
        self.assertTrue(user.username)
        self.assertTrue(user.email)
        self.assertTrue(user.first_name)
        self.assertTrue(user.last_name)
        self.assertTrue(user.phone_number)
        self.assertEqual(user.avatar, "avatars/default.png")
        # wallet
        self.assertTrue(user.token_balance)
        self.assertTrue(user.metamask_wallet)
        self.assertIsInstance(user.metamask_confirmed, bool)
        # settings
        self.assertTrue(user.settings.birthday)
        self.assertTrue(user.settings.city)

    def test_parent_set_null(self):
        parent = UserFactory()
        user = UserFactory(parent=parent, **self.user_data)
        self.assertEqual(user.parent, parent)
        parent.delete()
        user.refresh_from_db()
        self.assertEqual(user.parent, None)

    def test_parent_children_relation(self):
        parent = UserFactory(**self.user_data)
        users = [UserFactory(parent=parent), UserFactory(parent=parent), UserFactory()]
        # Test relations
        self.assertFalse(parent.parent)
        self.assertEqual(parent.children.count(), 2)
        # user1
        self.assertEqual(users[0].parent, parent)
        self.assertEqual(users[0].children.count(), 0)
        # user2
        self.assertEqual(users[1].parent, parent)
        self.assertEqual(users[1].children.count(), 0)
        # user3
        self.assertFalse(users[2].parent)
        self.assertEqual(users[2].children.count(), 0)

    def test_get_absolute_url(self):
        user = UserFactory()
        self.assertEqual(user.get_absolute_url(), f"/dashboard/{user.username}/")

    def test_clean_parent_not_equal_self(self):
        user = UserFactory()
        # Ensure the clean method raises a validation error
        with self.assertRaises(ValidationError):
            user.parent = user
            user.clean()

    def test_clean_metamask_wallet_blank(self):
        user = UserFactory(metamask_wallet="", metamask_confirmed=False)
        user.metamask_wallet = "123"
        user.metamask_confirmed = True
        user.clean()
        user.save()

    def test_clean_metamask_wallet_confirmed(self):
        user = UserFactory(metamask_confirmed=True)
        with self.assertRaises(ValidationError):
            user.metamask_wallet = "123"
            user.clean()

    def test_clean_metamask_wallet_confirmed_to_blank(self):
        user = UserFactory(metamask_wallet="123", metamask_confirmed=True)
        with self.assertRaises(ValidationError):
            user.metamask_wallet = ""
            user.clean()

    def test_clean_metamask_wallet_not_confirmed(self):
        user = UserFactory(metamask_confirmed=False)
        user.metamask_wallet = "123"
        user.clean()
        user.save()
        # Try to change unconfirmed wallet
        user.metamask_wallet = "1234"
        user.clean()

    def test_property_full_name(self):
        user = UserFactory()
        self.assertEqual(user.full_name, f"{user.first_name} {user.last_name}")
