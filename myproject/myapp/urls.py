from django.urls import path
from . import views

urlpatterns = [

    path("", views.inicio, name="inicio"),

    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),

    path("index", views.index, name="index"),
    path("index_1", views.index, name="index_1"),

    path("grabaciones", views.grabaciones, name="grabaciones"),
    path("crear_grabacion", views.crear_grabacion, name="crear_grabacion"),
    path("editar_grabacion/<str:titulo>", views.editar_grabacion, name="editar_grabacion"),
    path("eliminar_grabacion/<str:titulo>", views.eliminar_grabacion, name="eliminar_grabacion"),

    path("interpretes", views.interpretes, name="interpretes"),
    path("crear_interprete", views.crear_interprete, name="crear_interprete"),
    path("editar_interprete/<int:id>", views.editar_interprete, name="editar_interprete"),
    path("eliminar_interprete/<int:id>", views.eliminar_interprete, name="eliminar_interprete"),

    path("companias", views.companias, name="companias"),
    path("crear_compania", views.crear_compania, name="crear_compania"),
    path("editar_compania/<int:id>", views.editar_compania, name="editar_compania"),
    path("eliminar_compania/<int:id>", views.eliminar_compania, name="eliminar_compania"),

    path("formatos", views.formatos, name="formatos"),
    path("crear_formato", views.crear_formato, name="crear_formato"),
    path("editar_formato/<int:id>", views.editar_formato, name="editar_formato"),
    path("eliminar_formato/<int:id>", views.eliminar_formato, name="eliminar_formato"),

    path("usuarios", views.usuarios, name="usuarios"),
    path("crear_usuario", views.crear_usuario, name="crear_usuario"),
    path("editar_usuario/<int:id>", views.editar_usuario, name="editar_usuario"),

]
