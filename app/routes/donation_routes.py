from flask import Blueprint, request, jsonify, current_app
from flasgger import swag_from, Swagger
from app.schemas.donation_schema import validate_donation
from app.services.donation_service import create_donation
from app.utils.image_handler import save_image
from app.services.donation_service import list_donations
from flask import send_from_directory, current_app

donation_bp = Blueprint('donation', __name__)

@donation_bp.route("/donations", methods=["POST"])
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
    from app.services.donation_service import toggle_donation_availability
    success = toggle_donation_availability(donation_id)

    if success:
        return jsonify({"message": "Estado de disponibilidad actualizado"}), 200
    return jsonify({"error": "Donación no encontrada"}), 404

@donation_bp.route("/donations/<donation_id>", methods=["DELETE"])
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
    from app.services.donation_service import delete_donation
    if delete_donation(donation_id):
        return jsonify({"message": "Donación eliminada"}), 200
    return jsonify({"error": "Donación no encontrada"}), 404


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
