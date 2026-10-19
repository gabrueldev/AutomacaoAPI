
from rest_framework import serializers
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils.crypto import constant_time_compare
from .services import create_user_with_verification, hash_code
from .models import EmailVerification
from .tasks import email_boas_vindas
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()

class CadasterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    email    = serializers.EmailField()

    class Meta:
        model = User
        fields = ["username", "email", "password"]

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Email já cadastrado")
        return value.lower()

    def create(self, validated_data):
        return create_user_with_verification(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
        )

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, validators=[validate_password])

    class Meta:
        model = User
        fields = ["id", "username", "email", "password"]
        read_only_fields = ["id", "email"]

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        instance = super().update(instance, validated_data)
        if password:
            instance.set_password(password)
            instance.save()
        return instance

class VerifyEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField()

    def validate(self, attrs):
        verification = EmailVerification.objects.select_related("user").filter(
            user__email__iexact=attrs["email"]
        ).first()

        if not verification or verification.is_verified:
            raise serializers.ValidationError("Código inválido")
        if verification.is_expired():
            raise serializers.ValidationError("Código expirado, peça um novo")
        if verification.attempts >= settings.VERIFICATION_MAX_ATTEMPTS:
            raise serializers.ValidationError("Muitas tentativas, peça um novo código")
        if not constant_time_compare(verification.code, hash_code(attrs["code"])):
            verification.attempts += 1
            verification.save(update_fields=["attempts"])
            raise serializers.ValidationError("Código incorreto")

        user = verification.user
        user.is_active = True
        user.save()

        verification.is_verified = True
        verification.save()

        email_boas_vindas.delay(user.username, user.email)

        refresh = RefreshToken.for_user(user)

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token)
        }

class ResendCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()

class LoginSerializer(TokenObtainPairSerializer):

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token['username'] = user.username
        token['email']    = user.email

        return token
