import datetime
import re

def validate_donation(data):
    errors = {}
    
    # Validación de campos obligatorios
    required_fields = {
        "title": "Este campo es obligatorio",
        "description": "Este campo es obligatorio",
        "category": "Debe seleccionar una categoría",
        "condition": "Debe especificar la condición",
        "email": "El email es obligatorio"
    }
    
    for field, message in required_fields.items():
        if not data.get(field):
            errors[field] = message

    # Validación de email
    if "email" in data and data["email"]:
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, data["email"]):
            errors["email"] = "Formato de email inválido"

    # Validación de categoría y condición
    category = data.get("category")
    condition = data.get("condition")
    
    if category and condition:
        conditions_map = {
            "Alimentos": ["Perecedero", "No perecedero"],
            "default": ["Usado", "En perfecto estado", "Usado una vez", "Nuevo", "No aplica"]
        }
        
        valid_conditions = conditions_map.get(category, conditions_map["default"])
        if condition not in valid_conditions:
            error_msg = {
                "Alimentos": "Debe ser 'Perecedero' o 'No perecedero' para alimentos",
                "default": "Condición no válida para esta categoría"
            }
            errors["condition"] = error_msg.get(category, error_msg["default"])

    # Validación de fecha de expiración
    if category == "Alimentos" and "expiration_date" in data:
        try:
            exp_date = datetime.datetime.strptime(data["expiration_date"], "%Y-%m-%d").date()
            if exp_date < datetime.date.today():
                errors["expiration_date"] = "La fecha de expiración no puede ser en el pasado"
        except ValueError:
            errors["expiration_date"] = "Formato inválido. Debe ser YYYY-MM-DD"

    # Validación de ubicación
    location = data.get("location")
    if not location or not isinstance(location, dict):
        errors["location"] = "Debe incluir ciudad (y opcionalmente dirección)"
    else:
        if not location.get("city"):
            errors["city"] = "La ciudad es obligatoria"
        if "address" in location and location["address"] and not location["address"].strip():
            errors["address"] = "La dirección no puede estar vacía si se incluye"

    return errors
