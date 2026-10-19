# Só o serviço web roda as migrations, o worker do Celery espera ele
if [ "$RUN_MIGRATIONS" = "1" ]; then
    python manage.py migrate --noinput
    python manage.py collectstatic --noinput
fi

exec "$@"
