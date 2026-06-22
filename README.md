[README.md](https://github.com/user-attachments/files/29185944/README.md)
# BlackManager

Gestor de credenciales hecho en **Python** con interfaz gráfica usando **CustomTkinter**.

## Funciones actuales

- Contraseña maestra obligatoria al iniciar
- Cambio de contraseña maestra desde la interfaz
- Guardado de credenciales en **SQLite**
- Cifrado de contraseñas con **Fernet**
- Hash de la contraseña maestra con **bcrypt**
- Agregar credenciales
- Buscar credenciales
- Mostrar todas las credenciales
- Eliminar credenciales
- Modificar credenciales existentes

---

## Tecnologías usadas

- Python 3
- customtkinter
- sqlite3
- bcrypt
- cryptography

---

## Instalación

Instala las dependencias con:

```bash
pip install -r requirements.txt
```

---

## Ejecución

Desde la carpeta del proyecto:

```bash
python main.py
```

---

## Compilar a .exe

Si quieres generar un ejecutable con PyInstaller:

```bash
python -m PyInstaller --onefile --windowed main.py
```

El `.exe` se generará dentro de la carpeta:

```text
dist/
```

---

## Archivos que genera el programa

El programa crea automáticamente estos archivos al ejecutarse:

- `passwords.db` → base de datos SQLite donde se guardan las credenciales
- `clave.key` → clave usada para cifrar y descifrar contraseñas con Fernet

### Importante
**No compartas ni subas `clave.key` ni `passwords.db` a un repositorio público**, porque contienen información sensible o permiten descifrarla.

---

## Estructura recomendada del proyecto

```text
gestor_de_credenciales/
│
├─ main.py
├─ requirements.txt
├─ README.md
├─ .gitignore
```

---

## Notas de seguridad

- La contraseña maestra **no se guarda en texto plano**: se almacena como hash usando `bcrypt`.
- Las contraseñas de las credenciales **no se guardan en texto plano**: se cifran usando `cryptography.fernet`.
- Si se pierde el archivo `clave.key`, las credenciales cifradas ya no podrán descifrarse.

---

## Estado del proyecto

Proyecto personal en desarrollo.
