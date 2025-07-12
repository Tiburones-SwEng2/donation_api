from flask import Blueprint, request, jsonify, current_app, Flask, send_from_directory
from flasgger import swag_from, Swagger
from app.schemas.donation_schema import validate_donation
from app.services.donation_service import create_donation
from app.utils.image_handler import save_image
from app.services.donation_service import list_donations
from flask_jwt_extended import jwt_required, get_jwt_identity
from prometheus_client import Counter, Histogram, generate_latest
import time
from functools import wraps

app = Flask(__name__)

# MÉTRICAS
REQUEST_COUNT = Counter('http_requests_total', 'Total Requests', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'Request Latency', ['endpoint'])
ERROR_COUNT = Counter('http_request_errors_total', 'Total Errors', ['endpoint'])

def monitor_metrics(f):
    """Decorador para monitorear métricas de Prometheus"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        endpoint = request.endpoint or 'unknown'
        method = request.method
        
        # Incrementar contador de requests
        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        
        try:
            # Ejecutar la función
            response = f(*args, **kwargs)
            return response
        except Exception as e:
            # Incrementar contador de errores
            ERROR_COUNT.labels(endpoint=endpoint).inc()
            raise
        finally:
            # Medir latencia
            duration = time.time() - start_time
            REQUEST_LATENCY.labels(endpoint=endpoint).observe(duration)
    
    return decorated_function

donation_bp = Blueprint('donation', __name__)

@donation_bp.route("/donations", methods=["POST"])
@jwt_required()
@monitor_metrics
def post_donation():
    """
    Crear una nueva donación
    ---
    tags:
      - Donaciones
    consumes:
      - multipart/form-data
    parameters:
      - name: Authorization
        in: header
        required: true
        type: string
        description: "Formato: Bearer [Token]"
      - name: email
        in: formData
        type: string
        required: true
        description: Correo electronico de quien publica
      - name: name
        in: formData
        type: string
        required: true
        description: Nombre del donador
      - name: title
        in: formData
        type: string
        required: true
        description: Nombre del articulo a donar
      - name: description
        in: formData
        type: string
        required: true
        description: Descripción detallada
      - name: category
        in: formData
        type: string
        required: true
        enum: [Ropa, Alimentos, Muebles, Juguetes, Electrodomesticos]
        description: Categoría del producto
      - name: condition
        in: formData
        type: string
        required: true
        enum: [Usado, En perfecto estado, Usado una vez, Nuevo, Perecedero, No perecedero]
        description: Estado del producto
      - name: expiration_date
        in: formData
        type: string
        required: false
        description: Fecha de caducidad en formato YYYY-MM-DD (solo para alimentos)
      - name: city
        in: formData
        type: string
        required: true
        description: Ciudad donde se encuentra el producto
      - name: address
        in: formData
        type: string
        required: false
        description: Dirección (opcional)
      - name: image
        in: formData
        type: file
        required: true
        description: Imagen del producto (opcional)
    responses:
      201:
        description: Donación creada exitosamente
        schema:
          type: object
          properties:
            id:
              type: string
              example: 64a89f1234abcdef5678abcd
            message:
              type: string
              example: Donación creada
      400:
        description: Errores de validación
        schema:
          type: object
          example:
            title: Este campo es obligatorio
    """
    data = request.form.to_dict()
    data["email"] = get_jwt_identity() 
    image = request.files.get("image")

    # Ajuste: Valor por defecto para "available"
    data["available"] = True
    data["expiration_date"] = data.get("expiration_date")  # puede ser None si no viene

    city = data.pop("city", "").strip()
    address = data.pop("address", None)
    if address:
      address = address.strip()
    data["location"] = {"city": city, "address": address}

    # Validar con función existente
    errors = validate_donation(data)
    if errors:
        return jsonify(errors), 400

    image_url = save_image(image, current_app.config["UPLOAD_FOLDER"]) if image else None
    result = create_donation(data, image_url)
    return jsonify(result), 201


@donation_bp.route("/donations", methods=["GET"])
@jwt_required()
@monitor_metrics
def get_donations():
    """
     Obtener donaciones disponibles (available = true)
    ---
    tags:
      - Donaciones
    parameters:
      - name: Authorization
        in: header
        required: true
        type: string
        description: "Formato: Bearer [Token]"
    responses:
      200:
        description: Lista de donaciones disponibles
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: string
                example: 64a89f1234abcdef5678abcd
              email:
                type: string
                example: myemail@mail.com
              title:
                type: string
                example: Ropa en buen estado
              description:
                type: string
                example: Varias prendas de invierno
              category:
                type: string
                example: Ropa
              condition:
                type: string
                example: Usado
              expiration_date:
                type: string
                format: date
                example: Null
              available:
                type: boolean
                example: true
              city:
                type: string
                example: Cali
              address:
                type: string
                example: Null
              image_url:
                type: string
                example: http://localhost:5000/uploads/imagen123.jpg
              created_at:
                type: string
                format: date-time
                example: 2024-06-02T12:00:00
    """
    donations = list_donations(only_available=True)
    return jsonify(donations), 200

@donation_bp.route("/donations/all", methods=["GET"])
@monitor_metrics
def get_all_donations():
    """
    Obtener todas las donaciones (disponibles e inactivas)
    ---
    tags:
      - Donaciones
    parameters:
      - name: Authorization
        in: header
        required: true
        type: string
        description: "Formato: Bearer [Token]"
    responses:
      200:
        description: Lista completa de donaciones
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: string
                example: 64a89f1234abcdef5678abcd
              email:
                type: string
                example: myemail@mail.com
              title:
                type: string
                example: Ropa en buen estado
              description:
                type: string
                example: Varias prendas de invierno
              category:
                type: string
                example: Ropa
              condition:
                type: string
                example: Usado
              expiration_date:
                type: string
                format: date
                example: Null
              available:
                type: boolean
                example: false
              city:
                type: string
                example: Cali
              address:
                type: string
                example: Null
              image_url:
                type: string
                example: http://localhost:5000/uploads/imagen123.jpg
              created_at:
                type: string
                format: date-time
                example: 2024-06-02T12:00:00
    """
    donations = list_donations(only_available=False)
    return jsonify(donations), 200


@donation_bp.route("/donations/<donation_id>", methods=["PUT"])
@jwt_required()
@monitor_metrics
def update_donation_endpoint(donation_id):
    """
    Alternar disponibilidad de una donación (true <-> false)
    ---
    tags:
      - Donaciones
    parameters:
      - name: Authorization
        in: header
        required: true
        type: string
        description: "Formato: Bearer [Token]"
      - name: donation_id
        in: path
        type: string
        required: true
        description: ID de la donación a actualizar
    responses:
      200:
        description: Donación actualizada
      404:
        description: Donación no encontrada
    """
    from app.services.donation_service import toggle_donation_availability
    success = toggle_donation_availability(donation_id)

    if success:
        return jsonify({"message": "Estado de disponibilidad actualizado"}), 200
    return jsonify({"error": "Donación no encontrada"}), 404

@donation_bp.route("/donations/<donation_id>", methods=["DELETE"])
@jwt_required()
@monitor_metrics
def delete_donation_endpoint(donation_id):
    """
    Eliminar una donación
    ---
    tags:
      - Donaciones
    parameters:
      - name: Authorization
        in: header
        required: true
        type: string
        description: "Formato: Bearer [Token]"
      - name: donation_id
        in: path
        type: string
        required: true
        description: ID de la donación a eliminar
      
    responses:
      200:
        description: Donación eliminada exitosamente
      404:
        description: Donación no encontrada
    """
    from app.services.donation_service import delete_donation
    if delete_donation(donation_id):
        return jsonify({"message": "Donación eliminada"}), 200
    return jsonify({"error": "Donación no encontrada"}), 404


@donation_bp.route('/uploads/<path:filename>', methods=["GET"])
@jwt_required()
@monitor_metrics
def serve_uploaded_file(filename):
    """
    Servir archivos subidos (imágenes de donaciones)
    ---
    tags:
      - Donaciones
    parameters:
      - name: Authorization
        in: header
        required: true
        type: string
        description: "Formato: Bearer [Token]"
      - name: filename
        in: path
        type: string
        required: true
        description: Nombre del archivo a servir
    responses:
      200:
        description: Imagen encontrada
        content:
          image/jpeg:
            schema:
              type: string
              format: binary
      404:
        description: Imagen no encontrada
    """
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

@donation_bp.route("/donations/user", methods=["GET"])
@jwt_required()
@monitor_metrics
def get_user_donations():
    """
    Listar las donaciones de un usuario
    ---
    tags:
      - Donaciones
    parameters:
      - in : header
        name: Authorization
        required: true
        type: string
        description: "Formato: Bearer [Token]"
    responses:
      200:
        description: Lista retornada
    """
    email = get_jwt_identity()
    donations = [d for d in list_donations(only_available=False) if d["email"] == email]
    print(email)
    return jsonify(donations), 200

@donation_bp.route("/donations/user/<donation_id>", methods=["PUT"])
@jwt_required()
@monitor_metrics
def update_user_donation(donation_id):
    """
    Modificar una donacion de un usuario
    ---
    tags:
      - Donaciones
    consumes:
      - multipart/form-data
    parameters:
      - name: Authorization
        in: header
        required: true
        type: string
        description: "Formato: Bearer [Token]"
      - name: donation_id
        in: path
        type: string
        required: true
        description: ID de la donación a modificar
      - name: title
        in: formData
        type: string
        required: false
        description: Nombre del articulo a donar
      - name: description
        in: formData
        type: string
        required: false
        description: Descripción detallada
      - name: category
        in: formData
        type: string
        required: false
        enum: [Ropa, Alimentos, Muebles, Juguetes, Electrodomesticos]
        description: Categoría del producto
      - name: condition
        in: formData
        type: string
        required: false
        enum: [Usado, En perfecto estado, Usado una vez, Nuevo, Perecedero, No perecedero]
        description: Estado del producto
      - name: expiration_date
        in: formData
        type: string
        required: false
        description: Fecha de caducidad en formato YYYY-MM-DD (solo para alimentos)
      - name: city
        in: formData
        type: string
        required: false
        description: Ciudad donde se encuentra el producto
      - name: address
        in: formData
        type: string
        required: false
        description: Dirección (opcional)
      - name: image
        in: formData
        type: file
        required: false
        description: Imagen del producto (opcional)
    responses:
      200:
        description: Lista retornada
    """
    from app.services.donation_service import modify_donation
    image = request.files.get("image")
    image_url = save_image(image, current_app.config["UPLOAD_FOLDER"]) if image else None
    success = modify_donation(donation_id, request.form.to_dict(), image_url)

    if success:
        return jsonify({"message": "Publicacion modificada"}), 200
    return jsonify({"error": "Donación no encontrada"}), 404

@donation_bp.route("/metrics", methods=["GET"])
def metrics():
    """
    Endpoint para exponer métricas de Prometheus
    ---
    tags:
      - Métricas
    responses:
      200:
        description: Métricas de Prometheus
        content:
          text/plain:
            schema:
              type: string
    """
    return generate_latest(), 200, {'Content-Type': 'text/plain; charset=utf-8'}
