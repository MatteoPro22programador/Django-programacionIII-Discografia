import os
from functools import wraps
from django.db import connection
from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.auth.hashers import check_password


def dictfetchall(cursor):
    """Convierte el resultado del cursor en una lista de diccionarios,
    para poder usar los nombres de columna en el template (fila.columna)."""
    columnas = [col[0] for col in cursor.description]
    return [dict(zip(columnas, fila)) for fila in cursor.fetchall()]


def login_requerido(vista):
    @wraps(vista)
    def wrapper(request, *args, **kwargs):
        if not request.session.get("usuario_id"):
            return redirect("login")
        return vista(request, *args, **kwargs)
    return wrapper


def login_view(request):
    error = None

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id_usuario, username, password, nombre FROM usuarios WHERE username = %s",
                [username]
            )
            fila = cursor.fetchone()

        if fila and check_password(password, fila[2]):
            request.session["usuario_id"] = fila[0]
            request.session["usuario_nombre"] = fila[3]
            return redirect("index")
        else:
            error = "Usuario o contraseña incorrectos"

    return render(request, "myapp/login.html", {"error": error})


def logout_view(request):
    request.session.flush()
    return redirect("login")


@login_requerido
def index(request):
    return render(request, "myapp/index_1.html")



# GRABACIONES


@login_requerido
def grabaciones(request):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT g.titulo, g.categoria, g.num_temas, g.anio, g.descripcion, g.archivo,
                   c.nombre AS compania_nombre,
                   i.nombre AS interprete_nombre
            FROM grabaciones g
            LEFT JOIN compania c ON g.id_compania = c.id_compania
            LEFT JOIN interprete i ON g.id_interprete = i.id_interprete
        """)
        lista = dictfetchall(cursor)

    return render(request, "myapp/grabaciones.html", {"grabaciones": lista})


@login_requerido
def crear_grabacion(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT id_compania, nombre FROM compania")
        companias = dictfetchall(cursor)

        cursor.execute("SELECT id_interprete, nombre FROM interprete")
        interpretes = dictfetchall(cursor)

    if request.method == "POST":
        titulo = request.POST.get("titulo")
        categoria = request.POST.get("categoria")
        num_temas = request.POST.get("num_temas") or None
        anio = request.POST.get("anio") or None
        descripcion = request.POST.get("descripcion")
        id_compania = request.POST.get("id_compania") or None
        id_interprete = request.POST.get("id_interprete") or None

        nombre_archivo = None
        archivo = request.FILES.get("archivo")
        if archivo:
            os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
            nombre_archivo = archivo.name
            ruta = os.path.join(settings.MEDIA_ROOT, nombre_archivo)
            with open(ruta, "wb+") as destino:
                for chunk in archivo.chunks():
                    destino.write(chunk)

        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO grabaciones
                    (titulo, categoria, num_temas, anio, descripcion, id_compania, id_interprete, archivo)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, [titulo, categoria, num_temas, anio, descripcion, id_compania, id_interprete, nombre_archivo])

        return redirect("grabaciones")

    return render(request, "myapp/crear_grabacion.html", {
        "companias": companias,
        "interpretes": interpretes,
    })



# INTERPRETES


@login_requerido
def interpretes(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT id_interprete, nombre, descripcion FROM interprete")
        lista = dictfetchall(cursor)

    return render(request, "myapp/interpretes.html", {"interpretes": lista})


@login_requerido
def crear_interprete(request):
    if request.method == "POST":
        nombre = request.POST.get("nombre")
        descripcion = request.POST.get("descripcion")

        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO interprete (nombre, descripcion)
                VALUES (%s, %s)
            """, [nombre, descripcion])

        return redirect("interpretes")

    return render(request, "myapp/crear_interprete.html")



# COMPAÑÍAS


@login_requerido
def companias(request):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT c.id_compania, c.nombre, c.direccion,
                   COUNT(g.titulo) AS total_grabaciones
            FROM compania c
            LEFT JOIN grabaciones g ON g.id_compania = c.id_compania
            GROUP BY c.id_compania, c.nombre, c.direccion
        """)
        lista = dictfetchall(cursor)

    return render(request, "myapp/companias.html", {"companias": lista})


@login_requerido
def crear_compania(request):
    if request.method == "POST":
        nombre = request.POST.get("nombre")
        direccion = request.POST.get("direccion")

        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO compania (nombre, direccion)
                VALUES (%s, %s)
            """, [nombre, direccion])

        return redirect("companias")

    return render(request, "myapp/crear_compania.html")



# FORMATOS

@login_requerido
def formatos(request):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT f.id_formato, f.tipo, f.conservacion,
                   g.titulo AS grabacion_titulo
            FROM formato f
            LEFT JOIN grabaciones g ON f.titulo = g.titulo
        """)
        lista = dictfetchall(cursor)

    return render(request, "myapp/formatos.html", {"formatos": lista})


@login_requerido
def crear_formato(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT titulo FROM grabaciones")
        grabaciones_disponibles = dictfetchall(cursor)

    if request.method == "POST":
        tipo = request.POST.get("tipo")
        conservacion = request.POST.get("conservacion")
        titulo = request.POST.get("titulo") or None

        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO formato (tipo, conservacion, titulo)
                VALUES (%s, %s, %s)
            """, [tipo, conservacion, titulo])

        return redirect("formatos")

    return render(request, "myapp/crear_formato.html", {
        "grabaciones": grabaciones_disponibles,
    })