# ⚠️ VULNERABLE A PROPÓSITO (demo de escáneres). No desplegar.


def buscar_productos(conexion, texto):
    # V3: el SQL se arma aquí, lejos de donde entra el dato
    sql = "SELECT nombre FROM productos WHERE nombre LIKE '%" + texto + "%'"
    return conexion.execute(sql).fetchall()
