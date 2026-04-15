"""
EMIN TIME REPORT - Aplicación de Control Horario
================================================
Despacho de Abogados Emin
Backend: Flask (Python)
Base de datos: PostgreSQL (Supabase)
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import os
from functools import wraps

# ─────────────────────────────────────────────
# CONFIGURACIÓN DE LA APLICACIÓN
# ─────────────────────────────────────────────
app = Flask(__name__)

# Clave secreta para sesiones (cámbiala en producción)
app.secret_key = os.environ.get('SECRET_KEY', 'emin-secret-key-2024-cambiar')

# URL de la base de datos (viene de variable de entorno en producción)
# En local usa SQLite para pruebas; en producción usa PostgreSQL de Supabase
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///emin_local.db')

# Supabase a veces devuelve URLs con "postgres://" en lugar de "postgresql://"
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# ─────────────────────────────────────────────
# MODELOS DE BASE DE DATOS
# ─────────────────────────────────────────────

class Usuario(db.Model):
    """Tabla de usuarios del sistema"""
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)           # Nombre completo
    username = db.Column(db.String(50), unique=True, nullable=False)  # Login
    password_hash = db.Column(db.String(255), nullable=False)    # Contraseña encriptada
    rol = db.Column(db.String(20), nullable=False, default='worker')  # 'worker' o 'admin'
    activo = db.Column(db.Boolean, default=True)
    creado = db.Column(db.DateTime, default=datetime.utcnow)

    # Relación: un usuario tiene muchas tareas
    tareas = db.relationship('Tarea', backref='usuario', lazy=True)

    def set_password(self, password):
        """Encripta la contraseña antes de guardarla"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verifica si la contraseña introducida es correcta"""
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'username': self.username,
            'rol': self.rol
        }


class Tarea(db.Model):
    """Tabla de tareas/entradas de tiempo"""
    __tablename__ = 'tareas'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)        # Tipo de tarea
    hora_inicio = db.Column(db.Time, nullable=False)       # Hora de inicio
    hora_fin = db.Column(db.Time, nullable=False)          # Hora de fin
    cliente = db.Column(db.String(150))                    # Nombre del cliente/empresa
    dni_nif = db.Column(db.String(20))                     # DNI/NIF del cliente
    fecha = db.Column(db.Date, nullable=False, default=date.today)
    notas = db.Column(db.Text)                             # Notas adicionales
    creado = db.Column(db.DateTime, default=datetime.utcnow)

    def duracion_horas(self):
        """Calcula la duración en horas entre hora_inicio y hora_fin"""
        inicio = datetime.combine(date.today(), self.hora_inicio)
        fin = datetime.combine(date.today(), self.hora_fin)
        diff = fin - inicio
        return round(diff.total_seconds() / 3600, 2)

    def es_productiva(self):
        """Retorna True si la tarea es productiva (no es Descanso ni Reunión interna)"""
        return self.tipo not in ['Descanso', 'Reunión interna']

    def to_dict(self):
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'usuario_nombre': self.usuario.nombre if self.usuario else '',
            'tipo': self.tipo,
            'hora_inicio': self.hora_inicio.strftime('%H:%M'),
            'hora_fin': self.hora_fin.strftime('%H:%M'),
            'cliente': self.cliente or '',
            'dni_nif': self.dni_nif or '',
            'fecha': self.fecha.strftime('%Y-%m-%d'),
            'notas': self.notas or '',
            'duracion': self.duracion_horas(),
            'productiva': self.es_productiva()
        }


# ─────────────────────────────────────────────
# DECORADORES DE AUTENTICACIÓN
# ─────────────────────────────────────────────

