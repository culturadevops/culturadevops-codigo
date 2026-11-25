# -*- coding: utf-8 -*-
"""Django en un solo archivo, servido con gunicorn (WSGI, workers síncronos): lo habitual en producción.
El MIDDLEWARE y las INSTALLED_APPS son las de `django-admin startproject` (Django como sale de fábrica). La base de datos no se toca:
sesiones y usuario son perezosos y estas rutas no los leen."""
import logica  # noqa: I001  (primero: arranca el reloj de «listo»)

from django.conf import settings

settings.configure(
    DEBUG=False,
    SECRET_KEY="banco-cultura-devops-no-es-secreto",
    ALLOWED_HOSTS=["*"],
    ROOT_URLCONF=__name__,
    INSTALLED_APPS=[
        "django.contrib.admin",
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.messages",
        "django.contrib.staticfiles",
    ],
    MIDDLEWARE=[
        "django.middleware.security.SecurityMiddleware",
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.middleware.common.CommonMiddleware",
        "django.middleware.csrf.CsrfViewMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "django.contrib.messages.middleware.MessageMiddleware",
        "django.middleware.clickjacking.XFrameOptionsMiddleware",
    ],
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": "/tmp/db.sqlite3"}},
    TEMPLATES=[{"BACKEND": "django.template.backends.django.DjangoTemplates", "APP_DIRS": True,
                "OPTIONS": {"context_processors": ["django.template.context_processors.request",
                                                   "django.contrib.auth.context_processors.auth",
                                                   "django.contrib.messages.context_processors.messages"]}}],
    STATIC_URL="static/",
    USE_TZ=True,
)

from django.core.wsgi import get_wsgi_application  # noqa: E402
from django.http import HttpResponse  # noqa: E402
from django.urls import path  # noqa: E402

JSON = "application/json"


def suma(request):
    return HttpResponse(logica.suma(int(request.GET.get("n", 0))), content_type=JSON)


def trabajo(request):
    return HttpResponse(logica.trabajo(int(request.GET.get("n", 0))), content_type=JSON)


urlpatterns = [path("suma", suma), path("trabajo", trabajo)]

application = get_wsgi_application()
logica.listo("django")
