from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError

class UserTier(models.TextChoices):
    FREE="free", "Free"
    PRO="pro", "Pro"
    ENTERPRISE="enterprise", "Enterprise"
    
class User(AbstractUser):
    is_premium = models.BooleanField(default=False)
    tier = models.CharField(max_length=20,choices=UserTier.choices,default=UserTier.FREE)

    def clean(self):
        super().clean()
        if self.is_premium and self.tier == UserTier.FREE:
            raise ValidationError("A premium user cannot have a 'free' tier.")
        if not self.is_premium and self.tier != UserTier.FREE:
            raise ValidationError("A non-premium user must be on the 'free' tier.")

    def __str__(self):
        return self.username