def login_required(f):
    """Decorator: redirige al login si el usuario no ha iniciado sesión"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator: solo permite acceso a administradores"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        if session.get('rol') != 'admin':
            return jsonify({'error': 'Acceso denegado. Solo administradores.'}), 403
        return f(*args, **kwargs)
    return decorated_function


# ─────────────────────────────────────────────
# RUTAS DE PÁGINAS
# ─────────────────────────────────────────────

@app.route('/')
def index():
    """Página principal - redirige según estado de sesión"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Página de inicio de sesión"""
    if request.method == 'GET':
        if 'user_id' in session:
            return redirect(url_for('dashboard'))
        return render_template('login.html')

    # Procesar formulario de login
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')

    usuario = Usuario.query.filter_by(username=username, activo=True).first()

    if usuario and usuario.check_password(password):
        # Guardar datos en sesión
        session['user_id'] = usuario.id
        session['username'] = usuario.username
        session['nombre'] = usuario.nombre
        session['rol'] = usuario.rol
        return jsonify({'success': True, 'rol': usuario.rol})
    else:
        return jsonify({'success': False, 'error': 'Usuario o contraseña incorrectos'}), 401


@app.route('/logout')
def logout():
    """Cerrar sesión"""
    session.clear()
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard principal de la aplicación"""
    return render_template('dashboard.html',
                           nombre=session['nombre'],
                           rol=session['rol'],
                           username=session['username'])


# ─────────────────────────────────────────────
# API: TAREAS
# ─────────────────────────────────────────────

@app.route('/api/tareas', methods=['GET'])
@login_required
def get_tareas():
    """Obtener tareas con filtros opcionales"""
    user_id = session['user_id']
    rol = session['rol']

    # Parámetros de filtro
    filtro_usuario = request.args.get('usuario_id')
    filtro_dni = request.args.get('dni_nif', '').strip()
    filtro_fecha_desde = request.args.get('fecha_desde')
    filtro_fecha_hasta = request.args.get('fecha_hasta')

    # Base de la consulta
    query = Tarea.query

    # Los workers solo ven sus propias tareas
    if rol == 'worker':
        query = query.filter_by(usuario_id=user_id)
    elif rol == 'admin' and filtro_usuario:
        query = query.filter_by(usuario_id=filtro_usuario)

    # Filtro por DNI/NIF
    if filtro_dni:
        query = query.filter(Tarea.dni_nif.ilike(f'%{filtro_dni}%'))

    # Filtro por fecha
    if filtro_fecha_desde:
        query = query.filter(Tarea.fecha >= filtro_fecha_desde)
    if filtro_fecha_hasta:
        query = query.filter(Tarea.fecha <= filtro_fecha_hasta)

    # Ordenar por fecha y hora de creación (más reciente primero)
    tareas = query.order_by(Tarea.fecha.desc(), Tarea.creado.desc()).all()

    return jsonify([t.to_dict() for t in tareas])


@app.route('/api/tareas', methods=['POST'])
@login_required
def crear_tarea():
    """Crear una nueva tarea"""
    data = request.get_json()

    # Validaciones de campos obligatorios
    campos_requeridos = ['tipo', 'hora_inicio', 'hora_fin']
    for campo in campos_requeridos:
        if not data.get(campo):
            return jsonify({'error': f'El campo {campo} es obligatorio'}), 400

    # Para tareas de cliente, DNI y nombre son obligatorios
    if data.get('tipo') == 'Trabajo cliente':
        if not data.get('dni_nif'):
            return jsonify({'error': 'El DNI/NIF es obligatorio para tareas de cliente'}), 400
        if not data.get('cliente'):
            return jsonify({'error': 'El nombre del cliente es obligatorio'}), 400

    # Parsear horas
    try:
        hora_inicio = datetime.strptime(data['hora_inicio'], '%H:%M').time()
        hora_fin = datetime.strptime(data['hora_fin'], '%H:%M').time()
    except ValueError:
        return jsonify({'error': 'Formato de hora inválido. Use HH:MM'}), 400

    # Validar que hora_fin > hora_inicio
    if hora_fin <= hora_inicio:
        return jsonify({'error': 'La hora de fin debe ser posterior a la hora de inicio'}), 400

    # Parsear fecha (si no viene, usar hoy)
    try:
        fecha = datetime.strptime(data.get('fecha', date.today().strftime('%Y-%m-%d')), '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Formato de fecha inválido'}), 400

    # Crear la tarea
    tarea = Tarea(
        usuario_id=session['user_id'],
        tipo=data['tipo'],
        hora_inicio=hora_inicio,
        hora_fin=hora_fin,
        cliente=data.get('cliente', ''),
        dni_nif=data.get('dni_nif', '').upper(),
        fecha=fecha,
        notas=data.get('notas', '')
    )

    db.session.add(tarea)
    db.session.commit()

    return jsonify({'success': True, 'tarea': tarea.to_dict()}), 201


@app.route('/api/tareas/<int:tarea_id>', methods=['DELETE'])
@login_required
def eliminar_tarea(tarea_id):
    """Eliminar una tarea"""
    tarea = Tarea.query.get_or_404(tarea_id)

    # Solo el propietario o admin puede eliminar
    if tarea.usuario_id != session['user_id'] and session['rol'] != 'admin':
        return jsonify({'error': 'No tienes permiso para eliminar esta tarea'}), 403

    db.session.delete(tarea)
    db.session.commit()
    return jsonify({'success': True})


@app.route('/api/resumen', methods=['GET'])
@login_required
def get_resumen():
    """Obtener resumen de horas productivas/improductivas"""
    user_id = session['user_id']
    rol = session['rol']

    filtro_usuario = request.args.get('usuario_id')
    filtro_fecha_desde = request.args.get('fecha_desde')
    filtro_fecha_hasta = request.args.get('fecha_hasta')

    query = Tarea.query

    if rol == 'worker':
        query = query.filter_by(usuario_id=user_id)
    elif rol == 'admin' and filtro_usuario:
        query = query.filter_by(usuario_id=filtro_usuario)

    if filtro_fecha_desde:
        query = query.filter(Tarea.fecha >= filtro_fecha_desde)
    if filtro_fecha_hasta:
        query = query.filter(Tarea.fecha <= filtro_fecha_hasta)

    tareas = query.all()

    horas_productivas = sum(t.duracion_horas() for t in tareas if t.es_productiva())
    horas_improductivas = sum(t.duracion_horas() for t in tareas if not t.es_productiva())

    return jsonify({
        'horas_productivas': round(horas_productivas, 2),
        'horas_improductivas': round(horas_improductivas, 2),
        'total_tareas': len(tareas)
    })


# ─────────────────────────────────────────────
# API: USUARIOS (solo admin)
# ─────────────────────────────────────────────

@app.route('/api/usuarios', methods=['GET'])
@login_required
def get_usuarios():
    """Obtener lista de usuarios (admin) o datos propios (worker)"""
    if session['rol'] == 'admin':
        usuarios = Usuario.query.filter_by(activo=True).all()
        return jsonify([u.to_dict() for u in usuarios])
    else:
        usuario = Usuario.query.get(session['user_id'])
        return jsonify([usuario.to_dict()])


# ─────────────────────────────────────────────
# API: EXPORTAR A EXCEL
# ─────────────────────────────────────────────

@app.route('/api/exportar', methods=['GET'])
@login_required
def exportar_excel():
    """Exportar datos a Excel usando openpyxl"""
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    from flask import send_file
    import io

    user_id = session['user_id']
    rol = session['rol']

    filtro_usuario = request.args.get('usuario_id')
    filtro_dni = request.args.get('dni_nif', '').strip()
    filtro_fecha_desde = request.args.get('fecha_desde')
    filtro_fecha_hasta = request.args.get('fecha_hasta')

    query = Tarea.query
    if rol == 'worker':
        query = query.filter_by(usuario_id=user_id)
    elif rol == 'admin' and filtro_usuario:
        query = query.filter_by(usuario_id=filtro_usuario)

    if filtro_dni:
        query = query.filter(Tarea.dni_nif.ilike(f'%{filtro_dni}%'))
    if filtro_fecha_desde:
        query = query.filter(Tarea.fecha >= filtro_fecha_desde)
    if filtro_fecha_hasta:
        query = query.filter(Tarea.fecha <= filtro_fecha_hasta)

    tareas = query.order_by(Tarea.fecha.desc()).all()

    # Crear libro de Excel
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Informe de Horas"

    # Estilos
    color_header = "1a2744"
    color_productiva = "d4edda"
    color_improductiva = "fff3cd"

    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill(start_color=color_header, end_color=color_header, fill_type="solid")
    header_align = Alignment(horizontal="center", vertical="center")

    thin_border = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin')
    )

    # Título del informe
    ws.merge_cells('A1:H1')
    ws['A1'] = f"INFORME DE HORAS - EMIN ABOGADOS"
    ws['A1'].font = Font(bold=True, size=14, color="1a2744")
    ws['A1'].alignment = Alignment(horizontal="center")

    ws.merge_cells('A2:H2')
    ws['A2'] = f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    ws['A2'].alignment = Alignment(horizontal="center")
    ws['A2'].font = Font(size=10, color="666666")

    # Cabeceras
    headers = ['Fecha', 'Usuario', 'Tipo de Tarea', 'Hora Inicio',
               'Hora Fin', 'Duración (h)', 'Cliente', 'DNI/NIF']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=4, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_align
        cell.border = thin_border

    # Datos
    for row_idx, tarea in enumerate(tareas, 5):
        es_productiva = tarea.es_productiva()
        fill_color = color_productiva if es_productiva else color_improductiva
        row_fill = PatternFill(start_color=fill_color, end_color=fill_color, fill_type="solid")

        valores = [
            tarea.fecha.strftime('%d/%m/%Y'),
            tarea.usuario.nombre,
            tarea.tipo,
            tarea.hora_inicio.strftime('%H:%M'),
            tarea.hora_fin.strftime('%H:%M'),
            tarea.duracion_horas(),
            tarea.cliente or '',
            tarea.dni_nif or ''
        ]

        for col_idx, valor in enumerate(valores, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=valor)
            cell.fill = row_fill
            cell.border = thin_border
            cell.alignment = Alignment(vertical="center")

    # Fila de totales
    total_row = len(tareas) + 6
    ws.cell(row=total_row, column=1, value="TOTALES").font = Font(bold=True)
    ws.cell(row=total_row, column=6, value=round(sum(t.duracion_horas() for t in tareas), 2)).font = Font(bold=True)

    # Ajustar anchos de columnas
    anchos = [12, 20, 20, 12, 12, 14, 25, 15]
    for i, ancho in enumerate(anchos, 1):
        ws.column_dimensions[get_column_letter(i)].width = ancho

    # Guardar en memoria y enviar
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f"emin_informe_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     as_attachment=True, download_name=filename)


# ─────────────────────────────────────────────
# INICIALIZACIÓN: CREAR TABLAS Y USUARIOS
# ─────────────────────────────────────────────

def init_db():
    """Crear tablas y usuarios iniciales si no existen"""
    with app.app_context():
        db.create_all()

        # Crear usuarios iniciales solo si no existen
        if Usuario.query.count() == 0:
            usuarios_iniciales = [
                {
                    'nombre': 'Administrador CEO',
                    'username': 'admin',
                    'password': 'Emin2024!',
                    'rol': 'admin'
                },
                {
                    'nombre': 'Trabajador Uno',
                    'username': 'trabajador1',
                    'password': 'Emin2024!',
                    'rol': 'worker'
                },
                {
                    'nombre': 'Trabajador Dos',
                    'username': 'trabajador2',
                    'password': 'Emin2024!',
                    'rol': 'worker'
                }
            ]

            for u_data in usuarios_iniciales:
                usuario = Usuario(
                    nombre=u_data['nombre'],
                    username=u_data['username'],
                    rol=u_data['rol']
                )
                usuario.set_password(u_data['password'])
                db.session.add(usuario)

            db.session.commit()
            print("✅ Usuarios iniciales creados correctamente")
        else:
            print("ℹ️  Los usuarios ya existen en la base de datos")


# ─────────────────────────────────────────────
# PUNTO DE ENTRADA
# ─────────────────────────────────────────────

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
