release: python download_models.py && python manage.py collectstatic --noinput
web: gunicorn config.wsgi:application --log-file -
