from flask import Flask, send_from_directory, request, jsonify, make_response
from flask_cors import CORS
import csv
import uuid  # Para generar tokens únicos
import secrets
from dotenv import load_dotenv
import os
from flask import send_file
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from io import TextIOWrapper, BytesIO
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from sqlalchemy.sql import text
from sqlalchemy.orm import aliased  # Importar aliased
from sqlalchemy.sql import func
from zoneinfo import ZoneInfo
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, case
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from models import (
    db, SesionActiva, Usuario, Producto, Bodega, InventarioBodega, Movimiento, Venta, 
    EstadoInventario, RegistroMovimientos, MaterialProducto, 
    OrdenProduccion, DetalleProduccion, EntregaParcial, AjusteInventarioDetalle
)
# Añadir al inicio después de los imports
import logging

# Configurar logging para Railway
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler()]  # Enviar logs a stdout
)
logger = logging.getLogger(__name__)

# Forzar salida sin buffering para Gunicorn
import sys
if not sys.stdout.isatty():  # Detectar entorno de producción
    sys.stdout = sys.stderr = open('/dev/stdout', 'w', buffering=1)


# Cargar variables del archivo .env
load_dotenv()

# Construir la URI de la base de datos desde variables individuales
PGHOST = os.getenv('PGHOST')
PGDATABASE = os.getenv('PGDATABASE')
PGUSER = os.getenv('PGUSER')
PGPASSWORD = os.getenv('PGPASSWORD')
PGPORT = os.getenv('PGPORT')
# Construir la URI de conexión
DATABASE_URI = f"postgresql+psycopg2://{PGUSER}:{PGPASSWORD}@{PGHOST}:{PGPORT}/{PGDATABASE}"


def obtener_hora_utc():
    """Obtiene la hora actual en UTC."""
    return datetime.now(timezone.utc)

def obtener_hora_colombia(fecha_utc):
    """Convierte una fecha UTC a la hora local de Colombia."""
    if fecha_utc:
        return fecha_utc.astimezone(ZoneInfo('America/Bogota'))
    return None

# Prueba inicial para verificar las funciones de hora
def prueba_horas():
    print("\n=== PRUEBA DE HORAS ===")
    hora_utc = obtener_hora_utc()
    print(f"HORA UTC: {hora_utc} (tipo: {type(hora_utc)})")

    hora_colombia = obtener_hora_colombia(hora_utc)
    print(f"HORA COLOMBIA: {hora_colombia} (tipo: {type(hora_colombia)})")
    print("========================\n")



# Parametros de Usuarios y cantidadd de sesiones concurrentes permitidas
# Usar las variables de entorno
MAX_USUARIOS = int(os.getenv('MAX_USUARIOS', 5))  # Valor por defecto: 5
MAX_SESIONES_CONCURRENTES = int(os.getenv('MAX_SESIONES_CONCURRENTES', 3))  # Valor por defecto: 3

def generate_token():
    """
    Genera un token único y seguro para sesiones activas.
    """
    return secrets.token_hex(32)  # Genera un token hexadecimal de 64 caracteres


def calcular_inventario_producto(producto_id):
    """
    Calcula el inventario total y por bodega para un producto,
    basado en la tabla `estado_inventario`.
    """
    try:
        # Consultar inventario consolidado en estado_inventario
        inventarios = db.session.query(
            EstadoInventario.bodega_id,
            EstadoInventario.cantidad,
            Bodega.nombre.label('bodega_nombre')
        ).join(Bodega, EstadoInventario.bodega_id == Bodega.id
        ).filter(EstadoInventario.producto_id == producto_id).all()

        # Construir el resultado
        resultado = [
            {
                'bodega': inv.bodega_nombre,
                'cantidad': inv.cantidad
            }
            for inv in inventarios
        ]

        return resultado
    except Exception as e:
        print(f"Error en calcular_inventario_producto: {str(e)}")
        return []

# Función para generar consecutivo que escribe en tabla registro_movimientos
def generar_consecutivo():
    ultimo_consecutivo = db.session.query(
        db.func.max(db.cast(RegistroMovimientos.consecutivo, db.String))
    ).scalar() or "T00000"
    try:
        return f"T{int(ultimo_consecutivo[1:]) + 1:05d}"
    except ValueError:
        return "T00001"
    
