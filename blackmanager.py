# BlackManager 3.3
# Login obligatorio + cifrado real de credenciales + funciones básicas

import sqlite3
import customtkinter as ctk
from tkinter import ttk, messagebox
import bcrypt
import sys
from cryptography.fernet import Fernet, InvalidToken
import os

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# =========================================
# BASE DE DATOS
# =========================================

conexion = sqlite3.connect("passwords.db")
cursor = conexion.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS clave_maestra(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    password TEXT NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS credenciales(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    servicio TEXT NOT NULL,
    usuario TEXT NOT NULL,
    password TEXT NOT NULL
)
""")
conexion.commit()

# =========================================
# CIFRADO DE CONTRASEÑAS
# =========================================

KEY_FILE = "clave.key"

def cargar_o_crear_clave():
    if not os.path.exists(KEY_FILE):
        clave = Fernet.generate_key()
        with open(KEY_FILE, "wb") as archivo_clave:
            archivo_clave.write(clave)
    else:
        with open(KEY_FILE, "rb") as archivo_clave:
            clave = archivo_clave.read()
    return Fernet(clave)

cipher = cargar_o_crear_clave()

def cifrar_password(password: str) -> str:
    return cipher.encrypt(password.encode("utf-8")).decode("utf-8")

def es_password_cifrada(valor: str) -> bool:
    try:
        cipher.decrypt(valor.encode("utf-8"))
        return True
    except (InvalidToken, ValueError, TypeError):
        return False

def descifrar_password(password_cifrada: str) -> str:
    try:
        return cipher.decrypt(password_cifrada.encode("utf-8")).decode("utf-8")
    except (InvalidToken, ValueError, TypeError):
        # Si no está cifrada (credenciales viejas), se devuelve tal cual
        return password_cifrada

def migrar_credenciales_sin_cifrar():
    """
    Si encuentra contraseñas antiguas en texto plano, las cifra una sola vez.
    """
    cursor.execute("SELECT id, password FROM credenciales")
    filas = cursor.fetchall()
    cambios = False

    for id_credencial, password_guardada in filas:
        if password_guardada and not es_password_cifrada(password_guardada):
            nueva = cifrar_password(password_guardada)
            cursor.execute(
                "UPDATE credenciales SET password = ? WHERE id = ?",
                (nueva, id_credencial)
            )
            cambios = True

    if cambios:
        conexion.commit()

# Ejecutar migración al iniciar
migrar_credenciales_sin_cifrar()

# =========================================
# LOGIN / CONTRASEÑA MAESTRA
# =========================================

AUTENTICADO = False

def obtener_hash():
    cursor.execute("SELECT password FROM clave_maestra LIMIT 1")
    fila = cursor.fetchone()
    return fila[0] if fila else None

def login():
    global AUTENTICADO

    v = ctk.CTk()
    v.title("Acceso")
    v.geometry("350x220")
    v.resizable(False, False)

    def salir():
        v.destroy()
        sys.exit()

    v.protocol("WM_DELETE_WINDOW", salir)

    hash_guardado = obtener_hash()

    ctk.CTkLabel(
        v,
        text="Crear contraseña maestra" if hash_guardado is None else "Ingrese  la contraseña maestra",
        font=("Arial", 12, "bold")
    ).pack(pady=20)

    entrada = ctk.CTkEntry(v, show="*", width=250)
    entrada.pack(pady=10)

    def verificar():
        global AUTENTICADO
        password = entrada.get().strip()

        if not password:
            messagebox.showerror("Error", "Ingresa una contraseña")
            return

        if hash_guardado is None:
            if len(password) < 4:
                messagebox.showerror("Error", "La contraseña debe tener al menos 4 caracteres")
                return

            nuevo_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            cursor.execute(
                "INSERT INTO clave_maestra(password) VALUES(?)",
                (nuevo_hash,)
            )
            conexion.commit()
            AUTENTICADO = True
            v.destroy()
            return

        try:
            ok = bcrypt.checkpw(password.encode(), hash_guardado.encode())
        except ValueError:
            messagebox.showerror("Error", "Hash inválido. Borra la tabla clave_maestra.")
            return

        if ok:
            AUTENTICADO = True
            v.destroy()
        else:
            messagebox.showerror("Error", "Contraseña incorrecta")

    ctk.CTkButton(v, text="Entrar", command=verificar).pack(pady=20)
    v.mainloop()

login()

if not AUTENTICADO:
    sys.exit()

# =========================================
# APP PRINCIPAL
# =========================================

app = ctk.CTk()
app.title("BlackManager 3.3")
app.geometry("1100x700")

def cambiar_clave_maestra():
    win = ctk.CTkToplevel(app)
    win.title("Cambiar contraseña maestra")
    win.geometry("320x220")
    win.resizable(False, False)

    actual = ctk.CTkEntry(win, show="*", placeholder_text="Contraseña actual", width=220)
    actual.pack(pady=10)

    nueva = ctk.CTkEntry(win, show="*", placeholder_text="Nueva contraseña", width=220)
    nueva.pack(pady=10)

    def guardar():
        hash_guardado = obtener_hash()

        if not actual.get() or not nueva.get():
            messagebox.showerror("Error", "Completa todos los campos")
            return

        try:
            ok = bcrypt.checkpw(actual.get().encode(), hash_guardado.encode())
        except ValueError:
            messagebox.showerror("Error", "Hash inválido")
            return

        if not ok:
            messagebox.showerror("Error", "Contraseña actual incorrecta")
            return

        if len(nueva.get()) < 4:
            messagebox.showerror("Error", "La nueva contraseña debe tener al menos 4 caracteres")
            return

        nuevo_hash = bcrypt.hashpw(nueva.get().encode(), bcrypt.gensalt()).decode()

        cursor.execute("DELETE FROM clave_maestra")
        cursor.execute(
            "INSERT INTO clave_maestra(password) VALUES(?)",
            (nuevo_hash,)
        )
        conexion.commit()

        messagebox.showinfo("OK", "Contraseña actualizada")
        win.destroy()

    ctk.CTkButton(win, text="Guardar", command=guardar).pack(pady=15)

ctk.CTkButton(
    app,
    text="Cambiar contraseña maestra",
    command=cambiar_clave_maestra
).pack(pady=10)

left_frame = ctk.CTkFrame(app)
left_frame.pack(side="left", fill="y", padx=20, pady=20)

right_frame = ctk.CTkFrame(app)
right_frame.pack(side="right", fill="both", expand=True, padx=20, pady=20)

servicio_entry = ctk.CTkEntry(left_frame, placeholder_text="Servicio")
servicio_entry.pack(pady=5)

usuario_entry = ctk.CTkEntry(left_frame, placeholder_text="Usuario")
usuario_entry.pack(pady=5)

password_entry = ctk.CTkEntry(left_frame, placeholder_text="Password", show="*")
password_entry.pack(pady=5)
#faperez
style = ttk.Style()
style.theme_use("default")

style.configure(
    "Treeview",
    background="#0F172A",#f
    foreground="cyan",#a
    rowheight=30,#p
    fieldbackground="#000716",#e
    bordercolor="#00F5FF",#r
    borderwidth=1#e
)#z

style.configure(
    "Treeview.Heading",
    background="#00F5FF",
    foreground="black",
    font=("Arial", 10, "bold")
)

tabla = ttk.Treeview(
    right_frame,
    columns=("ID", "Servicio", "Usuario", "Password"),
    show="headings"
)

for c in ("ID", "Servicio", "Usuario", "Password"):
    tabla.heading(c, text=c)

tabla.pack(fill="both", expand=True)

# =========================================
# FUNCIONES DE CREDENCIALES
# =========================================

def limpiar_campos():
    servicio_entry.delete(0, "end")
    usuario_entry.delete(0, "end")
    password_entry.delete(0, "end")

def actualizar_tabla():
    for row in tabla.get_children():
        tabla.delete(row)

    cursor.execute("SELECT * FROM credenciales ORDER BY servicio ASC")
    filas = cursor.fetchall()

    for fila in filas:
        id_credencial = fila[0]
        servicio = fila[1]
        usuario = fila[2]
        password_guardada = fila[3]

        password_real = descifrar_password(password_guardada)

        tabla.insert("", "end", values=(
            id_credencial,
            servicio,
            usuario,
            password_real
        ))

def agregar_credencial():
    servicio = servicio_entry.get().strip()
    usuario = usuario_entry.get().strip()
    password = password_entry.get().strip()

    if not servicio or not usuario or not password:
        messagebox.showerror("Error", "Completa todos los campos")
        return

    password_cifrada = cifrar_password(password)

    cursor.execute(
        "INSERT INTO credenciales(servicio,usuario,password) VALUES(?,?,?)",
        (servicio, usuario, password_cifrada)
    )
    conexion.commit()
    limpiar_campos()
    actualizar_tabla()
    messagebox.showinfo("OK", "Credencial guardada")

def eliminar_credencial():
    sel = tabla.selection()
    if not sel:
        messagebox.showerror("Error", "Selecciona una credencial")
        return

    idx = tabla.item(sel)["values"][0]

    cursor.execute(
        "DELETE FROM credenciales WHERE id=?",
        (idx,)
    )
    conexion.commit()
    actualizar_tabla()
    messagebox.showinfo("OK", "Credencial eliminada")

def buscar_credencial():
    texto = servicio_entry.get().strip()

    for row in tabla.get_children():
        tabla.delete(row)

    cursor.execute(
        "SELECT * FROM credenciales WHERE servicio LIKE ?",
        ('%' + texto + '%',)
    )

    filas = cursor.fetchall()

    for fila in filas:
        id_credencial = fila[0]#f
        servicio = fila[1]#a
        usuario = fila[2]#p
        password_guardada = fila[3]#z

        password_real = descifrar_password(password_guardada)

        tabla.insert("", "end", values=(
            id_credencial,
            servicio,
            usuario,
            password_real
        ))

def cargar_credencial_seleccionada():
    sel = tabla.selection()
    if not sel:
        messagebox.showerror("Error", "Selecciona una credencial")
        return

    item = tabla.item(sel)
    valores = item["values"]

    if not valores:
        return

    limpiar_campos()
    servicio_entry.insert(0, valores[1])
    usuario_entry.insert(0, valores[2])
    password_entry.insert(0, valores[3])

def modificar_credencial():
    sel = tabla.selection()
    if not sel:
        messagebox.showerror("Error", "Selecciona una credencial para modificar")
        return

    item = tabla.item(sel)
    valores = item["values"]

    if not valores:
        messagebox.showerror("Error", "No se pudo leer la credencial seleccionada")
        return

    id_credencial = valores[0]
    servicio = servicio_entry.get().strip()
    usuario = usuario_entry.get().strip()
    password = password_entry.get().strip()

    if not servicio or not usuario or not password:
        messagebox.showerror("Error", "Completa todos los campos antes de modificar")
        return

    password_cifrada = cifrar_password(password)

    cursor.execute(
        """
        UPDATE credenciales
        SET servicio = ?, usuario = ?, password = ?
        WHERE id = ?
        """,
        (servicio, usuario, password_cifrada, id_credencial)
    )
    conexion.commit()
    actualizar_tabla()
    limpiar_campos()
    messagebox.showinfo("OK", "Credencial modificada")

ctk.CTkButton(left_frame, text="AGREGAR", command=agregar_credencial).pack(pady=5)
ctk.CTkButton(left_frame, text="BUSCAR", command=buscar_credencial).pack(pady=5)
ctk.CTkButton(left_frame, text="MOSTRAR TODO", command=actualizar_tabla).pack(pady=5)
ctk.CTkButton(left_frame, text="ELIMINAR", command=eliminar_credencial).pack(pady=5)
ctk.CTkButton(left_frame, text="CARGAR SELECCION", command=cargar_credencial_seleccionada).pack(pady=5)
ctk.CTkButton(left_frame, text="MODIFICAR", command=modificar_credencial).pack(pady=5)

actualizar_tabla()

app.mainloop()
conexion.close()
