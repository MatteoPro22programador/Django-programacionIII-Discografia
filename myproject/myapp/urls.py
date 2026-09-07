from django.urls import path
from . import views

urlpatterns = [

    path("index", views.index, name="index"),
    path("index_1", views.index, name="index_1"),

    path("grabaciones", views.grabaciones, name="grabaciones"),
    path("crear_grabacion", views.crear_grabacion, name="crear_grabacion"),

    path("interpretes", views.interpretes, name="interpretes"),
    path("crear_interprete", views.crear_interprete, name="crear_interprete"),

    path("companias", views.companias, name="companias"),
    path("crear_compania", views.crear_compania, name="crear_compania"),

    path("formatos", views.formatos, name="formatos"),
    path("crear_formato", views.crear_formato, name="crear_formato"),

]