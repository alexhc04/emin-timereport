# 📘 GUÍA COMPLETA DE INSTALACIÓN Y DESPLIEGUE
# EMIN TIME REPORT — Despacho de Abogados
# ==========================================
# Escrita para alguien sin experiencia previa en programación

---

## 🗂️ ESTRUCTURA DE ARCHIVOS

```
emin-timereport/
├── app.py              ← El cerebro de la aplicación (backend Python)
├── requirements.txt    ← Lista de librerías necesarias
├── Procfile            ← Instrucciones de arranque para el servidor
├── render.yaml         ← Configuración de despliegue en Render
├── .env.example        ← Plantilla de variables de entorno
├── .gitignore          ← Archivos que NO se suben a GitHub
└── templates/
    ├── login.html      ← Página de inicio de sesión
    └── dashboard.html  ← Panel principal de la aplicación
```

---

## 👤 CREDENCIALES DE ACCESO INICIALES

| Usuario      | Contraseña  | Rol           |
|-------------|-------------|---------------|
| admin       | Emin2024!   | CEO / Admin   |
| trabajador1 | Emin2024!   | Trabajador    |
| trabajador2 | Emin2024!   | Trabajador    |

⚠️ IMPORTANTE: Cambia estas contraseñas después del primer acceso.

---

## 🚀 OPCIÓN 1: PRUEBA LOCAL (en tu ordenador)

### Paso 1 — Instalar Python
1. Ve a https://www.python.org/downloads/
2. Descarga Python 3.11 o superior
3. En la instalación, marca ✅ "Add Python to PATH"
4. Haz clic en "Install Now"
5. Verifica: abre el símbolo del sistema (cmd) y escribe:
   ```
   python --version
   ```
   Deberías ver algo como "Python 3.11.x"

### Paso 2 — Descargar los archivos del proyecto
1. Crea una carpeta en tu escritorio llamada "emin-timereport"
2. Copia TODOS los archivos del proyecto dentro de esa carpeta
   (respetando la subcarpeta "templates/")

### Paso 3 — Instalar dependencias
1. Abre el símbolo del sistema (cmd) o Terminal
2. Navega a la carpeta del proyecto:
   ```
   cd Desktop\emin-timereport
   ```
   (En Mac/Linux: cd ~/Desktop/emin-timereport)
3. Instala las librerías:
   ```
   pip install -r requirements.txt
   ```
   Espera a que termine (puede tardar 1-2 minutos)

### Paso 4 — Ejecutar la aplicación
```
python app.py
```
Verás en pantalla:
```
✅ Usuarios iniciales creados correctamente
 * Running on http://0.0.0.0:5000
```

### Paso 5 — Abrir en el navegador
Abre tu navegador y ve a: http://localhost:5000

¡Ya puedes usar la aplicación localmente!

---

## ☁️ OPCIÓN 2: DEPLOY EN LA NUBE (acceso desde cualquier lugar)

Para que la aplicación sea accesible desde internet necesitas:
1. Una cuenta en GitHub (para guardar el código)
2. Una cuenta en Render (para el servidor gratuito)
3. Una cuenta en Supabase (para la base de datos gratuita)

### PASO A — Crear cuenta en GitHub
1. Ve a https://github.com
2. Haz clic en "Sign up"
3. Crea tu cuenta gratuita
4. Verifica tu email

### PASO B — Subir el código a GitHub
1. Una vez en GitHub, haz clic en el botón verde "New" (nuevo repositorio)
2. Nombre del repositorio: "emin-timereport"
3. Deja todo por defecto y haz clic en "Create repository"
4. GitHub te mostrará instrucciones. Elige la opción de subir archivos:
   - Haz clic en "uploading an existing file"
   - Arrastra TODOS los archivos del proyecto
   - Haz clic en "Commit changes"

   (Alternativa con Git instalado:)
   ```
   git init
   git add .
   git commit -m "Primera versión de EMIN Time Report"
   git branch -M main
   git remote add origin https://github.com/TU_USUARIO/emin-timereport.git
   git push -u origin main
   ```

### PASO C — Crear base de datos en Supabase
1. Ve a https://supabase.com
2. Haz clic en "Start your project" → Sign up gratis
3. Una vez dentro, haz clic en "New project"
4. Rellena:
   - Organization: tu nombre o "Emin"
   - Name: "emin-timereport"
   - Database Password: escribe una contraseña fuerte (¡guárdala!)
   - Region: "West EU (Ireland)" — es la más cercana a España
