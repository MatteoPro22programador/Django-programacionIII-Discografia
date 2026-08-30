from django.urls import path
from .import views

urlpatterns=[

    path("index",views.index,name="index"),

    path("index_1",views.index_1,name="index_1"),

    path("grabaciones",views.grabaciones,name="grabaciones"),

    path("interpretes",views.interpretes,name="interpretes"),

    path("companias",views.companias,name="companias"),

    path("formatos",views.formatos,name="formatos")
    
]