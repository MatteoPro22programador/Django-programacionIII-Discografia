import os
from functools import wraps
from django.db import connection, IntegrityError
from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden
from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password


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



def solo_admin(vista):
    @wraps(vista)
    def wrapper(request, *args, **kwargs):
        if request.session.get("nivel") != "ADMIN":
            return HttpResponseForbidden("No autorizado")
        return vista(request, *args, **kwargs)
    return wrapper 

def login_view(request):
    if request.session.get("usuario_id"):
        return redirect("index")

    error = None

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id_usuario, username, password, nombre, nivel FROM usuarios WHERE username = %s",
                [username]
            )
            fila = cursor.fetchone()

        if fila and check_password(password, fila[2]):
            request.session["usuario_id"] = fila[0]
            request.session["usuario_nombre"] = fila[3]
            request.session["nivel"] = fila[4]
            return redirect("index")
        else:
            error = "Usuario o contraseña incorrectos"

    return render(request, "myapp/login.html", {"error": error})


def logout_view(request):
    request.session.flush()
    return redirect("inicio")


def inicio(request):
    return render(request, "myapp/inicio.html")


@login_requerido
def index(request):
    return render(request, "myapp/index_1.html")



# GRABACIONES


@login_requerido
def grabaciones(request):
    q = request.GET.get("q", "").strip()

    sql = """
        SELECT g.titulo, g.categoria, g.num_temas, g.anio, g.descripcion, g.archivo,
               c.nombre AS compania_nombre,
               i.nombre AS interprete_nombre
        FROM grabaciones g
        LEFT JOIN compania c ON g.id_compania = c.id_compania
        LEFT JOIN interprete i ON g.id_interprete = i.id_interprete
    """
    params = []
    if q:
        sql += """
            WHERE g.titulo LIKE %s OR g.categoria LIKE %s OR g.descripcion LIKE %s
               OR c.nombre LIKE %s OR i.nombre LIKE %s
        """
        like = f"%{q}%"
        params = [like, like, like, like, like]
    sql += " ORDER BY g.titulo"

    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        lista = dictfetchall(cursor)

    return render(request, "myapp/grabaciones.html", {"grabaciones": lista, "q": q})


@login_requerido
@solo_admin
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


@login_requerido
@solo_admin
def editar_grabacion(request, titulo):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT titulo, categoria, num_temas, anio, descripcion, id_compania, id_interprete, archivo
            FROM grabaciones WHERE titulo = %s
        """, [titulo])
        fila = cursor.fetchone()
        if not fila:
            return redirect("grabaciones")
        grabacion = {
            "titulo": fila[0], "categoria": fila[1], "num_temas": fila[2],
            "anio": fila[3], "descripcion": fila[4], "id_compania": fila[5],
            "id_interprete": fila[6], "archivo": fila[7],
        }

        cursor.execute("SELECT id_compania, nombre FROM compania")
        companias = dictfetchall(cursor)

        cursor.execute("SELECT id_interprete, nombre FROM interprete")
        interpretes = dictfetchall(cursor)

    if request.method == "POST":
        nuevo_titulo = request.POST.get("titulo")
        categoria = request.POST.get("categoria")
        num_temas = request.POST.get("num_temas") or None
        anio = request.POST.get("anio") or None
        descripcion = request.POST.get("descripcion")
        id_compania = request.POST.get("id_compania") or None
        id_interprete = request.POST.get("id_interprete") or None

        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE grabaciones
                SET titulo = %s, categoria = %s, num_temas = %s, anio = %s,
                    descripcion = %s, id_compania = %s, id_interprete = %s
                WHERE titulo = %s
            """, [nuevo_titulo, categoria, num_temas, anio, descripcion,
                  id_compania, id_interprete, titulo])

            if nuevo_titulo != titulo:
                cursor.execute(
                    "UPDATE formato SET titulo = %s WHERE titulo = %s",
                    [nuevo_titulo, titulo]
                )

        return redirect("grabaciones")

    return render(request, "myapp/editar_grabacion.html", {
        "grabacion": grabacion,
        "companias": companias,
        "interpretes": interpretes,
    })