def registrar_entrega_parcial_logic(orden_id, cantidad_entregada, comentario):
    """Registra una entrega parcial o total, actualiza inventarios y movimientos."""
    # Obtener la orden de producción
    orden = db.session.get(OrdenProduccion, orden_id)
    if not orden or orden.estado not in ["En Producción", "En Producción-Parcial"]:
        raise ValueError("La orden no está en estado válido para registrar producción.")

    # Registrar la entrega
    nueva_entrega = EntregaParcial(
        orden_produccion_id=orden.id,
        cantidad_entregada=cantidad_entregada,
        fecha_entrega=obtener_hora_utc(),
        comentario=comentario
    )
    db.session.add(nueva_entrega)

    producto_id = orden.producto_compuesto_id
    bodega_origen_id = orden.bodega_produccion_id
    bodega_destino_id = orden.bodega_produccion_id  # 🔹 Se mantiene en la misma bodega de producción

    # Descontar materiales utilizados en la producción
    materiales_producto = db.session.query(MaterialProducto).filter_by(
        producto_compuesto_id=producto_id
    ).all()
    for material in materiales_producto:
        cantidad_requerida = material.cantidad * cantidad_entregada
        estado_material = EstadoInventario.query.filter_by(
            bodega_id=bodega_origen_id, producto_id=material.producto_base_id
        ).first()

        if not estado_material or estado_material.cantidad < cantidad_requerida:
            raise ValueError(f"Inventario insuficiente de producto {material.producto_base_id} "
                             f"en la bodega de producción. Requerido: {cantidad_requerida}, "
                             f"Disponible: {estado_material.cantidad if estado_material else 0}")

        estado_material.cantidad -= cantidad_requerida
        estado_material.ultima_actualizacion = obtener_hora_utc()

        # Registrar movimiento de salida para cada material
        movimiento_salida_material = RegistroMovimientos(
            consecutivo=generar_consecutivo(),
            tipo_movimiento='SALIDA',
            producto_id=material.producto_base_id,
            bodega_origen_id=bodega_origen_id,
            bodega_destino_id=None,
            cantidad=cantidad_requerida,
            fecha=obtener_hora_utc(),
            descripcion=f"Salida de mercancía para creación producto con orden de producción {orden.numero_orden}."
        )
        db.session.add(movimiento_salida_material)

    # Actualizar inventario del producto compuesto
    estado_destino = EstadoInventario.query.filter_by(
        bodega_id=bodega_destino_id, producto_id=producto_id
    ).first()
    if not estado_destino:
        estado_destino = EstadoInventario(
            bodega_id=bodega_destino_id,
            producto_id=producto_id,
            cantidad=0,
            ultima_actualizacion=obtener_hora_utc()
        )
        db.session.add(estado_destino)
    estado_destino.cantidad += cantidad_entregada
    estado_destino.ultima_actualizacion = obtener_hora_utc()

    # Calcular cantidad pendiente
    entregas_totales = db.session.query(func.sum(EntregaParcial.cantidad_entregada)).filter_by(
        orden_produccion_id=orden.id
    ).scalar() or 0
    cantidad_pendiente = orden.cantidad_paquetes - entregas_totales

    if cantidad_pendiente <= 0:  # Producción completa
        descripcion = f"Producción completa registrada para la orden {orden.numero_orden}."
    else:  # Producción parcial
        descripcion = f"Producción parcial registrada para la orden {orden.numero_orden}."

    # Registrar movimiento de entrada del producto compuesto
    movimiento_entrada = RegistroMovimientos(
        consecutivo=generar_consecutivo(),
        tipo_movimiento='ENTRADA',
        producto_id=producto_id,
        bodega_origen_id=bodega_origen_id,
        bodega_destino_id=bodega_destino_id,  # 🔹 Se mantiene en la misma bodega de producción
        cantidad=cantidad_entregada,
        fecha=obtener_hora_utc(),
        descripcion=descripcion
    )
    db.session.add(movimiento_entrada)

    db.session.commit()


