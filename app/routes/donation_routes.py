from flask import Blueprint, request, jsonify, current_app, send_from_directory
from flasgger import swag_from
from app.schemas.donation_schema import validate_donation
from app.services.donation_service import (
    create_donation, list_donations, toggle_donation_availability,
    delete_donation, get_donation_by_id, modify_donation, set_donation_availability, delete_all_donations
)
from app.utils.image_handler import save_image
from flask_jwt_extended import jwt_required, get_jwt_identity

donation_bp = Blueprint('donation', __name__)

@donation_bp.route("/donations", methods=["POST"])
@jwt_required()
def post_donation():
    """
    Crear una nueva donación
    ---
    tags:
      - Donaciones
    consumes:
      - multipart/form-data
    parameters:
      - name: email
        in: formData
        type: string
        required: true
        description: Correo electronico de quien publica
      - name: name
        in: formData
        type: string
        required: true
        description: Nombre de quien dona
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
      400:
        description: Errores de validación
    """
    data = request.form.to_dict()
    data["email"] = get_jwt_identity() 
    data["available"] = True
    data["expiration_date"] = data.get("expiration_date")
    data["name"] = data.get("name")

    city = data.pop("city", "").strip()
    address = data.pop("address", None)
    if address:
        address = address.strip()
    data["location"] = {"city": city, "address": address}

    errors = validate_donation(data)
    if errors:
        return jsonify(errors), 400

    image = request.files.get("image")
    image_url = save_image(image, current_app.config["UPLOAD_FOLDER"]) if image else None
    result = create_donation(data, image_url)
    return jsonify(result), 201

@donation_bp.route("/donations", methods=["GET"])
@jwt_required()
def get_donations():
    """
     Obtener donaciones disponibles (available = true)
    ---
    tags:
      - Donaciones
    responses:
      200:
        description: Lista de donaciones disponibles
    """
    donations = list_donations(only_available=True)
    return jsonify(donations), 200

@donation_bp.route("/donations/all", methods=["GET"])
def get_all_donations():
    """
    Obtener todas las donaciones (disponibles e inactivas)
    ---
    tags:
      - Donaciones
    responses:
      200:
        description: Lista completa de donaciones
    """
    donations = list_donations(only_available=False)
    return jsonify(donations), 200

@donation_bp.route("/donations/<donation_id>", methods=["PUT"])
@jwt_required()
def update_donation_endpoint(donation_id):
    """
    Toggle availability (maintained for backward compatibility)
    ---
    tags:
      - Donaciones
    parameters:
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
    success = toggle_donation_availability(donation_id)
    if not success:
        return jsonify({"error": "Donation not found"}), 404
    return jsonify({"message": "Availability toggled"}), 200

@donation_bp.route("/donations/<donation_id>", methods=["DELETE"])
@jwt_required()
def delete_donation_endpoint(donation_id):
    """
    Eliminar una donación
    ---
    tags:
      - Donaciones
    parameters:
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
    if delete_donation(donation_id):
        return jsonify({"message": "Donación eliminada"}), 200
    return jsonify({"error": "Donación no encontrada"}), 404

@donation_bp.route("/donations/<donation_id>", methods=["GET"])
def get_single_donation(donation_id):
    """
    Get a single donation by ID
    ---
    tags:
      - Donaciones
    parameters:
      - name: donation_id
        in: path
        type: string
        required: true
        description: ID of the donation to retrieve
    responses:
      200:
        description: Donation details
      404:
        description: Donation not found
    """
    donation = get_donation_by_id(donation_id)
    if not donation:
        return jsonify({"error": "Donación no encontrada"}), 404

    return jsonify({
        "id": str(donation["_id"]),
        "email": donation["email"],
        "name": donation["name"],
        "title": donation["title"],
        "description": donation["description"],
        "category": donation["category"],
        "condition": donation["condition"],
        "expiration_date": donation.get("expiration_date"),
        "available": donation.get("available", True),
        "city": donation["location"]["city"],
        "address": donation["location"].get("address"),
        "image_url": donation.get("image_url"),
        "created_at": donation["created_at"].isoformat()
    }), 200

