# from datetime import date

# from django.core.files.uploadedfile import SimpleUploadedFile
# from django.test import TestCase

# from prm.users.tests.factories import UserFactory

# from ..forms import AvatarUpdateForm, CustomUserUpdateForm


# class AvatarUpdateFormTests(TestCase):
#     def setUp(self):
#         base_path = "backend/dashboard/tests/assets"
#         self.avatar_path = f"{base_path}/test_avatar.jpg"
#         self.avatar_sm_path = f"{base_path}/test_avatar_sm.jpg"
#         self.avatar_lg_path = f"{base_path}/test_avatar_lg.jpg"

#     def test_valid_form(self):
#         # create a fake image file to upload
#         file_data = open(self.avatar_path, "rb").read()
#         uploaded_file = SimpleUploadedFile(
#             "image.jpg", file_data, content_type="image/jpeg"
#         )
#         form_data = {"avatar": uploaded_file}
#         form = AvatarUpdateForm(data=form_data, files=form_data)
#         self.assertTrue(form.is_valid())

#     def test_empty_form(self):
#         form_data = {}
#         form = AvatarUpdateForm(data=form_data, files=form_data)
#         self.assertFalse(form.is_valid())
#         self.assertIn("avatar", form.errors)

#     def test_invalid_image_sm(self):
#         # create a fake image file that is too small to pass the validator
#         file_data = open(self.avatar_sm_path, "rb").read()
#         uploaded_file = SimpleUploadedFile(
#             "small_image.jpg", file_data, content_type="image/jpeg"
#         )
#         form_data = {"avatar": uploaded_file}
#         form = AvatarUpdateForm(data=form_data, files=form_data)
#         self.assertFalse(form.is_valid())
#         self.assertIn("avatar", form.errors)

#     def test_invalid_image_lg(self):
#         # create a fake image file that is too small to pass the validator
#         file_data = open(self.avatar_lg_path, "rb").read()
#         uploaded_file = SimpleUploadedFile(
#             "large_image.jpg", file_data, content_type="image/jpeg"
#         )
#         form_data = {"avatar": uploaded_file}
#         form = AvatarUpdateForm(data=form_data, files=form_data)
#         self.assertFalse(form.is_valid())
#         self.assertIn("avatar", form.errors)


# class CustomUserUpdateFormTests(TestCase):
#     def setUp(self):
#         self.user = UserFactory()

#     def test_valid_data(self):
#         form = CustomUserUpdateForm(
#             data={
#                 "name": "Test User",
#                 "email": "testuser@example.com",
#                 "phone_number": "1234567890",
#                 "date_of_birth": "1990-01-01",
#                 "city": "Test City",
#                 "metamask_wallet": "0x1234567890",
#                 "password": "newpass123",
#                 "password1": "newpass123",
#             },
#             instance=self.user,
#         )
#         self.assertTrue(form.is_valid())
#         user = form.save()
#         self.assertEqual(user.name, "Test User")
#         self.assertEqual(user.phone_number, "1234567890")
#         self.assertEqual(user.date_of_birth, date(1990, 1, 1))
#         self.assertEqual(user.city, "Test City")
#         self.assertEqual(user.metamask_wallet, "0x1234567890")
#         self.assertTrue(user.check_password("newpass123"))

#     def test_password_mismatch(self):
#         form = CustomUserUpdateForm(
#             data={
#                 "name": "Test User",
#                 "email": "testuser@example.com",
#                 "phone_number": "1234567890",
#                 "date_of_birth": "1990-01-01",
#                 "city": "Test City",
#                 "metamask_wallet": "0x1234567890",
#                 "password": "newpass123",
#                 "password1": "mismatch",
#             },
#             instance=self.user,
#         )
#         self.assertFalse(form.is_valid())
#         self.assertIn("password1", form.errors)

#     def test_weak_password(self):
#         form = CustomUserUpdateForm(
#             data={
#                 "name": "Test User",
#                 "email": "testuser@example.com",
#                 "phone_number": "1234567890",
#                 "date_of_birth": "1990-01-01",
#                 "city": "Test City",
#                 "metamask_wallet": "0x1234567890",
#                 "password": "password",
#                 "password1": "password",
#             },
#             instance=self.user,
#         )
#         self.assertFalse(form.is_valid())
#         self.assertIn("password", form.errors)
