
from .serializers import CadasterSerializer, LoginSerializer, VerifyEmailSerializer, ResendCodeSerializer, UserSerializer
from .services import send_new_code
from rest_framework.views import APIView
from rest_framework.generics import RetrieveUpdateDestroyAPIView
from django.contrib.auth import get_user_model
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import IsAuthenticated, AllowAny

User = get_user_model()

class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        return Response(serializer.validated_data, status=status.HTTP_200_OK)

class ResendCodeView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResendCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = User.objects.filter(email__iexact=serializer.validated_data["email"], is_active=False).first()
        if user:
            send_new_code(user)

        # Mesma resposta sempre, para não revelar quais emails estão cadastrados
        return Response({"detail": "Se o email estiver pendente, um novo código foi enviado."})

class CadasterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CadasterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"detail": "Conta criada. Enviamos um código para o seu email."},
            status=status.HTTP_201_CREATED
        )
    
class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer

# A conta é sempre a do usuário logado, então ninguém mexe na conta de outro
class MeView(RetrieveUpdateDestroyAPIView):
    serializer_class   = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