5. Espera 2-3 minutos a que se cree el proyecto
6. Una vez creado, ve a: Settings → Database
7. En la sección "Connection string" elige "URI"
8. Copia la cadena que empieza con "postgresql://..."
   ⚠️ Reemplaza [YOUR-PASSWORD] por la contraseña que pusiste

   Ejemplo: postgresql://postgres:MiContrasena123@db.xxxxx.supabase.co:5432/postgres

### PASO D — Desplegar en Render
1. Ve a https://render.com
2. Haz clic en "Get Started for Free"
3. Regístrate con tu cuenta de GitHub (más fácil)
4. En el dashboard de Render, haz clic en "New +"
5. Selecciona "Web Service"
6. Conecta tu repositorio de GitHub "emin-timereport"
7. Render detectará automáticamente la configuración. Verifica:
   - Name: emin-timereport
   - Environment: Python 3
   - Build Command: pip install -r requirements.txt
   - Start Command: gunicorn app:app --workers 2 --bind 0.0.0.0:$PORT
8. Haz clic en "Add Environment Variable" y añade:
   - Key: DATABASE_URL
   - Value: (la cadena de Supabase que copiaste en el Paso C)
9. También añade:
   - Key: SECRET_KEY
   - Value: (escribe cualquier texto largo y aleatorio, ej: "emin-super-secret-2024-abcdef")
10. Haz clic en "Create Web Service"
11. Espera 3-5 minutos mientras Render despliega la aplicación

### PASO E — Acceder a tu aplicación
Una vez desplegada, Render te dará una URL como:
https://emin-timereport.onrender.com

¡Esa es tu URL pública! Compártela con tu equipo.

---

## 🔒 CAMBIAR CONTRASEÑAS DE USUARIOS

Para cambiar las contraseñas de los usuarios desde la base de datos en Supabase:

1. Ve a Supabase → Table Editor
2. Selecciona la tabla "usuarios"
3. Para cambiar una contraseña necesitas generar un nuevo hash

   Opción fácil: añade esta ruta temporal a app.py para cambiar contraseñas
   (elimínala después de usarla):

   ```python
   @app.route('/cambiar-password/<username>/<nueva_password>')
   def cambiar_password(username, nueva_password):
       u = Usuario.query.filter_by(username=username).first()
       if u:
           u.set_password(nueva_password)
           db.session.commit()
           return f'Contraseña de {username} actualizada'
       return 'Usuario no encontrado'
   ```

   Luego accede a: https://tu-app.onrender.com/cambiar-password/admin/NuevaContrasena123

---

## 🛠️ AÑADIR NUEVOS USUARIOS

Para añadir usuarios, puedes editar la función `init_db()` en app.py antes
del primer despliegue, o añadir una ruta de administración.

También puedes insertarlos directamente en Supabase:
1. Supabase → Table Editor → usuarios
2. Haz clic en "Insert row"
3. Rellena los campos (para el password_hash usa el endpoint temporal de arriba)

---

## ❓ SOLUCIÓN DE PROBLEMAS FRECUENTES

### "ModuleNotFoundError"
→ Las dependencias no están instaladas. Ejecuta: pip install -r requirements.txt

### "Error de conexión a base de datos"
→ Verifica que DATABASE_URL está bien configurado en las variables de entorno

### La app funciona local pero no en Render
→ Verifica los logs en Render: tu servicio → Events/Logs
→ Asegúrate de que DATABASE_URL está configurado en Environment Variables

### "Application Error" en Render
→ Ve a Render → tu servicio → Logs y busca el error específico

### Los datos no persisten al reiniciar
→ En local sin DATABASE_URL se usa SQLite (normal)
→ En producción verifica que Supabase está conectado

---

## 📞 SOPORTE

Si tienes problemas con el despliegue:
- Render tiene documentación en español: https://render.com/docs
- Supabase tiene soporte en: https://supabase.com/docs

---

## 🔄 ACTUALIZAR LA APLICACIÓN

Cuando quieras hacer cambios:
1. Modifica los archivos en tu ordenador
2. Súbelos a GitHub (repite el Paso B)
3. Render detectará los cambios automáticamente y re-desplegará

---

Creado para Emin Abogados · Sistema de Control Horario Profesional
