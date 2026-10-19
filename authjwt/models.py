from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

class EmailVerification(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # Guardado como hash sha256, nunca o código em texto puro
    code = models.CharField(max_length=64)
    created_at = models.DateTimeField(default=timezone.now)
    attempts = models.PositiveSmallIntegerField(default=0)
    is_verified = models.BooleanField(default=False)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=settings.VERIFICATION_CODE_MINUTES)

    def __str__(self):
        return f"{self.user.email} - {'verificado' if self.is_verified else 'pendente'}"
