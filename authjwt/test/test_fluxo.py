
import re
import pytest
from datetime import timedelta
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APIClient

from ..models import EmailVerification

DADOS = {"username": "joao", "email": "joao@example.com", "password": "SenhaForte!2026"}

@pytest.fixture
def client():
    return APIClient()

def codigo_do_email(mailoutbox):
    return re.search(r"\b(\d{6})\b", mailoutbox[-1].body).group(1)

def cadastrar(client):
    response = client.post("/api/cadaster/", DADOS)
    assert response.status_code == 201
    return response

@pytest.mark.django_db
def test_cadastro_envia_codigo_e_nao_devolve_token(client, mailoutbox):
    response = cadastrar(client)

    assert "access" not in response.data
    assert len(mailoutbox) == 1
    assert mailoutbox[0].to == [DADOS["email"]]
    assert User.objects.get(username="joao").is_active is False

@pytest.mark.django_db
def test_codigo_salvo_como_hash(client, mailoutbox):
    cadastrar(client)
    verification = EmailVerification.objects.get()
    assert verification.code != codigo_do_email(mailoutbox)

@pytest.mark.django_db
def test_verificar_ativa_conta_e_manda_boas_vindas(client, mailoutbox):
    cadastrar(client)
    response = client.post("/api/verify/", {"email": DADOS["email"], "code": codigo_do_email(mailoutbox)})

    assert response.status_code == 200
    assert "access" in response.data
    assert User.objects.get(username="joao").is_active is True
    assert mailoutbox[-1].subject == "Bem-Vindo!!"

@pytest.mark.django_db
def test_login_antes_de_verificar(client, mailoutbox):
    cadastrar(client)
    response = client.post("/api/login/", {"username": "joao", "password": DADOS["password"]})
    assert response.status_code == 401

@pytest.mark.django_db
def test_login_depois_de_verificar(client, mailoutbox):
    cadastrar(client)
    client.post("/api/verify/", {"email": DADOS["email"], "code": codigo_do_email(mailoutbox)})
    response = client.post("/api/login/", {"username": "joao", "password": DADOS["password"]})
    assert response.status_code == 200
    assert "access" in response.data

@pytest.mark.django_db
def test_email_duplicado(client, mailoutbox):
    cadastrar(client)
    response = client.post("/api/cadaster/", {**DADOS, "username": "outro", "email": "JOAO@example.com"})
    assert response.status_code == 400

@pytest.mark.django_db
def test_senha_fraca(client):
    response = client.post("/api/cadaster/", {**DADOS, "password": "123"})
    assert response.status_code == 400

@pytest.mark.django_db
def test_codigo_expirado(client, mailoutbox):
    cadastrar(client)
    EmailVerification.objects.update(created_at=timezone.now() - timedelta(minutes=11))
    response = client.post("/api/verify/", {"email": DADOS["email"], "code": codigo_do_email(mailoutbox)})
    assert response.status_code == 400

@pytest.mark.django_db
def test_limite_de_tentativas(client, mailoutbox):
    cadastrar(client)
    codigo = codigo_do_email(mailoutbox)
    errado = "000000" if codigo != "000000" else "111111"
    for _ in range(5):
        client.post("/api/verify/", {"email": DADOS["email"], "code": errado})

    response = client.post("/api/verify/", {"email": DADOS["email"], "code": codigo})
    assert response.status_code == 400
    assert User.objects.get(username="joao").is_active is False

@pytest.mark.django_db
def test_reenviar_codigo(client, mailoutbox):
    cadastrar(client)
    response = client.post("/api/verify/resend/", {"email": DADOS["email"]})
    assert response.status_code == 200
    assert len(mailoutbox) == 2

    response = client.post("/api/verify/", {"email": DADOS["email"], "code": codigo_do_email(mailoutbox)})
    assert response.status_code == 200

@pytest.mark.django_db
def test_reenviar_para_email_desconhecido_nao_revela(client, mailoutbox):
    response = client.post("/api/verify/resend/", {"email": "ninguem@example.com"})
    assert response.status_code == 200
    assert len(mailoutbox) == 0

@pytest.fixture
def logado(client, mailoutbox):
    cadastrar(client)
    client.post("/api/verify/", {"email": DADOS["email"], "code": codigo_do_email(mailoutbox)})
    token = client.post("/api/login/", {"username": "joao", "password": DADOS["password"]}).data["access"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client

@pytest.mark.django_db
def test_me(logado):
    response = logado.get("/api/me/")
    assert response.status_code == 200
    assert response.data["email"] == DADOS["email"]

@pytest.mark.django_db
def test_trocar_senha_salva_com_hash(logado):
    response = logado.patch("/api/me/", {"password": "OutraSenha!2026"})
    assert response.status_code == 200
    assert User.objects.get(username="joao").check_password("OutraSenha!2026")

@pytest.mark.django_db
def test_apagar_conta(logado):
    assert logado.delete("/api/me/").status_code == 204
    assert not User.objects.filter(username="joao").exists()

@pytest.mark.django_db
def test_me_sem_login(client):
    assert client.get("/api/me/").status_code == 401