@donation_bp.route('/uploads/<path:filename>', methods=["GET"])
def serve_uploaded_file(filename):
    """
    Servir archivos subidos (imágenes)
    ---
    tags:
      - Donaciones
    parameters:
      - name: filename
        in: path
        type: string
        required: true
        description: Nombre del archivo a servir
    responses:
      200:
        description: Archivo encontrado y servido
      404:
        description: Archivo no encontrado
    """
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

@donation_bp.route("/donations/user", methods=["GET"])
@jwt_required()
def get_user_donations():
    """
    Obtener todas las donaciones del usuario actual
    ---
    tags:
      - Donaciones
    security:
      - JWT: []
    responses:
      200:
        description: Lista de donaciones del usuario autenticado
      401:
        description: No autorizado - token inválido o no proporcionado
    """
    email = get_jwt_identity()
    donations = [d for d in list_donations(only_available=False) if d["email"] == email]
    return jsonify(donations), 200

@donation_bp.route("/donations/user/<donation_id>", methods=["PUT"])
@jwt_required()
def update_user_donation(donation_id):
    """
    Modificar una donación del usuario actual
    ---
    tags:
      - Donaciones
    security:
      - JWT: []
    consumes:
      - multipart/form-data
    parameters:
      - name: donation_id
        in: path
        type: string
        required: true
        description: ID de la donación a modificar
      - name: title
        in: formData
        type: string
        required: false
        description: Nuevo título del artículo
      - name: description
        in: formData
        type: string
        required: false
        description: Nueva descripción
      - name: category
        in: formData
        type: string
        required: false
        enum: [Ropa, Alimentos, Muebles, Juguetes, Electrodomesticos]
        description: Nueva categoría
      - name: condition
        in: formData
        type: string
        required: false
        enum: [Usado, En perfecto estado, Usado una vez, Nuevo, Perecedero, No perecedero]
        description: Nuevo estado
      - name: expiration_date
        in: formData
        type: string
        required: false
        description: Nueva fecha de caducidad (YYYY-MM-DD)
      - name: city
        in: formData
        type: string
        required: false
        description: Nueva ciudad
      - name: address
        in: formData
        type: string
        required: false
        description: Nueva dirección
      - name: image
        in: formData
        type: file
        required: false
        description: Nueva imagen del producto
    responses:
      200:
        description: Donación modificada exitosamente
      404:
        description: Donación no encontrada
      401:
        description: No autorizado - token inválido o no proporcionado
    """
    image = request.files.get("image")
    image_url = save_image(image, current_app.config["UPLOAD_FOLDER"]) if image else None
    success = modify_donation(donation_id, request.form.to_dict(), image_url)
    if success:
        return jsonify({"message": "Publicacion modificada"}), 200
    return jsonify({"error": "Donación no encontrada"}), 404

@donation_bp.route("/donations/<donation_id>/availability", methods=["PATCH"])
@jwt_required()
def set_availability_endpoint(donation_id):
    """
    Establecer disponibilidad de una donación
    ---
    tags:
      - Donaciones
    security:
      - JWT: []
    parameters:
      - name: donation_id
        in: path
        type: string
        required: true
        description: ID de la donación
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            available:
              type: boolean
              description: Nuevo estado de disponibilidad
    responses:
      200:
        description: Disponibilidad actualizada
      400:
        description: Falta el estado de disponibilidad
      404:
        description: Donación no encontrada
      401:
        description: No autorizado - token inválido o no proporcionado
    """
    data = request.get_json()
    if not data or 'available' not in data:
        return jsonify({"error": "Missing availability status"}), 400
    success = set_donation_availability(donation_id, data['available'])
    if not success:
        return jsonify({"error": "Donation not found"}), 404
    return jsonify({"message": "Availability updated"}), 200

@donation_bp.route("/donations/all", methods=["DELETE"])
@jwt_required()
def delete_all():
    """
    Eliminar todas las donaciones (uso restringido)
    ---
    tags:
      - Donaciones
    responses:
      200:
        description: Todas las donaciones han sido eliminadas
    """
    count = delete_all_donations()
    return jsonify({"message": f"{count} donaciones eliminadas"}), 200