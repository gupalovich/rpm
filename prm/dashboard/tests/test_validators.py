"""
TODO
"""

# import unittest
# from io import BytesIO

# from django.core.exceptions import ValidationError
# from django.core.files.uploadedfile import SimpleUploadedFile
# from django.utils.translation import gettext_lazy as _
# from PIL import Image

# from ..validators import (
#     validate_image_max_pixel_size,
#     validate_image_min_pixel_size,
#     validate_image_size,
# )

# class TestImageValidationFunctions(unittest.TestCase):
#     def setUp(self):
#         pass

# def test_validate_image_size_valid(self):
# Test that a valid image passes validation
# try:
# validate_image_size(self.image, max_size=500000)
# except ValidationError:
#     self.fail("validate_image_size() raised ValidationError unexpectedly!")

# def test_validate_image_size_invalid(self):
#     # Test that an invalid image raises a ValidationError
#     invalid_image = self.image.copy()
#     # Set the file size to be larger than the maximum allowed size (100kb)
#     invalid_image_file = io.BytesIO()
#     invalid_image.save(invalid_image_file, "JPEG")
#     invalid_image_file.seek(0)
#     invalid_image_file.size = 200000
#     with self.assertRaisesMessage(
#         ValidationError, _("The maximum image size is 200kb")
#     ):
#         validate_image_size(invalid_image_file)

# def test_validate_image_min_pixel_size_valid(self):
#     # Test that a valid image passes validation
#     try:
#         validate_image_min_pixel_size(self.image, min_width=100, min_height=100)
#     except ValidationError:
#         self.fail(
#             "validate_image_min_pixel_size() raised ValidationError unexpectedly!"
#         )

# def test_validate_image_min_pixel_size_invalid(self):
#     # Test that an invalid image raises a ValidationError
#     invalid_image = self.image.copy()
#     # Set the image dimensions to be smaller than the minimum allowed size (100x100)
#     invalid_image = invalid_image.resize((50, 50))
#     with self.assertRaisesMessage(
#         ValidationError, _("The minimum pixel size is 100 x 100.")
#     ):
#         validate_image_min_pixel_size(invalid_image)

# def test_validate_image_max_pixel_size_valid(self):
#     # Test that a valid image passes validation
#     try:
#         validate_image_max_pixel_size(self.image, max_width=1000, max_height=1000)
#     except ValidationError:
#         self.fail(
#             "validate_image_max_pixel_size() raised ValidationError unexpectedly!"
#         )

# def test_validate_image_max_pixel_size_invalid(self):
#     # Test that an invalid image raises a ValidationError
#     invalid_image = self.image.copy()
#     # Set the image dimensions to be larger than the maximum allowed size (1000x1000)
#     invalid_image = invalid_image.resize((1200, 1200))
#     with self.assertRaisesMessage(
#         ValidationError, _("The maximum pixel size is 1000 x 1000.")
#     ):
#         validate_image_max_pixel_size(invalid_image)
