from django.db import models
from django.contrib.auth.models import AbstractUser

class UserTier(models.TextChoices):
    FREE="free", "Free"
    PRO="pro", "Pro"
    ENTERPRISE="enterprise", "Enterprise"
    
class User(AbstractUser):
    is_premium = models.BooleanField(default=False)

    tier = models.CharField(max_length=20,choices=UserTier.choices,default=UserTier.FREE)

    def __str__(self):
        return self.username
