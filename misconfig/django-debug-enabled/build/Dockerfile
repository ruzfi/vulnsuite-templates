# A stock Django project generated at build time. The only variable is whether
# DEBUG is on (DJANGO_DEBUG, set per state). With DEBUG on, Django's 404/500
# pages leak settings, the URLconf and environment; off (the default for any
# real deployment) they are plain error pages. Django is safe by default; this
# target is purely the DEBUG misconfiguration.
FROM python:3.11-slim
RUN pip install --no-cache-dir "django==4.2.16"
WORKDIR /opt
RUN django-admin startproject demo
# DEBUG is driven by the environment; ALLOWED_HOSTS is permissive so the app
# serves in both states (DEBUG off otherwise rejects unknown hosts).
RUN printf '\nimport os\nDEBUG = os.environ.get("DJANGO_DEBUG", "0") == "1"\nALLOWED_HOSTS = ["*"]\n' >> /opt/demo/demo/settings.py
WORKDIR /opt/demo
EXPOSE 8000
CMD ["sh", "-c", "python manage.py runserver 0.0.0.0:8000"]
