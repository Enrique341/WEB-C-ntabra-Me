from flask import Flask, render_template, request, redirect, url_for, Response
from db import conectar
import csv
import io

app = Flask(__name__)


@app.route("/")
def dashboard():
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS total FROM productos")
    total_productos = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM productos WHERE stock <= stock_minimo")
    bajo_stock = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM productos WHERE fecha_vencimiento < CURDATE()")
    vencidos = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT COUNT(*) AS total FROM productos
        WHERE fecha_vencimiento BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)
    """)
    por_vencer = cursor.fetchone()["total"]

    cursor.execute("SELECT SUM(stock * precio_compra) AS total FROM productos")
    valor_compra = cursor.fetchone()["total"] or 0

    cursor.execute("SELECT SUM(stock * precio_venta) AS total FROM productos")
    valor_venta = cursor.fetchone()["total"] or 0

    ganancia_estimada = valor_venta - valor_compra

    cursor.close()
    conexion.close()

    return render_template(
        "dashboard_v2.html",
        total_productos=total_productos,
        bajo_stock=bajo_stock,
        vencidos=vencidos,
        por_vencer=por_vencer,
        valor_compra=valor_compra,
        valor_venta=valor_venta,
        ganancia_estimada=ganancia_estimada
    )


@app.route("/productos")
def productos():
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("SELECT * FROM productos ORDER BY id DESC")
    productos = cursor.fetchall()
    cursor.close()
    conexion.close()
    return render_template("productos_v2.html", productos=productos)


@app.route("/productos/nuevo")
def nuevo_producto():
    return render_template("nuevo_producto_v2.html")


@app.route("/productos/guardar", methods=["POST"])
def guardar_producto():
    codigo         = request.form["codigo"]
    nombre         = request.form["nombre"]
    categoria      = request.form["categoria"]
    stock          = request.form["stock"]
    stock_minimo   = request.form["stock_minimo"]
    precio_compra  = request.form["precio_compra"]
    precio_venta   = request.form["precio_venta"]
    fecha_ingreso  = request.form["fecha_ingreso"]
    fecha_vencimiento = request.form["fecha_vencimiento"]

    conexion = conectar()
    cursor = conexion.cursor()
    sql = """
        INSERT INTO productos
        (codigo, nombre, categoria, stock, stock_minimo, precio_compra, precio_venta, fecha_ingreso, fecha_vencimiento)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(sql, (codigo, nombre, categoria, stock, stock_minimo,
                         precio_compra, precio_venta, fecha_ingreso, fecha_vencimiento))
    conexion.commit()
    cursor.close()
    conexion.close()
    return redirect(url_for("productos"))


@app.route("/productos/editar/<int:id>")
def editar_producto(id):
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("SELECT * FROM productos WHERE id = %s", (id,))
    producto = cursor.fetchone()
    cursor.close()
    conexion.close()
    return render_template("editar_producto_v2.html", producto=producto)


@app.route("/productos/actualizar/<int:id>", methods=["POST"])
def actualizar_producto(id):
    codigo         = request.form["codigo"]
    nombre         = request.form["nombre"]
    categoria      = request.form["categoria"]
    stock          = request.form["stock"]
    stock_minimo   = request.form["stock_minimo"]
    precio_compra  = request.form["precio_compra"]
    precio_venta   = request.form["precio_venta"]
    fecha_ingreso  = request.form["fecha_ingreso"]
    fecha_vencimiento = request.form["fecha_vencimiento"]

    conexion = conectar()
    cursor = conexion.cursor()
    sql = """
        UPDATE productos
        SET codigo=%s, nombre=%s, categoria=%s, stock=%s, stock_minimo=%s,
            precio_compra=%s, precio_venta=%s, fecha_ingreso=%s, fecha_vencimiento=%s
        WHERE id=%s
    """
    cursor.execute(sql, (codigo, nombre, categoria, stock, stock_minimo,
                         precio_compra, precio_venta, fecha_ingreso, fecha_vencimiento, id))
    conexion.commit()
    cursor.close()
    conexion.close()
    return redirect(url_for("productos"))


@app.route("/productos/eliminar/<int:id>")
def eliminar_producto(id):
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM productos WHERE id = %s", (id,))
    conexion.commit()
    cursor.close()
    conexion.close()
    return redirect(url_for("productos"))


@app.route("/productos/filtrar", methods=["GET"])
def filtrar_productos():
    fecha_inicio = request.args.get("fecha_inicio")
    fecha_fin    = request.args.get("fecha_fin")

    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    sql = """
        SELECT * FROM productos
        WHERE fecha_ingreso BETWEEN %s AND %s
        ORDER BY fecha_ingreso DESC
    """
    cursor.execute(sql, (fecha_inicio, fecha_fin))
    productos = cursor.fetchall()
    cursor.close()
    conexion.close()
    return render_template("productos_v2.html", productos=productos)


@app.route("/productos/vencer")
def productos_vencer():
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM productos
        WHERE fecha_vencimiento BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)
        ORDER BY fecha_vencimiento ASC
    """)
    productos = cursor.fetchall()
    cursor.close()
    conexion.close()
    return render_template("productos_vencer_v2.html", productos=productos)


@app.route("/productos/exportar")
def exportar_csv():
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("SELECT * FROM productos ORDER BY id DESC")
    productos = cursor.fetchall()
    cursor.close()
    conexion.close()

    salida = io.StringIO()
    escritor = csv.writer(salida)
    escritor.writerow(["ID", "Codigo", "Nombre", "Categoria", "Stock", "Stock minimo",
                       "Precio compra", "Precio venta", "Fecha ingreso", "Fecha vencimiento"])
    for p in productos:
        escritor.writerow([p["id"], p["codigo"], p["nombre"], p["categoria"], p["stock"],
                           p["stock_minimo"], p["precio_compra"], p["precio_venta"],
                           p["fecha_ingreso"], p["fecha_vencimiento"]])

    respuesta = Response(salida.getvalue(), mimetype="text/csv")
    respuesta.headers["Content-Disposition"] = "attachment; filename=reporte_productos_perecibles.csv"
    return respuesta


if __name__ == "__main__":
    app.run(debug=True)