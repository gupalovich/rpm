from django.db import models
import base64


# Create your models here.

class TokenReward(models.Model):
    buyer_id = models.IntegerField()
    buyer_wallet_id = models.CharField(max_length=255)
    referral_id = models.IntegerField()
    referral_wallet_id = models.CharField(max_length=255)
    amount = models.CharField(max_length=255)
    reward = models.CharField(max_length=255)
    purchase_date = models.DateTimeField


class TokenPurchase(models.Model):
    buyer_id = models.IntegerField()
    buyer_wallet_id = models.CharField(max_length=255)
    seller_id = models.IntegerField()
    seller_wallet_id = models.CharField(max_length=255)
    amount = models.CharField(max_length=255)
    sum = models.CharField(max_length=255)
    reward = models.CharField(max_length=255)
    purchase_date = models.DateTimeField

class Settings(models.Model):
    user_id = models.IntegerField()
    birthday = models.DateField(null=True)
    country_id = models.IntegerField()
    city = models.CharField(max_length=45)
    _photo_big = models.TextField(db_column='photo', blank=True)

    def set_photo(self, photo):
        self._photo_big = base64.encodestring(photo)

    def get_photo(self):
        return base64.decodestring(self._photo_big)

    photo = property(get_photo, set_photo)
    vk = models.CharField(max_length=45, null=True)
    instagram = models.CharField(max_length=45, null=True)
    telegram = models.CharField(max_length=45, null=True)
    ok = models.CharField(max_length=45, null=True)
    youtube = models.CharField(max_length=45, null=True)


class Country(models.Model):
    country_name_EN = models.CharField(max_length=45, null=True)
    country_name_RU = models.CharField(max_length=45)