@login_requerido
@solo_admin
def eliminar_grabacion(request, titulo):
    if request.method == "POST":
        with connection.cursor() as cursor:
            cursor.execute("UPDATE formato SET titulo = NULL WHERE titulo = %s", [titulo])
            cursor.execute("DELETE FROM grabaciones WHERE titulo = %s", [titulo])
    return redirect("grabaciones")



# INTERPRETES


@login_requerido
def interpretes(request):
    q = request.GET.get("q", "").strip()

    sql = "SELECT id_interprete, nombre, descripcion FROM interprete"
    params = []
    if q:
        sql += " WHERE nombre LIKE %s OR descripcion LIKE %s"
        params = [f"%{q}%", f"%{q}%"]
    sql += " ORDER BY nombre"

    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        lista = dictfetchall(cursor)

    return render(request, "myapp/interpretes.html", {"interpretes": lista, "q": q})


@login_requerido
@solo_admin
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


@login_requerido
@solo_admin
def editar_interprete(request, id):
    with connection.cursor() as cursor:
        cursor.execute("SELECT id_interprete, nombre, descripcion FROM interprete WHERE id_interprete = %s", [id])
        fila = cursor.fetchone()
        if not fila:
            return redirect("interpretes")
        interprete = {"id_interprete": fila[0], "nombre": fila[1], "descripcion": fila[2]}

    if request.method == "POST":
        nombre = request.POST.get("nombre")
        descripcion = request.POST.get("descripcion")

        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE interprete SET nombre = %s, descripcion = %s WHERE id_interprete = %s",
                [nombre, descripcion, id]
            )

        return redirect("interpretes")

    return render(request, "myapp/editar_interprete.html", {"interprete": interprete})


@login_requerido
@solo_admin
def eliminar_interprete(request, id):
    if request.method == "POST":
        with connection.cursor() as cursor:
            cursor.execute("UPDATE grabaciones SET id_interprete = NULL WHERE id_interprete = %s", [id])
            cursor.execute("DELETE FROM interprete WHERE id_interprete = %s", [id])
    return redirect("interpretes")



# COMPAÑÍAS


@login_requerido
def companias(request):
    q = request.GET.get("q", "").strip()

    sql = """
        SELECT c.id_compania, c.nombre, c.direccion,
               COUNT(g.titulo) AS total_grabaciones
        FROM compania c
        LEFT JOIN grabaciones g ON g.id_compania = c.id_compania
    """
    params = []
    if q:
        sql += " WHERE c.nombre LIKE %s OR c.direccion LIKE %s"
        params = [f"%{q}%", f"%{q}%"]
    sql += " GROUP BY c.id_compania, c.nombre, c.direccion ORDER BY c.nombre"

    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        lista = dictfetchall(cursor)

    return render(request, "myapp/companias.html", {"companias": lista, "q": q})


@login_requerido
@solo_admin
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


@login_requerido
@solo_admin
def editar_compania(request, id):
    with connection.cursor() as cursor:
        cursor.execute("SELECT id_compania, nombre, direccion FROM compania WHERE id_compania = %s", [id])
        fila = cursor.fetchone()
        if not fila:
            return redirect("companias")
        compania = {"id_compania": fila[0], "nombre": fila[1], "direccion": fila[2]}

    if request.method == "POST":
        nombre = request.POST.get("nombre")
        direccion = request.POST.get("direccion")

        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE compania SET nombre = %s, direccion = %s WHERE id_compania = %s",
                [nombre, direccion, id]
            )

        return redirect("companias")

    return render(request, "myapp/editar_compania.html", {"compania": compania})


@login_requerido
@solo_admin
def eliminar_compania(request, id):
    if request.method == "POST":
        with connection.cursor() as cursor:
            cursor.execute("UPDATE grabaciones SET id_compania = NULL WHERE id_compania = %s", [id])
            cursor.execute("DELETE FROM compania WHERE id_compania = %s", [id])
    return redirect("companias")



# FORMATOS