# Función para calcular el inventario basado en movimientos
def calcular_inventario_por_bodega(producto_id):
    """Calcula el inventario por bodega usando los movimientos."""
    inventario = {}

    movimientos = db.session.query(
        Movimiento.bodega_destino_id.label('bodega_id'),
        func.sum(case([(Movimiento.tipo_movimiento == 'ENTRADA', Movimiento.cantidad)], else_=0)).label('entradas'),
        func.sum(case([(Movimiento.tipo_movimiento == 'VENTA', Movimiento.cantidad)], else_=0)).label('ventas'),
        func.sum(case([(Movimiento.tipo_movimiento == 'TRASLADO', Movimiento.cantidad)], else_=0)).label('traslados_entrantes'),
        func.sum(case([(Movimiento.tipo_movimiento == 'TRASLADO', Movimiento.cantidad)], else_=0)).label('traslados_salientes')
    ).filter(Movimiento.producto_id == producto_id).group_by(Movimiento.bodega_destino_id).all()

    for movimiento in movimientos:
        bodega = Bodega.db.session.get(movimiento.bodega_id)
        if not bodega:
            continue

        entradas = movimiento.entradas or 0
        ventas = movimiento.ventas or 0
        traslados_entrantes = movimiento.traslados_entrantes or 0
        traslados_salientes = movimiento.traslados_salientes or 0

        inventario[bodega.nombre] = entradas + traslados_entrantes - ventas - traslados_salientes

    return inventario

def consultar_kardex(producto_id):
    """Genera el kardex del producto con saldos actualizados por movimiento."""
    movimientos = db.session.query(
        Movimiento.fecha,
        Movimiento.tipo_movimiento,
        Movimiento.cantidad,
        db.case(
            (Movimiento.tipo_movimiento == 'ENTRADA', 'Compra de producto con Factura ' + Movimiento.descripcion),
            (Movimiento.tipo_movimiento == 'VENTA', 'Venta con Factura ' + Movimiento.descripcion),
            (Movimiento.tipo_movimiento == 'TRASLADO', 'Traslado entre bodegas: de ' + Movimiento.bodega_origen.nombre + ' a ' + Movimiento.bodega_destino.nombre),
            else_=''
        ).label('descripcion')
    ).filter(Movimiento.producto_id == producto_id).order_by(Movimiento.fecha).all()

    saldo = 0
    kardex = []

    for movimiento in movimientos:
        if movimiento.tipo_movimiento == 'ENTRADA':
            saldo += movimiento.cantidad
        elif movimiento.tipo_movimiento == 'VENTA':
            saldo -= movimiento.cantidad

        kardex.append({
            'fecha': movimiento.fecha.strftime('%Y-%m-%d %H:%M:%S'),
            'tipo': movimiento.tipo_movimiento,
            'cantidad': movimiento.cantidad,
            'saldo': saldo if movimiento.tipo_movimiento != 'TRASLADO' else None,
            'descripcion': movimiento.descripcion
        })

    return kardex

# Función para generar el kardex
def generar_kardex(producto_id):
    """Genera el kardex de un producto."""
    movimientos = db.session.query(
        Movimiento.fecha,
        Movimiento.tipo_movimiento,
        Movimiento.cantidad,
        case(
            (Movimiento.tipo_movimiento == 'ENTRADA', 'Compra de producto con Factura ' + Movimiento.descripcion),
            (Movimiento.tipo_movimiento == 'VENTA', 'Venta con Factura ' + Movimiento.descripcion),
            (Movimiento.tipo_movimiento == 'TRASLADO', 'Traslado entre bodegas: de ' + Movimiento.bodega_origen_id + ' a ' + Movimiento.bodega_destino_id),
            else_=''
        ).label('descripcion')
    ).filter(Movimiento.producto_id == producto_id).order_by(Movimiento.fecha).all()

    saldo = 0
    kardex = []

    for movimiento in movimientos:
        if movimiento.tipo_movimiento == 'ENTRADA':
            saldo += movimiento.cantidad
        elif movimiento.tipo_movimiento == 'VENTA':
            saldo -= movimiento.cantidad

        kardex.append({
            'fecha': movimiento.fecha.strftime('%Y-%m-%d %H:%M:%S'),
            'tipo': movimiento.tipo_movimiento,
            'cantidad': movimiento.cantidad,
            'saldo': saldo if movimiento.tipo_movimiento != 'TRASLADO' else None,
            'descripcion': movimiento.descripcion
        })

    return kardex

def recalcular_peso_producto_compuesto(producto_id):
    producto = Producto.query.get(producto_id)

    if not producto or not producto.es_producto_compuesto:
        return

    # Sumar el peso de los materiales que lo componen
    materiales = MaterialProducto.query.filter_by(producto_compuesto_id=producto_id).all()
    peso_total = sum(m.cantidad * m.peso_unitario for m in materiales)

    # ✔ Corregimos: el peso total y el peso por unidad deben ser iguales
    producto.peso_total_gr = peso_total
    producto.peso_unidad_gr = peso_total  # 🟢 Aseguramos que sea igual al total

    db.session.commit()


