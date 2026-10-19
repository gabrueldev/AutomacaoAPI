from django.urls import path
from .views import CadasterView, LoginView, MeView, VerifyEmailView, ResendCodeView

urlpatterns = [
    path("cadaster/", CadasterView.as_view(), name="cadaster"),
    path("verify/", VerifyEmailView.as_view(), name="verify"),
    path("verify/resend/", ResendCodeView.as_view(), name="resend"),
    path("login/", LoginView.as_view(), name="login"),
    path("me/", MeView.as_view(), name="me"),
]