@login_requerido
def formatos(request):
    q = request.GET.get("q", "").strip()

    sql = """
        SELECT f.id_formato, f.tipo, f.conservacion,
               g.titulo AS grabacion_titulo
        FROM formato f
        LEFT JOIN grabaciones g ON f.titulo = g.titulo
    """
    params = []
    if q:
        sql += " WHERE f.tipo LIKE %s OR f.conservacion LIKE %s OR g.titulo LIKE %s"
        params = [f"%{q}%", f"%{q}%", f"%{q}%"]
    sql += " ORDER BY f.id_formato"

    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        lista = dictfetchall(cursor)

    return render(request, "myapp/formatos.html", {"formatos": lista, "q": q})


@login_requerido
@solo_admin
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


@login_requerido
@solo_admin
def editar_formato(request, id):
    with connection.cursor() as cursor:
        cursor.execute("SELECT id_formato, tipo, conservacion, titulo FROM formato WHERE id_formato = %s", [id])
        fila = cursor.fetchone()
        if not fila:
            return redirect("formatos")
        formato = {"id_formato": fila[0], "tipo": fila[1], "conservacion": fila[2], "titulo": fila[3]}

        cursor.execute("SELECT titulo FROM grabaciones")
        grabaciones_disponibles = dictfetchall(cursor)

    if request.method == "POST":
        tipo = request.POST.get("tipo")
        conservacion = request.POST.get("conservacion")
        titulo = request.POST.get("titulo") or None

        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE formato SET tipo = %s, conservacion = %s, titulo = %s WHERE id_formato = %s",
                [tipo, conservacion, titulo, id]
            )

        return redirect("formatos")

    return render(request, "myapp/editar_formato.html", {
        "formato": formato,
        "grabaciones": grabaciones_disponibles,
    })


@login_requerido
@solo_admin
def eliminar_formato(request, id):
    if request.method == "POST":
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM formato WHERE id_formato = %s", [id])
    return redirect("formatos")



# USUARIOS


@login_requerido
@solo_admin
def usuarios(request):
    q = request.GET.get("q", "").strip()

    sql = "SELECT id_usuario, username, nombre, nivel FROM usuarios"
    params = []
    if q:
        sql += " WHERE username LIKE %s OR nombre LIKE %s OR nivel LIKE %s"
        params = [f"%{q}%", f"%{q}%", f"%{q}%"]
    sql += " ORDER BY id_usuario"

    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        lista = dictfetchall(cursor)

    return render(request, "myapp/usuarios.html", {"usuarios": lista, "q": q})


@login_requerido
@solo_admin
def crear_usuario(request):
    error = None

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        nombre = request.POST.get("nombre", "").strip()
        password = request.POST.get("password", "")
        nivel = request.POST.get("nivel", "VISOR")

        if not username or not nombre or not password:
            error = "Username, nombre y contraseña son obligatorios"
        elif nivel not in ("ADMIN", "VISOR"):
            error = "Nivel inválido"
        else:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO usuarios (username, password, nombre, nivel) VALUES (%s, %s, %s, %s)",
                        [username, make_password(password), nombre, nivel]
                    )
                return redirect("usuarios")
            except IntegrityError:
                error = "Ya existe un usuario con ese username"

    return render(request, "myapp/crear_usuario.html", {"error": error})


@login_requerido
@solo_admin
def editar_usuario(request, id):
    with connection.cursor() as cursor:
        cursor.execute("SELECT id_usuario, username, nombre, nivel FROM usuarios WHERE id_usuario = %s", [id])
        fila = cursor.fetchone()
        if not fila:
            return redirect("usuarios")
        usuario = {"id_usuario": fila[0], "username": fila[1], "nombre": fila[2], "nivel": fila[3]}

    error = None

    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        nivel = request.POST.get("nivel", "VISOR")
        password = request.POST.get("password", "")

        if not nombre:
            error = "El nombre es obligatorio"
        elif nivel not in ("ADMIN", "VISOR"):
            error = "Nivel inválido"
        else:
            with connection.cursor() as cursor:
                if password:
                    cursor.execute(
                        "UPDATE usuarios SET nombre = %s, nivel = %s, password = %s WHERE id_usuario = %s",
                        [nombre, nivel, make_password(password), id]
                    )
                else:
                    cursor.execute(
                        "UPDATE usuarios SET nombre = %s, nivel = %s WHERE id_usuario = %s",
                        [nombre, nivel, id]
                    )
            return redirect("usuarios")

    return render(request, "myapp/editar_usuario.html", {"usuario": usuario, "error": error})
