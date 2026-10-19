import hashlib
import secrets
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import EmailVerification
from .tasks import email_verificacao

User = get_user_model()

def generate_verification_code():
    return f"{secrets.randbelow(1_000_000):06d}"

def hash_code(code):
    return hashlib.sha256(code.encode()).hexdigest()

def send_new_code(user):
    code = generate_verification_code()

    EmailVerification.objects.update_or_create(
        user     = user,
        defaults = {
            "code_hash": hash_code(code),
            "created_at": timezone.now(),
            "attempts": 0,
            "is_verified": False,
        }
    )

    email_verificacao.delay(user.username, user.email, code)

def create_user_with_verification(username, email, password):
    user = User.objects.create_user(
        username  = username,
        email     = email,
        password  = password,
        is_active = False
    )

    send_new_code(user)

    return user
