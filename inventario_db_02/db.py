import mysql.connector

# Función para conectar Python con MySQL (XAMPP)
def conectar():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",  # Si tu MySQL tiene contraseña, escríbela aquí
        database="inventario_db_02"
    )