def draw_wrapped_text_ajuste(pdf, x, y, text, max_width):
    """Dibuja texto que salta de línea si excede el ancho máximo y devuelve la altura total usada."""
    words = text.split(" ")
    line = ""
    lines = []
    for word in words:
        test_line = f"{line} {word}".strip()
        if pdf.stringWidth(test_line, "Helvetica", 10) <= max_width:
            line = test_line
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    
    # Dibujar todas las líneas desde la y inicial, hacia abajo
    y_inicial = y
    for i, line in enumerate(lines):
        pdf.drawString(x, y - (i * 15), line)  # Cada línea baja 15 píxeles
    # Devolver la y más baja (posición después de la última línea)
    return y - (len(lines) * 15)


def draw_wrapped_text_traslado(pdf, x, y, text, max_width):
    """Dibuja texto que salta de línea si excede el ancho máximo y devuelve la altura total usada."""
    words = text.split(" ")
    line = ""
    lines = []
    for word in words:
        test_line = f"{line} {word}".strip()
        if pdf.stringWidth(test_line, "Helvetica", 10) <= max_width:
            line = test_line
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    
    y_inicial = y
    for i, line in enumerate(lines):
        pdf.drawString(x, y - (i * 15), line)
    return y - (len(lines) * 15)



def create_app():
    app = Flask(__name__, static_folder='static/dist', static_url_path='')
    # Usar la misma URI global en lugar de hardcoded
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)  # Asocia `db` con la app
    CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

    # Actualizar la verificación de conexión
    with app.app_context():
        try:
            db.session.execute(text("SELECT 1"))
            logger.info("Database connection successful")
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")


    # Rutas API (prioridad alta)
    
    #ENDPOINTS LOGIN
    @app.route('/api/login', methods=['POST'])
    def login():
        try:
            data = request.get_json()
            logger.debug(f"Received data: {data}")
            # 📌 Validar datos de entrada
            if not data.get('usuario') or not data.get('password'):
                logger.debug("Missing usuario or password")
                return jsonify({'message': 'Faltan datos para el inicio de sesión'}), 400
                    
            # 🔍 Buscar usuario en la BD
            usuario = Usuario.query.filter_by(usuario=data['usuario']).first()
            logger.debug(f"Found user: {usuario.usuario if usuario else 'None'}")
            if not usuario or not check_password_hash(usuario.password, data['password']):
                logger.debug(f"Password match for {data['usuario']}: {check_password_hash(usuario.password, data['password']) if usuario else 'No user'}")
                return jsonify({'message': 'Credenciales incorrectas'}), 401

            # 🚫 Validar si el usuario está activo
            if not usuario.activo:
                logger.debug(f"User {data['usuario']} is inactive")
                return jsonify({'message': 'Este usuario está inactivo. Contacta al administrador.'}), 409

            # Eliminar sesiones activas existentes del usuario
            sesiones_existentes = SesionActiva.query.filter_by(usuario_id=usuario.id).all()
            if sesiones_existentes:
                for sesion in sesiones_existentes:
                    db.session.delete(sesion)
                db.session.commit()
                logger.debug(f"{len(sesiones_existentes)} sesiones antiguas eliminadas para el usuario {usuario.usuario}")
            else:
                logger.debug(f"No había sesiones activas previas para el usuario {usuario.usuario}")

            # 🔥 Validar si ya se alcanzó el límite global de sesiones activas
            sesiones_activas_totales = SesionActiva.query.count()
            logger.debug(f"Total active sessions: {sesiones_activas_totales}")
            if sesiones_activas_totales >= MAX_SESIONES_CONCURRENTES:
                logger.debug(f"Max sessions reached: {MAX_SESIONES_CONCURRENTES}")
                return jsonify({'message': f'Se ha alcanzado el número máximo de sesiones activas permitidas ({MAX_SESIONES_CONCURRENTES}). Intenta más tarde.'}), 403

            # 🔑 Generar token y crear nueva sesión activa
            token = generate_token()
            fecha_expiracion = obtener_hora_utc() + timedelta(hours=2)  # ⏳ Expira en 2 horas
            nueva_sesion = SesionActiva(
                usuario_id=usuario.id,
                token=token,
                ultima_actividad=obtener_hora_utc(),
                fecha_expiracion=fecha_expiracion
            )
            db.session.add(nueva_sesion)
            db.session.commit()
            logger.debug(f"Nueva sesión creada para {usuario.usuario}. Expiración: {nueva_sesion.fecha_expiracion}")

            # ✅ Respuesta exitosa
            return jsonify({
                'id': usuario.id,
                'usuario': usuario.usuario,
                'nombres': usuario.nombres,
                'apellidos': usuario.apellidos,
                'tipo_usuario': usuario.tipo_usuario,
                'token': token,
                'message': 'Inicio de sesión exitoso'
            }), 200

        except Exception as e:
            logger.error(f"Error en login: {str(e)}")
            db.session.rollback()
            return jsonify({'error': f'Error al iniciar sesión: {str(e)}'}), 500


    # Middleware: Verificación de sesión activa
    @app.before_request
    def verificar_sesion_activa():
        if request.method == 'OPTIONS':
            return '', 200  # Respuesta exitosa a las solicitudes preflight

        if request.endpoint in ['login', 'logout', 'serve_frontend', 'serve_static', 'debug_static']:
            return  # Permitir acceso a rutas públicas sin verificar el token

        # Extraer el token
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        #print(f"DEBUG: Token recibido: {token}")

        if not token:
            print("DEBUG: Token no proporcionado")
            return jsonify({'message': 'No autorizado. Debes iniciar sesión.'}), 401

        # Buscar la sesión activa en la base de datos
        sesion = SesionActiva.query.filter_by(token=token).first()
        if not sesion:
            print(f"DEBUG: Sesión no encontrada o expirada para el token: {token}")
            return jsonify({'message': 'Sesión no encontrada o expirada.'}), 401

        # Validar tiempo de expiración
        tiempo_actual = obtener_hora_utc()  # Obtiene la hora actual en UTC
        #print(f"DEBUG: Tiempo actual UTC: {tiempo_actual}, Expiración: {sesion.fecha_expiracion}")

        # Convertir fecha_expiracion a UTC si es necesario
        if sesion.fecha_expiracion.tzinfo is None:
            sesion.fecha_expiracion = sesion.fecha_expiracion.replace(tzinfo=timezone.utc)
        else:
            sesion.fecha_expiracion = sesion.fecha_expiracion.astimezone(timezone.utc)

        # Comparar las fechas
        if sesion.fecha_expiracion < tiempo_actual:
            print("DEBUG: Sesión expirada. Eliminando sesión.")
            db.session.delete(sesion)
            db.session.commit()
            return jsonify({'message': 'Sesión expirada. Por favor, inicia sesión nuevamente.'}), 401

        # Actualizar última actividad y extender la sesión
        sesion.ultima_actividad = tiempo_actual
        sesion.fecha_expiracion = tiempo_actual + timedelta(hours=2)  # Extiende la sesión 1 hora más
        #print(f"DEBUG: Última actividad actualizada. Nueva expiración: {sesion.fecha_expiracion}")
        db.session.commit()




    @app.route('/api/logout', methods=['POST'])
    def logout():
        try:
            token = request.headers.get('Authorization').replace('Bearer ', '')
            if not token:
                return jsonify({"message": "Token no proporcionado"}), 400

            sesion = SesionActiva.query.filter_by(token=token).first()
            if not sesion:
                return jsonify({"message": "Sesión no encontrada"}), 404

            db.session.delete(sesion)
            db.session.commit()
            return jsonify({"message": "Sesión cerrada correctamente"}), 200
        except Exception as e:
            print(f"Error al cerrar sesión: {str(e)}")
            return jsonify({"error": "Error al cerrar sesión"}), 500


 
    @app.after_request
    def after_request(response):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Authorization, Content-Type'
        return response




    # Rutas estáticas (prioridad baja)
    @app.route('/')
    def serve_frontend():
        return send_from_directory(app.static_folder, 'index.html')

    @app.route('/<path:path>', methods=['GET'])
    def serve_static(path):
        full_path = os.path.join(app.static_folder, path)
        if os.path.exists(full_path) and not path.startswith('api/'):
            return send_from_directory(app.static_folder, path)
        return send_from_directory(app.static_folder, 'index.html')

    @app.route('/debug-static')
    def debug_static():
        try:
            files = os.listdir(app.static_folder)
            return jsonify({'static_files': files, 'static_folder': app.static_folder})
        except Exception as e:
            return jsonify({'error': str(e), 'static_folder': app.static_folder})

    return app

# Crear la aplicación directamente en el nivel superior
app = create_app()

if __name__ == '__main__':
        
    with app.app_context():
        db.create_all()  # Crea las tablas si no existen
    port = int(os.getenv('PORT', 5000))  # Usa $PORT si existe (Railway), o 5000 por defecto
    app.run(debug=True, host='0.0.0.0', port=port)
