# Projeto de Automação

![CI](https://github.com/gabrueldev/AutomacaoAPI/actions/workflows/main.yml/badge.svg)
## Projeto destinado à automações de email's para novos usuários com Celery + Redis.
Diariamente pequenos sites se perguntam:

**Clientes entram mas após um tempo... Não voltam. Como poderiamos resolver isso?**

E a resposta é mais simples do que parece. Embora podemos achar que receber email's chatos mais podem nos irritar do que nos fazer pensar "Vou voltar para este site.", devíamos olhar por outro lado, email's não servem para anúncios, quando percebemos que é um "anúncio" automáticamente não olhamos e possívelmente iríamos parar como spam. De fato, email's como **anúncio** são um saco, porém, não consigo ignorar um email do **meu banco**. Bancos tem email's como aviso, até mesmo para anúnciar algo utilizam do aviso, e nunca ignoramos um email de nosso banco, até porquê nossa renda está lá. Email's bem utilizados podem ser uma **arma crucial** na jogada de marketing de um site, se utilizados da maneira certa.

## Sistema de email's automático

Propus um sistema em que logo que o usuário se cadastra recebe um código de confirmação de email, e após o cadastro recebe um email de boas vindas. A parte boa? Você pode colocar seus emails estratégicos para serem enviados diretamente para seu cliente logo após uma ação! Utilizando Redis + Celery o sistema de filas pode enviar **automáticamente** um email para seu cliente sem que você precise se preocupar com isso! Automatizando uma tarefa super chata mas que, usada estratégicamente pode ser *um benefício incrível* para seu site **trazendo resultados significantes**!

## Como funciona

```
1. POST /api/cadaster/      → conta criada como inativa, Celery envia o código por email
2. POST /api/verify/        → código certo: conta ativada, Celery envia o email de boas-vindas
                              e a API já devolve o JWT (access + refresh)
3. POST /api/login/         → login normal com JWT
```

Os emails saem por uma **fila no Redis**, processada pelo worker do Celery. A resposta da API não espera o email ser enviado, então o cadastro continua rápido mesmo se o SMTP estiver lento.

| Método | Rota | O que faz |
|---|---|---|
| POST | `/api/cadaster/` | Cria a conta e envia o código |
| POST | `/api/verify/` | Confirma o código e devolve o JWT |
| POST | `/api/verify/resend/` | Envia um código novo |
| POST | `/api/login/` | Devolve access e refresh token |
| GET / PATCH / DELETE | `/api/me/` | Vê, edita ou apaga a própria conta |

Nas rotas protegidas, mande o token no header: `Authorization: Bearer <access>`.

### Segurança

+ Código de 6 dígitos gerado com `secrets`, salvo como hash e com validade de **10 minutos**
+ Bloqueio depois de **5 tentativas erradas**, contra força bruta
+ Conta inativa até confirmar o email, então não dá para logar antes
+ Email duplicado recusado e validação de senha forte do Django
+ O reenvio de código não revela se um email está cadastrado
+ `/api/me/` sempre age sobre o usuário do token, então ninguém edita a conta de outro

## Tecnologias Utilizadas

+ Python 3.12
+ Django REST Framework
+ Autenticação com JSON Web Token (SimpleJWT)
+ Celery + Redis
+ PostgreSQL
+ Docker Compose
+ Pytest | 18 testes automatizados
+ CI com GitHub Actions

## Rodando com Docker

    cp .env.example .env
    docker compose up --build

Isso sobe a API, o Postgres, o Redis e o worker do Celery. A API fica em **http://localhost:8000/api/**.

> Para enviar pelo Gmail, use uma **senha de app** (myaccount.google.com/apppasswords). Se deixar `EMAIL_HOST_USER` vazio, os emails aparecem no log do worker em vez de serem enviados, o que é útil para testar.

## Testes

    pip install -r app/requirements.txt
    pytest

Nos testes o Celery roda síncrono e os emails ficam em memória. Assim dá para conferir o conteúdo de cada email sem Redis nem SMTP.
