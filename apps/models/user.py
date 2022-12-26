from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db.models import ImageField, TextField, CharField, EmailField, \
    BooleanField

from apps.managers import UserManager


class User(AbstractUser):
    avatar = ImageField(upload_to='authors/', null=True, blank=True)
    bio = TextField(null=True, blank=True)
    # social_accounts = JSONField(null=True, blank=True)
    email = EmailField(max_length=255, unique=True)
    is_active = BooleanField(default=False)
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$')
    phone = CharField(validators=[phone_regex], max_length=17, null=True, blank=True)
    objects = UserManager()

    @property
    def full_name(self):
        return self.first_name + ' ' + self.last_name

