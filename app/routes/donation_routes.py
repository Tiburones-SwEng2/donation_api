from flask import Blueprint, request, jsonify, current_app, send_from_directory
from flasgger import swag_from
from app.schemas.donation_schema import validate_donation
from app.services.donation_service import (
    create_donation, list_donations, toggle_donation_availability,
    delete_donation, get_donation_by_id, modify_donation, set_donation_availability, delete_all_donations
)
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.utils.image_handler import save_image

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
    image = request.files.get("image")

    # Ajuste: Valor por defecto para "available"
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
def get_all_donations():
    """
    Obtener todas las donaciones (disponibles e inactivas)
    ---
    tags:
      - Donaciones
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
def update_donation_endpoint(donation_id):
    """
    Alternar disponibilidad de una donación (true <-> false)
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
        schema:
          type: object
          properties:
            id:
              type: string
            email:
              type: string
            name:
              type: string
            title:
              type: string
            description:
              type: string
            category:
              type: string
            condition:
              type: string
            expiration_date:
              type: string
            available:
              type: boolean
            city:
              type: string
            address:
              type: string
            image_url:
              type: string
            created_at:
              type: string
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
    Servir archivos subidos (imágenes de donaciones)
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
        schema:
          type: object
          properties:
            message:
              type: string
              example: "5 donaciones eliminadas"
    """
    count = delete_all_donations()
    return jsonify({"message": f"{count} donaciones eliminadas"}), 200